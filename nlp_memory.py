import ollama
import json
from intelligent_cache import cache_llm_response


def _heuristic_facts(text):
    """Small offline fallback for obvious personal facts."""
    import re

    source = " ".join(str(text).strip().split())
    if not source or len(source) < 6:
        return []

    patterns = [
        (r"\bmy name is\s+([^,.!?]+)", "User's name is {}"),
        (r"\bi am\s+(\d{1,3})\s*(?:years old|yo)?\b", "User is {} years old"),
        (r"\bi live in\s+([^,.!?]+)", "User lives in {}"),
        (r"\bi work as\s+(?:a |an )?([^,.!?]+)", "User works as {}"),
        (r"\bi am\s+(?:a |an )([^,.!?]+)", "User is a {}"),
        (r"\bi like\s+([^,.!?]+)", "User likes {}"),
        (r"\bi love\s+([^,.!?]+)", "User loves {}"),
        (r"\bi hate\s+([^,.!?]+)", "User dislikes {}"),
        (r"\bi prefer\s+([^,.!?]+)", "User prefers {}"),
        (r"\bmy favorite ([^,.!?]+?) is\s+([^,.!?]+)", "User's favorite {} is {}"),
    ]

    facts = []
    lowered = source.lower()
    for pattern, template in patterns:
        for match in re.finditer(pattern, lowered, re.IGNORECASE):
            groups = [g.strip(" .") for g in match.groups()]
            if not all(groups):
                continue
            if len(groups) == 1:
                facts.append(template.format(groups[0]))
            else:
                facts.append(template.format(*groups))

    cleaned = []
    seen = set()
    for fact in facts:
        fact = fact[:180].strip()
        key = fact.lower()
        if key not in seen:
            seen.add(key)
            cleaned.append(fact)
    return cleaned[:5]

@cache_llm_response(ttl=86400) # Cache fact extractions for 24 hours
def extract_facts(text, model_name="llama3.1:8b"):
    """
    Uses the local LLM to extract facts, preferences, and important memory points.
    Returns a list of extracted facts.
    """
    prompt = f"""
You are Kora's autonomous memory extraction module. Analyze the user's text and extract any long-term factual information, user preferences, states, relationships, or important details worth remembering. 
Do not extract transient commands, casual chat, or questions.

Facts to ALWAYS extract:
- User's name, age, residence, occupation, family members, or pets (e.g. "My dog's name is Rex" -> "User's dog's name is Rex").
- User's likes, dislikes, habits, and preferences (e.g. "I live in New York" -> "User lives in New York", "I like to eat pizza" -> "User likes to eat pizza").
- Long-term goals, states, or needs.

Format your output strictly as a JSON list of strings. Each string should be a clear, standalone fact about the user.
If there is nothing worth remembering (e.g. casual chat, short commands like "turn off lights", "hi"), output an empty list: []

Examples:
"My dog's name is Rex" -> ["User's dog's name is Rex"]
"I am a software engineer and I live in Austin" -> ["User is a software engineer", "User lives in Austin"]
"I love watching movies on weekends" -> ["User loves watching movies on weekends"]
"What time is it?" -> []
"Can you open Chrome?" -> []
"Turn off the lights" -> []

User text: {text}
Output JSON list ONLY:
"""
    fallback = _heuristic_facts(text)
    try:
        response = ollama.generate(model=model_name, prompt=prompt)
        content = response['response'].strip()
        
        # Robust JSON extraction: Find the first '[' and the last ']'
        import re
        match = re.search(r'\[.*\]', content, re.DOTALL)
        if match:
            json_str = match.group(0)
            try:
                facts = json.loads(json_str)
                if isinstance(facts, list):
                    merged = [str(f) for f in facts] + fallback
                    deduped = []
                    seen = set()
                    for fact in merged:
                        key = fact.lower().strip()
                        if key and key not in seen:
                            seen.add(key)
                            deduped.append(fact)
                    return deduped[:8]
            except json.JSONDecodeError:
                pass
        
        return fallback
    except Exception as e:
        print(f"[LLM Memory Extractor Error] {e}")
        return fallback

if __name__ == "__main__":
    # Test cases
    test_sentences = [
        "My favorite color is blue.",
        "My dog's name is Rex.",
        "I am a software engineer.",
        "I live in New York City.",
        "I like to eat pizza.",
        "I love watching movies on weekends.",
        "I need a new laptop.",
        "Turn off the lights."  # Should extract nothing
    ]
    for s in test_sentences:
        res = extract_facts(s)
        print(f"{s} -> {res}")
