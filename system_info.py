import psutil
import platform
import os
import re
import subprocess

def get_gpu_info():
    try:
        output = subprocess.check_output(['wmic', 'path', 'win32_VideoController', 'get', 'name'], universal_newlines=True, stderr=subprocess.STDOUT)
        lines = [line.strip() for line in output.split('\n') if line.strip() and 'Name' not in line]
        if lines:
            return ", ".join(lines)
    except Exception:
        pass
    return "Unknown GPU"

def get_cpu_temp():
    try:
        temps = psutil.sensors_temperatures()
        if not temps:
            return None
        # Usually 'coretemp' on Intel or 'k10temp' on AMD
        for name, entries in temps.items():
            for entry in entries:
                if entry.current:
                    return entry.current
    except Exception:
        pass
    return None

def get_system_report():
    # CPU
    cpu_usage = psutil.cpu_percent(interval=0.5)
    cpu_count = psutil.cpu_count()
    temp = get_cpu_temp()
    temp_str = f" at {temp}°C" if temp else ""
    
    # RAM
    memory = psutil.virtual_memory()
    mem_used = memory.percent
    mem_total = round(memory.total / (1024 ** 3), 1)
    
    # Disk
    disk = psutil.disk_usage('/')
    disk_used = disk.percent
    disk_free = round(disk.free / (1024 ** 3), 1)
    
    # GPU
    gpu_name = get_gpu_info()
    
    # Battery
    battery = psutil.sensors_battery()
    battery_status = ""
    if battery:
        plugged = "plugged in" if battery.power_plugged else "on battery"
        battery_status = f", battery at {battery.percent}% ({plugged})"
    
    report = (
        f"Your system is running at {cpu_usage}% CPU usage across {cpu_count} cores{temp_str}. "
        f"Memory usage is at {mem_used}% of {mem_total} GB. "
        f"Your primary disk is {disk_used}% full with {disk_free} GB free. "
        f"Graphics processing is handled by {gpu_name}{battery_status}."
    )
    return report

def is_system_request(text):
    patterns = [
        r"system (status|health|report|info)",
        r"how is (my|the) system",
        r"cpu (usage|percent|temperature|temp)",
        r"memory (usage|percent)",
        r"battery (level|status)",
        r"(gpu|graphics|video card) (info|status)",
    ]
    normalized = text.lower().strip()
    return any(re.search(p, normalized) for p in patterns)

def handle_system_command(text):
    if is_system_request(text):
        return {"action": "system_report", "reply": get_system_report()}
    return None
