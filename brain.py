import ollama
import re
from datetime import datetime
from storage import build_memory_profile, init_db, save_message, retrieve_info, store_info, clear_conversation_logs, load_recent_history
from task_memory import get_active_task_context
from settings import get_setting
from personas import get_active_persona

class KoraBrain:
    def __init__(self):
        init_db()
        self.model_name = get_setting("model_name", "llama3.1:8b")
        self.max_history = 40
        self.conversation_history = load_recent_history(limit=self.max_history)

    def _system_instruction(self):
        persona = get_active_persona()
        return (
            f"{persona.get('system_prompt', '')} "
            "You are a personal AI assistant for one user, so use saved memory when it is relevant. "
            "Never reveal private memory unless the user asks about it or it directly helps the answer. "
            "Keep responses concise and precise. Do not use markdown or asterisks. "
            "At the VERY END of your response, you MUST include a tag in this exact format: "
            "[MOOD: POSITIVE|NEGATIVE|URGENT|IDLE] [INTENT: NONE]. "
            "Example: 'I can help with that. [MOOD: POSITIVE] [INTENT: NONE]'"
        )

    def _select_model(self, user_input):
        if not get_setting("enable_model_routing", True):
            return get_setting("model_name", self.model_name)

        text = str(user_input).lower()
        deep_signals = [
            "debug", "error", "traceback", "code", "plan", "analyze", "explain",
            "summarize", "write", "build", "optimize", "refactor", "strategy",
        ]
        if len(text) > 500 or any(signal in text for signal in deep_signals):
            return get_setting("deep_model_name", get_setting("model_name", self.model_name))
        return get_setting("fast_model_name", get_setting("model_name", self.model_name))

    def learn(self, text):
        from nlp_memory import extract_facts
        facts = extract_facts(text, self.model_name)
        for fact in facts:
            store_info("memory", fact)
            print(f"[KORA LEARNED] {fact}")

    def generate_reply(self, user_input):
        text = user_input.lower()
        
        # Priority check for time
        if "time" in text and ("what" in text or "current" in text):
            reply = f"The current time is {datetime.now().strftime('%I:%M %p')}."
            save_message("user", user_input)
            save_message("assistant", reply)
            return {"text": reply, "mood": "IDLE"}

        # RAG - Context Retrieval
        from storage import load_recent_memories
        core_memories = load_recent_memories(limit=5) # Get top 5 persistent facts
        core_facts = [m[1] for m in core_memories] if core_memories else []
        
        context_items = retrieve_info(text)
        # Avoid duplicating core facts in context items
        context_items = [i for i in context_items if i not in core_facts]
        context_string = " | ".join(context_items[:5])
        
        # Contextual Clipboard Injection
        clipboard_context = ""
        if any(w in text for w in ["this", "that", "it", "clipboard", "summarize", "fix", "code"]):
            try:
                from clipboard_ops import read_clipboard
                clip = read_clipboard()
                if clip and len(clip.strip()) > 2:
                    clipboard_context = f"Clipboard Contents: {clip}"
            except Exception:
                pass
        
        active_tasks = get_active_task_context()
        
        prompt_context = []
        if core_facts:
            prompt_context.append(f"Core User Facts: {' | '.join(core_facts)}")
        memory_profile = build_memory_profile(limit=12)
        if memory_profile:
            prompt_context.append(f"Personal Memory Profile: {memory_profile}")
        if context_string:
            prompt_context.append(f"Relevant Context: {context_string}")
        if active_tasks:
            prompt_context.append(f"Active tasks: {active_tasks}")
        if clipboard_context:
            prompt_context.append(clipboard_context)

        current_user_prompt = f"[{' || '.join(prompt_context)}]\n\nUser: {user_input}" if prompt_context else user_input

        self.conversation_history.append({"role": "user", "content": user_input})
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]

        try:
            llm_messages = [
                {"role": "system", "content": self._system_instruction()},
                *self.conversation_history[:-1],
                {"role": "user", "content": current_user_prompt}
            ]

            selected_model = self._select_model(user_input)
            try:
                response = ollama.chat(
                    model=selected_model,
                    messages=llm_messages,
                )
            except Exception:
                if selected_model == self.model_name:
                    raise
                response = ollama.chat(
                    model=self.model_name,
                    messages=llm_messages,
                )

            full_reply = response["message"]["content"].strip()
            
            # Parse mood and intent from the metadata tag
            mood = "IDLE"
            auto_intent = None
            clean_reply = full_reply
            
            # Extract [MOOD: ...] or [META: ...]
            mood_match = re.search(r"\[(?:MOOD|META):\s*(\w+)\]", full_reply, re.IGNORECASE)
            if mood_match:
                mood = mood_match.group(1).upper()
                
            # Extract [INTENT: ...]
            intent_match = re.search(r"\[INTENT:\s*(.*?)\]", full_reply, re.IGNORECASE)
            if intent_match:
                intent_part = intent_match.group(1).strip()
                if intent_part.startswith("{"):
                    try:
                        import json
                        auto_intent = json.loads(intent_part)
                    except: pass
                    
            # Aggressively clean up all such tags
            clean_reply = re.sub(r"\[(?:MOOD|META|INTENT):.*?\]", "", clean_reply, flags=re.IGNORECASE).strip()

            if mood not in ["POSITIVE", "NEGATIVE", "URGENT", "IDLE"]:
                mood = "IDLE"

            self.conversation_history.append({"role": "assistant", "content": clean_reply})
            save_message("user", user_input)
            save_message("assistant", clean_reply)
            
            return {"text": clean_reply, "mood": mood, "intent": auto_intent}
        except Exception as e:
            print(f"[Kora Brain Error]: {e}")
            return {"text": "I'm having trouble connecting to my local Llama model.", "mood": "NEGATIVE"}

    def reset_conversation(self):
        self.conversation_history = []
        clear_conversation_logs()
        print("[KORA BRAIN] Conversation history cleared.")
