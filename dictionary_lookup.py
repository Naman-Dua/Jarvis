"""Dictionary lookup and translation via free APIs."""

import re
import requests

DEFINE_PATTERNS = [
    re.compile(r"^(?:define|meaning of|what does|what is the meaning of) (.+?)[\s?.]*$", re.I),
    re.compile(r"^(?:dictionary|definition) (.+)$", re.I),
]
TRANSLATE_PATTERNS = [
    re.compile(r"^translate (.+?) (?:to|into) (\w+)$", re.I),
]


def is_dictionary_request(text):
    normalized = " ".join(str(text).strip().split())
    return any(p.match(normalized) for p in DEFINE_PATTERNS)


def is_translate_request(text):
    normalized = " ".join(str(text).strip().split())
    return any(p.match(normalized) for p in TRANSLATE_PATTERNS)


def lookup_word(word):
    word = word.strip().lower()
    try:
        r = requests.get(
            f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}",
            timeout=6,
        )
        r.raise_for_status()
        data = r.json()
        if not data or not isinstance(data, list):
            return None
        entry = data[0]
        meanings = entry.get("meanings", [])
        results = []
        for meaning in meanings[:2]:
            part = meaning.get("partOfSpeech", "")
            defs = meaning.get("definitions", [])
            if defs:
                results.append(f"{part}: {defs[0]['definition']}")
        if results:
            return f"{word} — " + " | ".join(results)
        return None
    except Exception:
        return None


def handle_dictionary_command(text):
    normalized = " ".join(str(text).strip().split())
    for pattern in DEFINE_PATTERNS:
        m = pattern.match(normalized)
        if m:
            word = m.group(1).strip(" ?.")
            result = lookup_word(word)
            if result:
                return {"action": "dictionary", "reply": result}
            return {"action": "dictionary", "reply": f"Could not find a definition for {word}."}
    return None


def handle_translate_command(text):
    normalized = " ".join(str(text).strip().split())
    for pattern in TRANSLATE_PATTERNS:
        m = pattern.match(normalized)
        if m:
            phrase = m.group(1).strip()
            target_lang = m.group(2).strip()
            # Use MyMemory free translation API
            try:
                r = requests.get(
                    "https://api.mymemory.translated.net/get",
                    params={"q": phrase, "langpair": f"en|{target_lang}"},
                    timeout=6,
                )
                r.raise_for_status()
                data = r.json()
                translated = data.get("responseData", {}).get("translatedText", "")
                if translated:
                    return {"action": "translate", "reply": f"Translation: {translated}"}
            except Exception:
                pass
            return {"action": "translate", "reply": "Could not translate that right now."}
    return None
