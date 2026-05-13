"""Personal memory commands for Kora."""

import re

from storage import delete_memories_matching, search_memories, store_info


SHOW_MEMORY_PATTERN = re.compile(
    r"^(?:what do you remember(?: about me)?|show memories|show my memory|memory summary|what have you learned(?: about me)?)$",
    re.IGNORECASE,
)
SEARCH_MEMORY_PATTERN = re.compile(
    r"^(?:search|find|show)\s+(?:memory|memories)\s+(?:for|about)\s+(.+)$",
    re.IGNORECASE,
)
REMEMBER_PATTERN = re.compile(
    r"^(?:remember that|remember this|learn that)\s+(.+)$",
    re.IGNORECASE,
)
FORGET_PATTERN = re.compile(
    r"^(?:forget|delete memory|remove memory|forget that)\s+(.+)$",
    re.IGNORECASE,
)


def is_memory_request(text):
    normalized = " ".join(str(text).strip().split()).rstrip(" ?!.")
    return bool(
        SHOW_MEMORY_PATTERN.match(normalized)
        or SEARCH_MEMORY_PATTERN.match(normalized)
        or REMEMBER_PATTERN.match(normalized)
        or FORGET_PATTERN.match(normalized)
    )


def _format_memories(rows):
    if not rows:
        return "I do not have any saved personal memories yet."
    snippets = []
    for row in rows[:10]:
        content = row[2] if len(row) >= 3 else row[1]
        snippets.append(str(content))
    return "I remember: " + "; ".join(snippets) + "."


def handle_memory_command(text):
    normalized = " ".join(str(text).strip().split()).rstrip(" ?!.")

    remember_match = REMEMBER_PATTERN.match(normalized)
    if remember_match:
        fact = remember_match.group(1).strip(" .")
        if not fact:
            return {"action": "memory_remember", "reply": "Tell me what to remember."}
        if not fact.lower().startswith("user "):
            fact = f"User said: {fact}"
        store_info("user", fact)
        return {"action": "memory_remember", "reply": "Got it. I saved that to memory."}

    forget_match = FORGET_PATTERN.match(normalized)
    if forget_match:
        keyword = forget_match.group(1).strip(" .")
        deleted = delete_memories_matching(keyword)
        if not deleted:
            return {"action": "memory_forget", "reply": f"I could not find a memory matching {keyword}."}
        return {
            "action": "memory_forget",
            "reply": f"Forgot {len(deleted)} matching memor{'y' if len(deleted) == 1 else 'ies'}.",
        }

    search_match = SEARCH_MEMORY_PATTERN.match(normalized)
    if search_match:
        keyword = search_match.group(1).strip(" .")
        return {"action": "memory_search", "reply": _format_memories(search_memories(keyword, limit=10))}

    if SHOW_MEMORY_PATTERN.match(normalized):
        return {"action": "memory_show", "reply": _format_memories(search_memories(limit=10))}

    return None
