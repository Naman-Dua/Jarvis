"""Conversation summarizer — summarize current chat using LLM."""

import re

SUMMARIZE_PATTERNS = [
    re.compile(r"^summarize (?:this |our )?conversation$", re.I),
    re.compile(r"^(?:conversation|chat) summary$", re.I),
    re.compile(r"^what (?:have we|did we) (?:talked|spoken|discussed) about$", re.I),
    re.compile(r"^recap$", re.I),
]


def is_summarize_request(text):
    normalized = " ".join(str(text).strip().split())
    return any(p.match(normalized) for p in SUMMARIZE_PATTERNS)


def summarize_conversation(conversation_history, model_name="llama3.1:8b"):
    import ollama

    if not conversation_history:
        return "There is no conversation to summarize yet."

    recent = conversation_history[-20:]
    transcript = "\n".join(f"{m['role']}: {m['content'][:200]}" for m in recent)

    try:
        r = ollama.generate(
            model=model_name,
            prompt=(
                "Summarize this conversation in 3-5 bullet points. "
                "Be concise. No formatting or asterisks.\n\n"
                f"{transcript}"
            ),
        )
        return r["response"].strip()
    except Exception as e:
        return f"Could not summarize: {e}"
