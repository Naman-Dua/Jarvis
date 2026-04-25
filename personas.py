"""Custom persona/voice profiles for Kora."""

import re
from storage import load_setting, save_setting

PERSONAS = {
    "default": {
        "name": "Kora",
        "system_prompt": (
            "You are Kora, a highly capable, polite, and beautiful AI assistant. "
            "You converse naturally like a human. You keep your responses concise, precise, "
            "and conversational. Do not use asterisks or formatting because your output will be spoken aloud."
        ),
        "voice": "en-US-AriaNeural",
    },
    "professional": {
        "name": "Kora Pro",
        "system_prompt": (
            "You are Kora, a professional AI assistant. "
            "Give precise, formal responses. Be direct and efficient. "
            "No casual language. No formatting — output is spoken aloud."
        ),
        "voice": "en-US-GuyNeural",
    },
    "friendly": {
        "name": "Kora Buddy",
        "system_prompt": (
            "You are Kora, a warm and friendly AI companion. "
            "You are enthusiastic, supportive, and casual. Use simple language. "
            "Be encouraging. No formatting — output is spoken aloud."
        ),
        "voice": "en-US-JennyNeural",
    },
    "concise": {
        "name": "Kora Minimal",
        "system_prompt": (
            "You are Kora. Answer in 1-2 sentences max. "
            "Be extremely brief and direct. No fluff. No formatting."
        ),
        "voice": "en-US-AriaNeural",
    },
}

PERSONA_PATTERN = re.compile(
    r"^(?:switch|change|set) (?:persona|personality|mode) (?:to )?(\w+)$", re.I
)
LIST_PERSONA_PATTERN = re.compile(r"^(?:list|show) (?:personas|personalities|modes)$", re.I)


def is_persona_request(text):
    normalized = " ".join(str(text).strip().split())
    return bool(PERSONA_PATTERN.match(normalized) or LIST_PERSONA_PATTERN.match(normalized))


def get_active_persona():
    name = load_setting("active_persona", "default")
    return PERSONAS.get(name, PERSONAS["default"])


def handle_persona_command(text):
    normalized = " ".join(str(text).strip().split())

    if LIST_PERSONA_PATTERN.match(normalized):
        names = ", ".join(f"{k} ({v['name']})" for k, v in PERSONAS.items())
        active = load_setting("active_persona", "default")
        return {"action": "list_personas", "reply": f"Available personas: {names}. Active: {active}."}

    m = PERSONA_PATTERN.match(normalized)
    if m:
        name = m.group(1).lower()
        if name not in PERSONAS:
            return {"action": "set_persona", "reply": f"Unknown persona: {name}. Available: {', '.join(PERSONAS.keys())}"}
        save_setting("active_persona", name)
        persona = PERSONAS[name]
        return {"action": "set_persona", "reply": f"Switched to {persona['name']} persona."}

    return None
