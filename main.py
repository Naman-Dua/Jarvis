from ears import listen
from voice import speak
from vision import scan_for_master
from monitor import check_system_health, get_system_vitals

def run_jarvis():
    # Security Scan First
    if not scan_for_master():
        return

    speak("All sensors online. Monitoring system health in background.")

    while True:
        # 1. Background Health Check
        health_alerts = check_system_health()
        for alert in health_alerts:
            speak(alert)

        # 2. Listen for Master's Commands
        user_input = listen()
        if not user_input: continue
        
        user_cmd = user_input.lower()

        # Specific command for a full report
        if "status report" in user_cmd or "system status" in user_cmd:
            vitals = get_system_vitals()
            report = f"CPU is at {vitals['cpu']} percent. Memory is at {vitals['ram']} percent. Battery is {vitals['battery']}."
            speak(report)
            
        elif "go to sleep" in user_cmd:
            speak("Powering down, sir.")
            break
            
        # ... Add your other logic (Search/Learn) here ...