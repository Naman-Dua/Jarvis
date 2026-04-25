import time
import threading
from window_mgmt import _get_window_text, user32

DISTRACTING_APPS = ["CHROME", "SPOTIFY", "STEAM", "DISCORD", "YOUTUBE", "NETFLIX", "TWITCH"]

class FocusMode:
    def __init__(self):
        self.active = False
        self.end_time = None
        self._thread = None
        self._stop_event = threading.Event()

    def start(self, duration_minutes=30):
        if self.active:
            return "Focus mode is already active."
        
        self.active = True
        self.end_time = time.time() + (duration_minutes * 60)
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._monitor, daemon=True)
        self._thread.start()
        return f"Focus mode activated for {duration_minutes} minutes. I'll help you stay on track."

    def stop(self):
        if not self.active:
            return "Focus mode is not active."
        self.active = False
        self._stop_event.set()
        return "Focus mode deactivated."

    def _monitor(self):
        while not self._stop_event.is_set():
            if time.time() > self.end_time:
                self.active = False
                break
            
            hwnd = user32.GetForegroundWindow()
            title = _get_window_text(hwnd).upper()
            
            for app in DISTRACTING_APPS:
                if app in title:
                    # In a real app, we might send a notification or a signal to the UI.
                    # For now, we'll just log it or handle it in main.py if possible.
                    # But since this is a separate thread, we'll just print for now.
                    print(f"[FOCUS] Distraction detected: {title}")
                    # We could also minimize it: user32.ShowWindow(hwnd, 6) # SW_MINIMIZE
                    
            time.sleep(5) # Check every 5 seconds

focus_instance = FocusMode()

def is_focus_request(text):
    import re
    patterns = [
        r"(?:start|enter|begin) focus mode",
        r"deep work",
        r"stop focus mode",
    ]
    normalized = text.lower().strip()
    return any(re.search(p, normalized) for p in patterns)

def handle_focus_command(text):
    import re
    normalized = text.lower().strip()
    
    if "stop" in normalized:
        return {"action": "focus_stop", "reply": focus_instance.stop()}
        
    match = re.search(r"(?:for )?(\d+) (?:minutes|mins?)", normalized)
    duration = int(match.group(1)) if match else 30
    
    return {"action": "focus_start", "reply": focus_instance.start(duration)}
