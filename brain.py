import os
from datetime import datetime
from storage import init_db, store_info, retrieve_info
import ollama

class AuraBrain:
    def __init__(self):
        init_db()
        self.model_name = "llama3.1:8b"
        
        # This is the key: A list to hold the current conversation session
        self.conversation_history = [] 
        self.max_history = 100  # Keep the last 10 messages to avoid slowing down

        self.system_instruction = (
            "You are Aura, a highly capable, polite, and beautiful AI assistant. "
            "You converse naturally like a human. You keep your responses concise, precise, "
            "and conversational. Do not use asterisks or formatting because your output will be spoken aloud."
        )

    def learn(self, text):
        store_info("memory", text)

    def generate_reply(self, user_input):
        text = user_input.lower()

        if "time" in text and ("what" in text or "current" in text):
            return f"The current time is {datetime.now().strftime('%H:%M')}."

        # --- CONTEXT RETRIEVAL (Long term memory) ---
        words = text.split()
        context_items = []
        for word in words:
            if len(word) > 4:
                results = retrieve_info(word)
                if results:
                    context_items.extend(results)
        
        context_string = ", ".join(list(set(context_items))[:4])
        
        # Build the specific prompt for this turn, including long-term facts
        full_user_prompt = user_input
        if context_string:
            full_user_prompt = f"Context facts: {context_string}\n\nUser says: {user_input}"

        # --- CONVERSATION HISTORY (Short term memory) ---
        # 1. Add the new user message to the history
        self.conversation_history.append({'role': 'user', 'content': full_user_prompt})

        # 2. Keep the history from growing too large (Sliding Window)
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]

        try:
            # Use ollama.chat instead of ollama.generate
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {'role': 'system', 'content': self.system_instruction},
                    *self.conversation_history # Unpack the entire history here
                ]
            )
            
            reply = response['message']['content'].strip()
            
            # 3. Add Aura's own reply to history so she remembers what she said
            self.conversation_history.append({'role': 'assistant', 'content': reply})
            
            return reply
            
        except Exception as e:
            print(f"[Aura Brain Error]: {e}")
            return "I am having trouble connecting to my local Ollama server, sir."