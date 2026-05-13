"""Auto-debug commands for Kora."""

import compileall
import os
import re
from pathlib import Path

from storage import load_setting, save_setting


MODE_PATTERN = re.compile(r"^auto[- ]?debug\s+mode\s+(on|off)$", re.IGNORECASE)
RUN_PATTERN = re.compile(r"^(?:auto[- ]?debug|debug kora|diagnose kora|check errors)$", re.IGNORECASE)


def is_auto_debug_request(text):
    normalized = " ".join(str(text).strip().split())
    return bool(MODE_PATTERN.match(normalized) or RUN_PATTERN.match(normalized))


def _read_crash_tail(limit=1800):
    log_path = Path("kora_crash.log")
    if not log_path.exists():
        return ""
    try:
        text = log_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""
    return text[-limit:].strip()


def _compile_project():
    ok = compileall.compile_dir(
        os.getcwd(),
        quiet=1,
        maxlevels=2,
        rx=re.compile(r"[\\/](?:\.venv|\.git|kora_chroma_db)[\\/]"),
    )
    return bool(ok)


def handle_auto_debug_command(text):
    normalized = " ".join(str(text).strip().split())

    mode_match = MODE_PATTERN.match(normalized)
    if mode_match:
        enabled = mode_match.group(1).lower() == "on"
        save_setting("auto_debug_mode", enabled)
        return {"action": "auto_debug_mode", "reply": f"Auto-debug mode is {'on' if enabled else 'off'}."}

    crash_tail = _read_crash_tail()
    compile_ok = _compile_project()
    parts = [f"Compile check: {'passed' if compile_ok else 'failed'}."]
    if crash_tail:
        short_tail = " ".join(crash_tail.splitlines()[-8:])
        parts.append(f"Latest crash signal: {short_tail[:700]}")
    else:
        parts.append("No crash log is present.")

    if not compile_ok:
        parts.append("Next step: run the import smoke test and inspect the first syntax error.")
    elif crash_tail:
        parts.append("Next step: fix the newest crash cause above, then clear the log after verification.")
    else:
        parts.append("Kora looks healthy from the local checks I can run.")

    return {"action": "auto_debug", "reply": " ".join(parts)}
