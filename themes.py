"""Theme management for Kora GUI."""

import re
from storage import load_setting, save_setting

THEMES = {
    "neon": {
        "main_bg": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #080a12, stop:1 #0c0e18)",
        "accent": "#00d2ff",
        "border": "#1a2235",
        "log_bg": "rgba(6, 8, 14, 180)",
    },
    "ruby": {
        "main_bg": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #120808, stop:1 #180c0c)",
        "accent": "#ff0044",
        "border": "#351a1a",
        "log_bg": "rgba(14, 6, 6, 180)",
    },
    "emerald": {
        "main_bg": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #08120a, stop:1 #0c180e)",
        "accent": "#00ff88",
        "border": "#1a351f",
        "log_bg": "rgba(6, 14, 8, 180)",
    },
    "gold": {
        "main_bg": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #121008, stop:1 #18150c)",
        "accent": "#ffcc00",
        "border": "#352f1a",
        "log_bg": "rgba(14, 12, 6, 180)",
    }
}

THEME_PATTERN = re.compile(r"^(?:switch|change|set) (?:theme|appearance) (?:to )?(\w+)$", re.I)
LIST_THEME_PATTERN = re.compile(r"^(?:list|show) (?:themes|appearances)$", re.I)

def is_theme_request(text):
    normalized = " ".join(str(text).strip().split())
    return bool(THEME_PATTERN.match(normalized) or LIST_THEME_PATTERN.match(normalized))

def get_active_theme():
    name = load_setting("active_theme", "neon")
    return THEMES.get(name, THEMES["neon"])

def handle_theme_command(text):
    normalized = " ".join(str(text).strip().split())
    if LIST_THEME_PATTERN.match(normalized):
        return {"action": "list_themes", "reply": f"Available themes: {', '.join(THEMES.keys())}"}
    
    m = THEME_PATTERN.match(normalized)
    if m:
        name = m.group(1).lower()
        if name not in THEMES:
            return {"action": "set_theme", "reply": f"Unknown theme: {name}. Try neon, ruby, emerald, or gold."}
        save_setting("active_theme", name)
        return {"action": "set_theme", "reply": f"Appearance changed to {name}. Restart Kora to apply fully."}
    return None
