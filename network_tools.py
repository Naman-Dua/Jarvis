import subprocess
import re
import urllib.request

def get_public_ip():
    try:
        return urllib.request.urlopen('https://ident.me').read().decode('utf8')
    except Exception:
        return "could not be determined"

def ping_host(host="google.com"):
    try:
        # -n 1 for Windows (1 packet)
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
        r"what(?:'s| is) my ip",
        r"network status",
    ]
    normalized = text.lower().strip()
    return any(re.search(p, normalized) for p in patterns)

def handle_network_command(text):
    normalized = text.lower().strip()
    
    if "my ip" in normalized:
        return {"action": "network_ip", "reply": f"Your public IP address is {get_public_ip()}."}
        
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
