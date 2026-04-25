import psutil
import platform
import os
import re

def get_system_report():
    # CPU
    cpu_usage = psutil.cpu_percent(interval=0.5)
    cpu_count = psutil.cpu_count()
    
    # RAM
    memory = psutil.virtual_memory()
    mem_used = memory.percent
    mem_total = round(memory.total / (1024 ** 3), 1)
    
    # Disk
    disk = psutil.disk_usage('/')
    disk_used = disk.percent
    disk_free = round(disk.free / (1024 ** 3), 1)
    
    # Battery
    battery = psutil.sensors_battery()
    battery_status = ""
    if battery:
        plugged = "plugged in" if battery.power_plugged else "on battery"
        battery_status = f", battery at {battery.percent}% ({plugged})"
    
    report = (
        f"Your system is running at {cpu_usage}% CPU usage across {cpu_count} cores. "
        f"Memory usage is at {mem_used}% of {mem_total} GB. "
        f"Your primary disk is {disk_used}% full with {disk_free} GB free{battery_status}."
    )
    return report

def is_system_request(text):
    patterns = [
        r"system (status|health|report|info)",
        r"how is (my|the) system",
        r"cpu (usage|percent)",
        r"memory (usage|percent)",
        r"battery (level|status)",
    ]
    normalized = text.lower().strip()
    return any(re.search(p, normalized) for p in patterns)

def handle_system_command(text):
    if is_system_request(text):
        return {"action": "system_report", "reply": get_system_report()}
    return None
