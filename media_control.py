"""Media key control via Windows keybd_event — no extra packages."""

import ctypes
import re

user32 = ctypes.windll.user32

VK_MEDIA_PLAY_PAUSE = 0xB3
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002

MEDIA_COMMANDS = {
    "play": VK_MEDIA_PLAY_PAUSE,
    "pause": VK_MEDIA_PLAY_PAUSE,
    "play pause": VK_MEDIA_PLAY_PAUSE,
    "resume": VK_MEDIA_PLAY_PAUSE,
    "next": VK_MEDIA_NEXT_TRACK,
    "next track": VK_MEDIA_NEXT_TRACK,
    "skip": VK_MEDIA_NEXT_TRACK,
    "previous": VK_MEDIA_PREV_TRACK,
    "previous track": VK_MEDIA_PREV_TRACK,
    "go back": VK_MEDIA_PREV_TRACK,
    "mute": VK_VOLUME_MUTE,
    "unmute": VK_VOLUME_MUTE,
    "volume up": VK_VOLUME_UP,
    "louder": VK_VOLUME_UP,
    "volume down": VK_VOLUME_DOWN,
    "quieter": VK_VOLUME_DOWN,
}

MEDIA_PATTERN = re.compile(
    r"^(?:media |music )?(?:" + "|".join(re.escape(k) for k in MEDIA_COMMANDS) + r")(?:$| music| media| song| track)",
    re.I,
)
VOLUME_REPEAT = re.compile(r"^volume (up|down)(?: (\d+))?$", re.I)


def _press_key(vk_code):
    user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY, 0)
    user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)


def is_media_request(text):
    normalized = " ".join(str(text).strip().lower().split())
    normalized = re.sub(r"\b(kora|please)\b", "", normalized).strip()
    return bool(MEDIA_PATTERN.match(normalized))


def handle_media_command(text):
    normalized = " ".join(str(text).strip().lower().split())
    normalized = re.sub(r"\b(kora|please)\b", "", normalized).strip()

    # Volume repeat: "volume up 5"
    vol_m = VOLUME_REPEAT.match(normalized)
    if vol_m:
        direction = vol_m.group(1).lower()
        count = int(vol_m.group(2) or 3)
        count = min(count, 20)
        vk = VK_VOLUME_UP if direction == "up" else VK_VOLUME_DOWN
        for _ in range(count):
            _press_key(vk)
        return {"action": "media_volume", "reply": f"Volume {direction} by {count} steps."}

    for label, vk in MEDIA_COMMANDS.items():
        if normalized.startswith(label):
            _press_key(vk)
            return {"action": "media_key", "reply": f"Done. Sent {label}."}

    return None
