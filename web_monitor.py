import requests
import re
import time

def check_website_status(url):
    """Check if a website is up and measure its response time."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
        
    try:
        start = time.time()
        response = requests.get(url, timeout=10)
        end = time.time()
        latency = (end - start) * 1000 # ms
        
        if response.status_code == 200:
            return f"{url} is up and running. Response time: {latency:.0f}ms."
        else:
            return f"{url} responded with status code {response.status_code}."
    except requests.exceptions.ConnectionError:
        return f"I couldn't connect to {url}. It might be down."
    except requests.exceptions.Timeout:
        return f"The request to {url} timed out."
    except Exception as e:
        return f"An error occurred while checking {url}: {e}"

def is_web_monitor_request(text):
    patterns = [
        r"is (.+) (?:up|down)",
        r"check (?:the )?status of (.+)",
        r"website status (.+)",
    ]
    normalized = text.lower().strip()
    return any(re.search(p, normalized) for p in patterns)

def handle_web_monitor_command(text):
    normalized = text.lower().strip()
    
    # Try different patterns to extract the URL
    match = re.search(r"is (.+) (?:up|down)", normalized)
    if not match:
        match = re.search(r"check (?:the )?status of (.+)", normalized)
    if not match:
        match = re.search(r"website status (.+)", normalized)
        
    if match:
        url = match.group(1).strip().strip("?")
        # Remove filler words
        url = re.sub(r"^(?:the |website )", "", url)
        return {"action": "web_monitor", "reply": check_website_status(url)}
        
    return None
