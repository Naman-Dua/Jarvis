import time
import re
import threading
import winsound

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

def beep_alarm(times=3):
    for _ in range(times):
        winsound.Beep(1000, 500)
        time.sleep(0.1)

class TimerManager:
    def __init__(self):
        self.timers = []
        
    def set_timer(self, seconds, name="Timer"):
        def alarm():
            beep_alarm(3)
        t = threading.Timer(seconds, alarm)
        t.daemon = True
        t.start()
        self.timers.append(t)
        return f"{name} set for {seconds} seconds."

    def start_pomodoro(self):
        def pomodoro_end():
            beep_alarm(5)
            # automatically start 5 min break
            t2 = threading.Timer(5 * 60, break_end)
            t2.daemon = True
            t2.start()
            self.timers.append(t2)
            
        def break_end():
            beep_alarm(3)
            
        t1 = threading.Timer(25 * 60, pomodoro_end)
        t1.daemon = True
        t1.start()
        self.timers.append(t1)
        return "Pomodoro session started: 25 minutes of focus."

    def set_reminder(self, task, seconds):
        def reminder():
            beep_alarm(2)
        t = threading.Timer(seconds, reminder)
        t.daemon = True
        t.start()
        self.timers.append(t)
        return f"Reminder set for: {task}."

# Global instances
stopwatch_instance = Stopwatch()
timer_manager = TimerManager()

def is_stopwatch_request(text):
    patterns = [
        r"(?:start|stop|reset|lap|status) (?:the )?stopwatch",
        r"how long has it been",
        r"stopwatch (?:start|stop|reset|lap|status)",
        r"set (?:a )?timer for (\d+) (seconds?|minutes?|hours?)",
        r"(?:start|begin) (?:a )?pomodoro",
        r"remind me to (.+) in (\d+) (seconds?|minutes?|hours?)",
    ]
    normalized = text.lower().strip()
    return any(re.search(p, normalized) for p in patterns)

def parse_time_to_seconds(amount, unit):
    amount = int(amount)
    if "hour" in unit:
        return amount * 3600
    if "minute" in unit:
        return amount * 60
    return amount

def handle_stopwatch_command(text):
    normalized = text.lower().strip()
    
    # Reminders
    m = re.search(r"remind me to (.+) in (\d+) (seconds?|minutes?|hours?)", normalized)
    if m:
        task = m.group(1).strip()
        secs = parse_time_to_seconds(m.group(2), m.group(3))
        return {"action": "timer_reminder", "reply": timer_manager.set_reminder(task, secs)}
        
    # Timers
    m = re.search(r"set (?:a )?timer for (\d+) (seconds?|minutes?|hours?)", normalized)
    if m:
        secs = parse_time_to_seconds(m.group(1), m.group(2))
        return {"action": "timer_set", "reply": timer_manager.set_timer(secs)}
        
    # Pomodoro
    if "pomodoro" in normalized:
        return {"action": "timer_pomodoro", "reply": timer_manager.start_pomodoro()}
    
    # Stopwatch
    if "start" in normalized and "stopwatch" in normalized:
        return {"action": "stopwatch_start", "reply": stopwatch_instance.start()}
    if "stop" in normalized and "stopwatch" in normalized:
        return {"action": "stopwatch_stop", "reply": stopwatch_instance.stop()}
    if "lap" in normalized:
        return {"action": "stopwatch_lap", "reply": stopwatch_instance.lap()}
    if "reset" in normalized:
        return {"action": "stopwatch_reset", "reply": stopwatch_instance.reset()}
    if "status" in normalized or "how long" in normalized:
        return {"action": "stopwatch_status", "reply": stopwatch_instance.status()}
        
    return None
