"""Game and entertainment commands for Kora."""

import random
import re

from storage import load_setting, save_setting


MODE_PATTERN = re.compile(r"^(?:game|entertainment|fun)\s+mode\s+(on|off)$", re.IGNORECASE)
JOKE_PATTERN = re.compile(r"^(?:tell me a joke|joke|make me laugh)$", re.IGNORECASE)
PICK_PATTERN = re.compile(r"^(?:pick|choose)\s+(?:a\s+)?(?:movie|game|activity|something fun)(?:\s+for me)?$", re.IGNORECASE)
ROLL_PATTERN = re.compile(r"^(?:roll|throw)\s+(?:a\s+)?(?:dice|die)(?:\s+d?(\d+))?$", re.IGNORECASE)
COIN_PATTERN = re.compile(r"^(?:flip|toss)\s+(?:a\s+)?coin$", re.IGNORECASE)


JOKES = [
    "I told my computer I needed a break, and it said no problem, it would go to sleep.",
    "Why do programmers prefer dark mode? Because light attracts bugs.",
    "I tried to write a joke about recursion, but it keeps referring back to itself.",
]

ACTIVITIES = [
    "Play a short puzzle game for ten minutes.",
    "Watch one episode of a comfort show.",
    "Try a quick aim trainer or rhythm game session.",
    "Queue a movie and make it a proper break, not background noise.",
    "Do a low-stakes chess puzzle run.",
]


def is_entertainment_request(text):
    normalized = " ".join(str(text).strip().split())
    return bool(
        MODE_PATTERN.match(normalized)
        or JOKE_PATTERN.match(normalized)
        or PICK_PATTERN.match(normalized)
        or ROLL_PATTERN.match(normalized)
        or COIN_PATTERN.match(normalized)
    )


def handle_entertainment_command(text):
    normalized = " ".join(str(text).strip().split())

    mode_match = MODE_PATTERN.match(normalized)
    if mode_match:
        enabled = mode_match.group(1).lower() == "on"
        save_setting("entertainment_mode", enabled)
        return {
            "action": "entertainment_mode",
            "reply": f"Game and entertainment mode is {'on' if enabled else 'off'}.",
        }

    if JOKE_PATTERN.match(normalized):
        return {"action": "joke", "reply": random.choice(JOKES)}

    if PICK_PATTERN.match(normalized):
        mode_note = " Since entertainment mode is on, I am biased toward actual downtime." if load_setting("entertainment_mode", False) else ""
        return {"action": "pick_fun", "reply": random.choice(ACTIVITIES) + mode_note}

    roll_match = ROLL_PATTERN.match(normalized)
    if roll_match:
        sides = int(roll_match.group(1) or 6)
        sides = max(2, min(1000, sides))
        return {"action": "roll_dice", "reply": f"You rolled {random.randint(1, sides)} on a d{sides}."}

    if COIN_PATTERN.match(normalized):
        return {"action": "coin_flip", "reply": f"It landed on {random.choice(['heads', 'tails'])}."}

    return None
