import psutil
import re
import os
import subprocess

def list_running_processes(limit=15):
    """Return a list of top running processes by name."""
    processes = []
    for proc in psutil.process_iter(['name', 'cpu_percent']):
        try:
            processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    # Sort by CPU usage
    processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
    names = [p['name'] for p in processes[:limit]]
    # Remove duplicates while preserving order
    seen = set()
    unique_names = [x for x in names if not (x in seen or seen.add(x))]
    
    return "Running apps include: " + ", ".join(unique_names) + "."

def kill_process_by_name(name):
    """Find and kill processes by name (case-insensitive)."""
    count = 0
    target = name.lower()
    if not target.endswith(".exe"):
        target += ".exe"
        
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'].lower() == target:
                proc.kill()
                count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    if count > 0:
        return {"action": "process_kill", "reply": f"Successfully terminated {count} instance(s) of {name}.", "success": True}
    else:
        # Try a partial match if no exact match found
        for proc in psutil.process_iter(['name']):
            try:
                if name.lower() in proc.info['name'].lower():
                    proc.kill()
                    count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        if count > 0:
            return {"action": "process_kill", "reply": f"Successfully terminated {count} instance(s) matching '{name}'.", "success": True}
            
    return {"action": "process_kill", "reply": f"I couldn't find any running process named '{name}'.", "success": False, "error": "Process not found"}

def launch_app(name):
    try:
        # Windows 'start' command can launch apps via their registered names
        # e.g., 'start chrome' or 'start notepad'
        os.system(f'start "" "{name}"')
        return {"action": "process_launch", "reply": f"Attempting to launch {name}.", "success": True}
    except Exception as e:
        return {"action": "process_launch", "reply": f"Could not launch {name}.", "success": False, "error": str(e)}

def _change_process_state(name, state="pause"):
    count = 0
    target = name.lower()
    if not target.endswith(".exe"):
        target += ".exe"
        
    for proc in psutil.process_iter(['name']):
        try:
            if target in proc.info['name'].lower() or proc.info['name'].lower() in target:
                if state == "pause":
                    proc.suspend()
                else:
                    proc.resume()
                count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
            
    action_word = "paused" if state == "pause" else "resumed"
    if count > 0:
        return {"action": f"process_{state}", "reply": f"Successfully {action_word} {count} instance(s) of {name}.", "success": True}
    return {"action": f"process_{state}", "reply": f"I couldn't find any running process named '{name}' to {state}.", "success": False}

def system_power(action):
    try:
        if action == "restart":
            os.system("shutdown /r /t 5")
            return {"action": "system_restart", "reply": "Restarting the system in 5 seconds."}
        elif action == "shutdown":
            os.system("shutdown /s /t 5")
            return {"action": "system_shutdown", "reply": "Shutting down the system in 5 seconds."}
        elif action == "sleep":
            os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
            return {"action": "system_sleep", "reply": "Going to sleep."}
    except Exception as e:
        return {"action": f"system_{action}", "reply": f"Failed to {action} the system.", "success": False, "error": str(e)}
    return {"action": "unknown", "reply": "Unknown power command."}

def is_process_request(text):
    patterns = [
        r"what(?:'s| is) running",
        r"(?:list|show) (?:running )?(?:apps|processes)",
        r"(?:kill|terminate|stop|force close) (.+)",
        r"(?:open|launch|start|run) (?:the )?(?:app|program|application )?(.+)",
        r"(?:pause|freeze|suspend) (?:the )?(?:app|program|process )?(.+)",
        r"(?:resume|unfreeze|continue) (?:the )?(?:app|program|process )?(.+)",
        r"(?:restart|reboot|shutdown|shut down|sleep) (?:the )?(?:system|pc|computer|machine)",
        r"^restart pc$",
        r"^shutdown pc$",
        r"^sleep pc$"
    ]
    normalized = text.lower().strip()
    return any(re.search(p, normalized) for p in patterns)

def handle_process_command(text):
    normalized = text.lower().strip()
    
    # List
    if any(p in normalized for p in ["what's running", "what is running", "list running", "show running", "list apps"]):
        return {"action": "process_list", "reply": list_running_processes()}
        
    # Kill
    match = re.search(r"(?:kill|terminate|stop|force close) (.+)", normalized)
    if match:
        name = match.group(1).strip().strip("'\"")
        name = re.sub(r"^(?:the |app |program )", "", name)
        return kill_process_by_name(name)
        
    # Launch
    match = re.search(r"(?:open|launch|start|run) (?:the )?(?:app|program|application )?(.+)", normalized)
    if match:
        name = match.group(1).strip().strip("'\"")
        name = re.sub(r"^(?:the |app |program )", "", name)
        return launch_app(name)
        
    # Pause
    match = re.search(r"(?:pause|freeze|suspend) (?:the )?(?:app|program|process )?(.+)", normalized)
    if match:
        name = match.group(1).strip().strip("'\"")
        name = re.sub(r"^(?:the |app |program )", "", name)
        return _change_process_state(name, "pause")
        
    # Resume
    match = re.search(r"(?:resume|unfreeze|continue) (?:the )?(?:app|program|process )?(.+)", normalized)
    if match:
        name = match.group(1).strip().strip("'\"")
        name = re.sub(r"^(?:the |app |program )", "", name)
        return _change_process_state(name, "resume")
        
    # System Power
    if any(p in normalized for p in ["restart", "reboot"]):
        return system_power("restart")
    if any(p in normalized for p in ["shutdown", "shut down"]):
        return system_power("shutdown")
    if any(p in normalized for p in ["sleep"]):
        return system_power("sleep")
        
    return None
