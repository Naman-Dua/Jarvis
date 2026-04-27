import threading
import time
import os
import ollama
from screen_analysis import capture_screen, get_available_vision_model
from settings import get_setting

class LiveEye(threading.Thread):
    def __init__(self, ui_log_callback, speak_callback):
        super().__init__(daemon=True)
        self.ui_log = ui_log_callback
        self.speak = speak_callback
        self.running = False
        self.interval = 60 # seconds
        self.last_observation = ""

    def run(self):
        self.running = True
        self.ui_log("SYSTEM", "Live Eye proactive monitoring started.")
        
        while self.running:
            if get_setting("enable_live_eye", False):
                self._observe()
            time.sleep(self.interval)

    def _observe(self):
        model_name = get_available_vision_model()
        if not model_name:
            return

        screenshot_path = None
        try:
            screenshot_path = capture_screen()
            
            prompt = """
Analyze this screen. Is the user facing a clear problem, error, or waiting for something? 
If you see a coding error, a slow download, or an interesting piece of news, provide a VERY SHORT proactive suggestion (1 sentence).
If everything looks normal or private, output exactly one word: 'CLEAR'.
Do not be annoying. Only speak up for high-value insights.
"""
            response = ollama.chat(
                model=model_name,
                messages=[{
                    "role": "user",
                    "content": prompt,
                    "images": [screenshot_path],
                }],
            )
            
            observation = response["message"]["content"].strip()
            
            if observation.upper() != "CLEAR" and observation != self.last_observation:
                self.ui_log("KORA (PROACTIVE)", observation)
                self.speak(observation)
                self.last_observation = observation
                
        except Exception as e:
            print(f"[LIVE EYE ERROR] {e}")
        finally:
            if screenshot_path and os.path.exists(screenshot_path):
                os.remove(screenshot_path)

    def stop(self):
        self.running = False
