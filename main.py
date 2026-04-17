import threading
import sys
import os
import traceback
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QCoreApplication
from gui import AuraDashboard
from brain import AuraBrain
from tasks import check_for_tasks
from voice import speak
from ears import listen

brain = AuraBrain()

def aura_logic(ui):
    ui.status_signal.emit("SYSTEM ONLINE")
    ui.log_signal.emit("SYSTEM", "Aura core initialized. Native graphics engaged.")
    speak("Welcome back, sir. Systems are online.")

    while True:
        try:
            ui.status_signal.emit("LISTENING...")
            query = listen()
            if not query: continue
            
            ui.log_signal.emit("USER", query)
            ui.status_signal.emit("PROCESSING...")
            cmd = query.lower()

            # INSTANT POWER DOWN (Zero Freezing)
            if any(word in cmd for word in ["shutdown", "power down", "exit"]):
                ui.log_signal.emit("SYSTEM", "Shutting down immediately. Goodbye.")
                print("\nAURA: Shutting down immediately.")
                QCoreApplication.quit()
                os._exit(0) # Immediate OS-level process kill

            # Task/Reminder Logic
            task = check_for_tasks(cmd)
            if task:
                ui.log_signal.emit("AURA", task["reply"])
                ui.status_signal.emit("SPEAKING...")
                speak(task["reply"])
                brain.learn(f"TASK: {task['task']}")
                ui.status_signal.emit("TASK LOGGED")
                continue

            # General Reply
            brain.learn(query)
            
            res = brain.generate_reply(query)
            
            ui.log_signal.emit("AURA", res)
            ui.status_signal.emit("SPEAKING...")
            speak(res)
            ui.status_signal.emit("SYSTEM ONLINE")
            
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

    sys.exit(app.exec())