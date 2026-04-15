import psutil

def get_system_vitals():
    # 1. CPU Usage (%)
    cpu_usage = psutil.cpu_percent(interval=1)
    
    # 2. RAM Usage (%)
    ram = psutil.virtual_memory()
    ram_usage = ram.percent
    
    # 3. Battery Status (if on a laptop)
    battery = psutil.sensors_battery()
    battery_status = f"{battery.percent}%" if battery else "Not detected"
    
    return {
        "cpu": cpu_usage,
        "ram": ram_usage,
        "battery": battery_status
    }

def check_system_health():
    vitals = get_system_vitals()
    alerts = []
    
    if vitals['cpu'] > 85:
        alerts.append(f"Sir, CPU usage is critical at {vitals['cpu']} percent.")
    
    if vitals['ram'] > 90:
        alerts.append(f"Memory load is reaching peak capacity at {vitals['ram']} percent.")
        
    return alerts