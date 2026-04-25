import time
import re

class Stopwatch:
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.running = False
        self.laps = []

    def start(self):
        if self.running:
            return "Stopwatch is already running."
        self.start_time = time.time()
        self.running = True
        self.end_time = None
        self.laps = []
        return "Stopwatch started."

    def stop(self):
        if not self.running:
            return "Stopwatch is not running."
        self.end_time = time.time()
        self.running = False
        elapsed = self.end_time - self.start_time
        return f"Stopwatch stopped. Elapsed time: {self._format_time(elapsed)}."

    def lap(self):
        if not self.running:
            return "Stopwatch is not running."
        now = time.time()
        elapsed = now - self.start_time
        self.laps.append(elapsed)
        return f"Lap {len(self.laps)} recorded: {self._format_time(elapsed)}."

    def status(self):
        if not self.start_time:
            return "Stopwatch hasn't been started yet."
        
        if self.running:
            elapsed = time.time() - self.start_time
            return f"Stopwatch is running. Current time: {self._format_time(elapsed)}."
        else:
            elapsed = self.end_time - self.start_time
            return f"Stopwatch is stopped at {self._format_time(elapsed)}."

    def reset(self):
        self.start_time = None
        self.end_time = None
        self.running = False
        self.laps = []
        return "Stopwatch reset."

    def _format_time(self, seconds):
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        if h > 0:
            return f"{int(h)}h {int(m)}m {s:.2f}s"
        elif m > 0:
            return f"{int(m)}m {s:.2f}s"
        else:
            return f"{s:.2f} seconds"

# Global instance for the operator
stopwatch_instance = Stopwatch()

def is_stopwatch_request(text):
    patterns = [
        r"(?:start|stop|reset|lap|status) (?:the )?stopwatch",
        r"how long has it been",
        r"stopwatch (?:start|stop|reset|lap|status)",
    ]
    normalized = text.lower().strip()
    return any(re.search(p, normalized) for p in patterns)

def handle_stopwatch_command(text):
    normalized = text.lower().strip()
    
    if "start" in normalized:
        return {"action": "stopwatch_start", "reply": stopwatch_instance.start()}
    if "stop" in normalized:
        return {"action": "stopwatch_stop", "reply": stopwatch_instance.stop()}
    if "lap" in normalized:
        return {"action": "stopwatch_lap", "reply": stopwatch_instance.lap()}
    if "reset" in normalized:
        return {"action": "stopwatch_reset", "reply": stopwatch_instance.reset()}
    if "status" in normalized or "how long" in normalized:
        return {"action": "stopwatch_status", "reply": stopwatch_instance.status()}
        
    return None
