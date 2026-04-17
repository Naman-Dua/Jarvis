import threading
import sys
import os
import time
import traceback
import winsound
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QCoreApplication
from actions import perform_action
from screen_analysis import analyze_screen, is_screen_request
from gui import AuraDashboard
from brain import AuraBrain
from tasks import ReminderManager, check_for_tasks
from voice import speak
from ears import extract_wake_command, listen

brain = AuraBrain()
reminder_manager = ReminderManager()
sleep_mode = threading.Event()
pending_alerts = []
pending_alerts_lock = threading.Lock()
wake_notice_pending = threading.Event()
ENABLE_WAKE_WORD = os.getenv("AURA_ENABLE_WAKE_WORD", "0").lower() in {"1", "true", "yes", "on"}
WAKE_STATUS = "LISTENING FOR WAKE WORD"
COMMAND_STATUS = "LISTENING FOR COMMAND"
DEFAULT_LISTENING_STATUS = WAKE_STATUS if ENABLE_WAKE_WORD else "LISTENING..."
SLEEPING_STATUS = "SLEEPING..."
SHUTDOWN_COMMANDS = {
    "shutdown",
    "power down",
    "exit",
    "exit aura",
    "quit aura",
    "shutdown aura",
    "close aura",
}
SLEEP_COMMANDS = {
    "go to sleep",
    "sleep mode",
    "go silent",
    "be quiet",
    "stay quiet",
    "stop talking",
    "don't talk",
    "do not talk",
    "stop listening",
    "mute yourself",
}


def is_sleep_request(cmd):
    normalized = " ".join(cmd.strip().split())
    return normalized in SLEEP_COMMANDS


def queue_pending_alert(message):
    with pending_alerts_lock:
        pending_alerts.append(message)


def pop_pending_alerts():
    with pending_alerts_lock:
        queued = list(pending_alerts)
        pending_alerts.clear()
        return queued


def handle_wake_transition(ui):
    if not wake_notice_pending.is_set():
        return

    wake_notice_pending.clear()
    ui.log_signal.emit("SYSTEM", "Aura is awake again.")
    ui.status_signal.emit("SPEAKING...")
    speak("I'm awake.")

    queued_alerts = pop_pending_alerts()
    for message in queued_alerts:
        wake_message = f"While you were away, {message}"
        ui.log_signal.emit("REMINDER", wake_message)
        speak(wake_message)

    ui.status_signal.emit(DEFAULT_LISTENING_STATUS)


def wait_for_command(ui):
    """Listen for a command, with wake-word gating only when explicitly enabled."""
    if sleep_mode.is_set():
        while True:
            ui.status_signal.emit(SLEEPING_STATUS)
            heard_text = listen()
            if not heard_text:
                continue

            wake_command = extract_wake_command(heard_text)
            if wake_command is None:
                continue

            sleep_mode.clear()
            wake_notice_pending.set()
            if wake_command:
                return wake_command
            return ""

    if not ENABLE_WAKE_WORD:
        ui.status_signal.emit(DEFAULT_LISTENING_STATUS)
        return listen()

    while True:
        ui.status_signal.emit(DEFAULT_LISTENING_STATUS)
        heard_text = listen()
        if not heard_text:
            continue

        command_after_wake = extract_wake_command(heard_text)
        if command_after_wake is None:
            continue

        if command_after_wake:
            return command_after_wake

        ui.log_signal.emit("SYSTEM", "Wake word detected.")
        ui.status_signal.emit(COMMAND_STATUS)
        speak("Yes?")
        follow_up = listen()
        if follow_up:
            return follow_up


def reminder_loop(ui):
    while True:
        try:
            due_items = reminder_manager.pop_due()
            for item in due_items:
                if sleep_mode.is_set():
                    queued_message = item.trigger_message()
                    ui.log_signal.emit("REMINDER", f"Queued while sleeping: {queued_message}")
                    queue_pending_alert(queued_message)
                    continue

                alert_thread = threading.Thread(
                    target=deliver_reminder_alert,
                    args=(ui, item),
                    daemon=True,
                )
                alert_thread.start()
        except Exception:
            print(f"Reminder loop error: {traceback.format_exc()}")
        time.sleep(1)


