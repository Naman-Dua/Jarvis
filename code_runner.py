"""Execute Python code snippets safely in a subprocess."""

import re
import subprocess
import sys
import textwrap

CODE_PATTERNS = [
    re.compile(r"^(?:run|execute|eval) (?:python |code )?\s*```(.+?)```$", re.I | re.S),
    re.compile(r"^(?:run|execute|eval) (?:python |code )?\s*(.+)$", re.I | re.S),
    re.compile(r"^python\s+(.+)$", re.I | re.S),
]

BLOCKED_KEYWORDS = {"rmtree", "format(", "system(", "rm -rf", "del /"}


def is_code_request(text):
    normalized = " ".join(str(text).strip().split())
    return any(p.match(normalized) for p in CODE_PATTERNS)


def _extract_code(text):
    normalized = text.strip()
    # Try ``` delimited first
    m = re.search(r"```(?:python)?\s*\n?(.+?)```", normalized, re.S)
    if m:
        return m.group(1).strip()
    # Strip prefix
    for prefix in ("run python", "run code", "execute python", "execute code", "eval python", "eval code", "run", "execute", "eval", "python"):
        if normalized.lower().startswith(prefix):
            code = normalized[len(prefix):].strip()
            if code:
                return code
    return normalized


def _is_safe(code):
    lowered = code.lower()
    for kw in BLOCKED_KEYWORDS:
        if kw in lowered:
            return False
    return True


def handle_code_command(text):
    code = _extract_code(text)
    if not code:
        return None

    if not _is_safe(code):
        return {"action": "code_blocked", "reply": "That code contains potentially destructive operations. Blocked for safety."}

    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=".",
        )
        output = result.stdout.strip()
        error = result.stderr.strip()

        if result.returncode == 0:
            response = output if output else "Code ran successfully with no output."
            return {"action": "code_run", "reply": f"Output: {response[:500]}"}
        else:
            return {"action": "code_error", "reply": f"Error: {error[:400]}"}
    except subprocess.TimeoutExpired:
        return {"action": "code_timeout", "reply": "Code execution timed out after 15 seconds."}
    except Exception as e:
        return {"action": "code_error", "reply": f"Could not run code: {e}"}
