"""Chat log export — export conversation to text or markdown."""

import os
import re
from datetime import datetime
from storage import load_all_logs

EXPORT_PATTERNS = [
    re.compile(r"^export (?:chat|conversation|logs?)(?:\s+(?:as|to)\s+(\w+))?$", re.I),
    re.compile(r"^save (?:chat|conversation|logs?)(?:\s+(?:as|to)\s+(\w+))?$", re.I),
    re.compile(r"^download (?:chat|conversation|logs?)$", re.I),
]

EXPORT_DIR = os.path.join(os.path.dirname(__file__), "exports")


def is_export_request(text):
    normalized = " ".join(str(text).strip().split())
    return any(p.match(normalized) for p in EXPORT_PATTERNS)


def handle_export_command(text):
    normalized = " ".join(str(text).strip().split())
    fmt = "txt"
    for pattern in EXPORT_PATTERNS:
        m = pattern.match(normalized)
        if m and m.groups() and m.group(1):
            fmt = m.group(1).lower()
            break

    logs = load_all_logs()
    if not logs:
        return {"action": "export", "reply": "No conversation history to export."}

    os.makedirs(EXPORT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if fmt == "md" or fmt == "markdown":
        filename = f"kora_chat_{timestamp}.md"
        filepath = os.path.join(EXPORT_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Kora Conversation — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            for ts, role, content in logs:
                f.write(f"**{role.upper()}** ({str(ts)[:16]})\n\n{content}\n\n---\n\n")
    else:
        filename = f"kora_chat_{timestamp}.txt"
        filepath = os.path.join(EXPORT_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            for ts, role, content in logs:
                f.write(f"[{str(ts)[:16]}] {role.upper()}: {content}\n")

    return {"action": "export", "reply": f"Exported {len(logs)} messages to {filepath}"}