def play_alert_tone():
    try:
        winsound.Beep(1200, 350)
        winsound.Beep(1000, 350)
    except Exception:
        winsound.MessageBeep()


def deliver_reminder_alert(ui, item):
    base_message = item.trigger_message()
    follow_up_messages = [
        base_message,
        f"Follow-up: {base_message}",
        f"Final reminder: {base_message}",
    ]

    for index, message in enumerate(follow_up_messages):
        ui.log_signal.emit("REMINDER", message)
        ui.status_signal.emit("SPEAKING...")
        play_alert_tone()
        speak(message)
        ui.status_signal.emit(DEFAULT_LISTENING_STATUS)
        if index < len(follow_up_messages) - 1:
            time.sleep(8)

def aura_logic(ui):
    ui.status_signal.emit("SYSTEM ONLINE")
    ui.log_signal.emit("SYSTEM", "Aura core initialized. Native graphics engaged.")
    speak("Welcome back, sir. Systems are online.")
    if ENABLE_WAKE_WORD:
        ui.log_signal.emit("SYSTEM", "Wake word mode enabled.")
    else:
        ui.log_signal.emit("SYSTEM", "Wake word mode disabled. Direct listening active.")
    ui.status_signal.emit(DEFAULT_LISTENING_STATUS)

    while True:
        try:
            query = wait_for_command(ui)
            handle_wake_transition(ui)
            if not query:
                continue
            ui.log_signal.emit("USER", query)
            ui.status_signal.emit("PROCESSING...")
            cmd = query.lower()

            # INSTANT POWER DOWN (Zero Freezing)
            if cmd.strip() in SHUTDOWN_COMMANDS:
                ui.log_signal.emit("SYSTEM", "Shutting down immediately. Goodbye.")
                print("\nAURA: Shutting down immediately.")
                QCoreApplication.quit()
                os._exit(0) # Immediate OS-level process kill

            if is_sleep_request(cmd):
                sleep_mode.set()
                sleep_reply = "Going to sleep. Say Hey Aura to wake me."
                ui.log_signal.emit("AURA", sleep_reply)
                ui.status_signal.emit("SPEAKING...")
                speak(sleep_reply)
                ui.status_signal.emit(SLEEPING_STATUS)
                continue

            # Desktop Action Logic
            action_reply = perform_action(cmd)
            if action_reply:
                ui.log_signal.emit("AURA", action_reply)
                ui.status_signal.emit("SPEAKING...")
                speak(action_reply)
                ui.status_signal.emit(DEFAULT_LISTENING_STATUS)
                continue

            if is_screen_request(cmd):
                screen_reply = analyze_screen(query)
                ui.log_signal.emit("AURA", screen_reply)
                ui.status_signal.emit("SPEAKING...")
                speak(screen_reply)
                ui.status_signal.emit(DEFAULT_LISTENING_STATUS)
                continue

            # Task/Reminder Logic
            task = check_for_tasks(cmd, reminder_manager)
            if task:
                ui.log_signal.emit("AURA", task["reply"])
                ui.status_signal.emit("SPEAKING...")
                speak(task["reply"])
                if task.get("action") == "schedule" and task.get("item"):
                    brain.learn(
                        f"{task['item'].kind.upper()} scheduled: {task['item'].task} at {task['item'].due_phrase()}"
                    )
                ui.status_signal.emit("TASK LOGGED")
                ui.status_signal.emit(DEFAULT_LISTENING_STATUS)
                continue

            # General Reply
            brain.learn(query)
            
            res = brain.generate_reply(query)
            
            ui.log_signal.emit("AURA", res)
            ui.status_signal.emit("SPEAKING...")
            speak(res)
            ui.status_signal.emit(DEFAULT_LISTENING_STATUS)
            
        except Exception as e:
            err_msg = f"Crash prevented: {str(e)}"
            ui.log_signal.emit("SYSTEM ERROR", err_msg)
            print(f"Exception logic branch: {traceback.format_exc()}")
            ui.status_signal.emit("RECOVERED")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    hud = AuraDashboard()
    hud.show()

    # Start logic thread
    t = threading.Thread(target=aura_logic, args=(hud,), daemon=True)
    t.start()
    reminder_thread = threading.Thread(target=reminder_loop, args=(hud,), daemon=True)
    reminder_thread.start()

    sys.exit(app.exec())
