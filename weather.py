"""Weather lookup using wttr.in — no API key needed."""

import re
import requests

WEATHER_PATTERNS = [
    re.compile(r"^(?:what(?:'s| is) the )?weather(?: in (.+))?$", re.I),
    re.compile(r"^(?:how(?:'s| is) the )?weather(?: in (.+))?$", re.I),
    re.compile(r"^weather (?:for|in|at) (.+)$", re.I),
    re.compile(r"^(?:temperature|forecast)(?: in (.+))?$", re.I),
    re.compile(r"^(?:is it|will it) (?:raining|sunny|cold|hot|warm)(?: in (.+))?", re.I),
]


def is_weather_request(text):
    normalized = " ".join(str(text).strip().split())
    return any(p.match(normalized) for p in WEATHER_PATTERNS)


def _extract_location(text):
    normalized = " ".join(str(text).strip().split())
    for pattern in WEATHER_PATTERNS:
        m = pattern.match(normalized)
        if m and m.groups() and m.group(1):
            return m.group(1).strip()
    return None


def fetch_weather(location=None):
    loc = location or ""
    try:
        url = f"https://wttr.in/{loc}?format=%l:+%C,+%t,+feels+like+%f,+humidity+%h,+wind+%w"
        r = requests.get(url, timeout=6, headers={"User-Agent": "curl/7.68.0"})
        r.raise_for_status()
        return r.text.strip()
    except Exception:
        return None


def handle_weather_command(text):
    location = _extract_location(text)
    result = fetch_weather(location)
    if result:
        return {"action": "weather", "reply": f"Weather: {result}"}
    return {"action": "weather", "reply": "Could not fetch weather right now."}
