import subprocess
import re
import urllib.request
import socket
import psutil
import time

def get_public_ip():
    try:
        return urllib.request.urlopen('https://ident.me').read().decode('utf8')
    except Exception:
        return "could not be determined"

def get_local_ip():
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception:
        return "could not be determined"

def check_open_ports():
    try:
        conns = psutil.net_connections(kind='inet')
        listening = set(c.laddr.port for c in conns if c.status == 'LISTEN')
        if not listening:
            return "No open listening ports found."
        ports = sorted(list(listening))
        # Limit to 10
        if len(ports) > 10:
            return f"Found {len(ports)} open ports. Some of them are: {', '.join(map(str, ports[:10]))}."
        return f"Open listening ports: {', '.join(map(str, ports))}."
    except Exception as e:
        return f"Could not check open ports: {e}"

import threading

_last_dl = 0.0
_last_ul = 0.0

def _bandwidth_loop():
    global _last_dl, _last_ul
    try:
        old_io = psutil.net_io_counters()
        while True:
            time.sleep(1)
            new_io = psutil.net_io_counters()
            _last_dl = (new_io.bytes_recv - old_io.bytes_recv) / 1024 / 1024 # MB/s
            _last_ul = (new_io.bytes_sent - old_io.bytes_sent) / 1024 / 1024 # MB/s
            old_io = new_io
    except Exception:
        pass

threading.Thread(target=_bandwidth_loop, daemon=True).start()

def monitor_bandwidth():
    try:
        return f"Current network speeds - Download: {_last_dl:.2f} MB/s, Upload: {_last_ul:.2f} MB/s."
    except Exception as e:
        return "Could not monitor bandwidth."

def ping_host(host="google.com"):
    try:
        output = subprocess.check_output(["ping", "-n", "1", host], stderr=subprocess.STDOUT, universal_newlines=True)
        if "Reply from" in output or "bytes=" in output:
            match = re.search(r"time[=<](\d+ms)", output)
            latency = match.group(1) if match else "unknown latency"
            return f"Ping to {host} successful ({latency})."
        return f"Ping to {host} failed."
    except Exception:
        return f"I couldn't reach {host} right now."

def is_network_request(text):
    patterns = [
        r"check (?:my )?internet",
        r"ping (.+)",
        r"what(?:'s| is) my (?:public |local )?ip",
        r"network status",
        r"(?:check|monitor|show) (?:my )?(?:bandwidth|speed)",
        r"(?:check|show) (?:my )?(?:open )?ports",
    ]
    normalized = text.lower().strip()
    return any(re.search(p, normalized) for p in patterns)

def handle_network_command(text):
    normalized = text.lower().strip()
    
    if "my local ip" in normalized:
        return {"action": "network_local_ip", "reply": f"Your local IP address is {get_local_ip()}."}
        
    if "my ip" in normalized or "my public ip" in normalized:
        return {"action": "network_ip", "reply": f"Your public IP address is {get_public_ip()}."}
        
    if "bandwidth" in normalized or "speed" in normalized:
        return {"action": "network_bandwidth", "reply": monitor_bandwidth()}
        
    if "ports" in normalized:
        return {"action": "network_ports", "reply": check_open_ports()}
        
    match = re.search(r"ping (.+)", normalized)
    if match:
        host = match.group(1).strip().strip("?")
        return {"action": "network_ping", "reply": ping_host(host)}
        
    if "internet" in normalized or "network status" in normalized:
        res = ping_host("google.com")
        if "successful" in res:
            return {"action": "network_check", "reply": "Your internet connection seems stable. " + res}
        else:
            return {"action": "network_check", "reply": "I'm having trouble reaching the web. " + res}
            
    return None
