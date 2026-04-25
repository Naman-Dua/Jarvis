from datetime import datetime

import ollama

from settings import get_setting
from storage import (
    clear_conversation_logs,
    init_db,
    load_recent_history,
    retrieve_info,
    save_message,
    store_info,
)
from task_memory import get_active_task_context

class KoraBrain:
    def __init__(self):
        init_db()
        self.model_name = get_setting("model_name", "llama3.1:8b")
        self.max_history = 40

        self.system_instruction = (
            "You are Kora, a highly capable, polite, and beautiful AI assistant. "
            "You converse naturally like a human. You keep your responses concise, precise, "
            "and conversational. Do not use asterisks or formatting because your output will be spoken aloud. "
            "You have access to a memory of past conversations with the user and a list of active tasks. "
            "Use both when relevant, but stay direct."
        )

        self.conversation_history = load_recent_history(limit=self.max_history)
        if self.conversation_history:
            print(f"[KORA BRAIN] Loaded {len(self.conversation_history)} messages from past sessions.")
        else:
            print("[KORA BRAIN] No past conversation found. Starting fresh.")

    def learn(self, text):
        from nlp_memory import extract_facts
        facts = extract_facts(text, self.model_name)
        for fact in facts:
            store_info("memory", fact)
            print(f"[KORA LEARNED] {fact}")

    def generate_reply(self, user_input):
        text = user_input.lower()

        if "time" in text and ("what" in text or "current" in text):
            reply = f"The current time is {datetime.now().strftime('%I:%M %p')}."
            save_message("user", user_input)
            save_message("assistant", reply)
            return reply

        context_items = retrieve_info(text)
        context_string = " | ".join(context_items[:5])
        active_tasks = get_active_task_context()
        
        prompt_context = []
        if context_string:
            prompt_context.append(f"Relevant memory: {context_string}")
        if active_tasks:
            prompt_context.append(f"Active tasks: {active_tasks}")

        # Construct the current prompt with context
        if prompt_context:
            current_user_prompt = f"[{' | '.join(prompt_context)}]\n\nUser says: {user_input}"
        else:
            current_user_prompt = user_input

        # Add ONLY the raw input to the permanent history for future turns
        self.conversation_history.append({"role": "user", "content": user_input})
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]

        try:
            # Prepare messages for Ollama, replacing the last message with the context-aware one
            llm_messages = [
                {"role": "system", "content": self.system_instruction},
                *self.conversation_history[:-1],
                {"role": "user", "content": current_user_prompt}
            ]

            response = ollama.chat(
                model=self.model_name,
                messages=llm_messages,
            )

            reply = response["message"]["content"].strip()
            self.conversation_history.append({"role": "assistant", "content": reply})
            
            # Save raw message to DB
            save_message("user", user_input)
            save_message("assistant", reply)

            return reply
        except Exception as exc:
            print(f"[Kora Brain Error]: {exc}")
            return "I am having trouble connecting to my local Ollama server. Please make sure Ollama is running."

    def reset_conversation(self):
        self.conversation_history = []
        clear_conversation_logs()
        print("[KORA BRAIN] Conversation history cleared.")
