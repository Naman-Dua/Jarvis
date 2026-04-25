"""Window management — minimize, maximize, snap, resize, close windows."""

import ctypes
import re

user32 = ctypes.windll.user32

SW_MINIMIZE = 6
SW_MAXIMIZE = 3
SW_RESTORE = 9

WINDOW_PATTERNS = [
    re.compile(r"^minimize (?:the )?(?:current )?window$", re.I),
    re.compile(r"^maximize (?:the )?(?:current )?window$", re.I),
    re.compile(r"^restore (?:the )?(?:current )?window$", re.I),
    re.compile(r"^snap (?:the )?window (?:to )?(left|right)$", re.I),
    re.compile(r"^minimize all(?: windows)?$", re.I),
    re.compile(r"^show desktop$", re.I),
]


def is_window_request(text):
    normalized = " ".join(str(text).strip().split())
    return any(p.match(normalized) for p in WINDOW_PATTERNS)


def _get_window_text(hwnd):
    length = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value


def _get_target_hwnd():
    """Get the foreground window, but skip Kora itself if it's currently focused."""
    hwnd = user32.GetForegroundWindow()
    title = _get_window_text(hwnd).upper()
    if "KORA" in title:
        # If Kora is focused, we don't want to minimize/maximize Kora.
        # We could try to find the next window, but for now just return None or handle it.
        return hwnd, True # True means it's Kora
    return hwnd, False


def _get_screen_size():
    w = user32.GetSystemMetrics(0)
    h = user32.GetSystemMetrics(1)
    return w, h


def handle_window_command(text):
    normalized = " ".join(str(text).strip().split())
    hwnd, is_kora = _get_target_hwnd()

    if re.match(r"^minimize (?:the )?(?:current )?window$", normalized, re.I):
        if is_kora:
            return {"action": "window_minimize", "reply": "I won't minimize myself. Please click on the target window first."}
        user32.ShowWindow(hwnd, SW_MINIMIZE)
        return {"action": "window_minimize", "reply": "Window minimized."}

    if re.match(r"^maximize (?:the )?(?:current )?window$", normalized, re.I):
        if is_kora:
            return {"action": "window_maximize", "reply": "I am already at my preferred size."}
        user32.ShowWindow(hwnd, SW_MAXIMIZE)
        return {"action": "window_maximize", "reply": "Window maximized."}

    if re.match(r"^restore (?:the )?(?:current )?window$", normalized, re.I):
        user32.ShowWindow(hwnd, SW_RESTORE)
        return {"action": "window_restore", "reply": "Window restored."}

    m = re.match(r"^snap (?:the )?window (?:to )?(left|right)$", normalized, re.I)
    if m:
        if is_kora:
            return {"action": "window_snap", "reply": "I can't snap myself. Please select another window."}
        side = m.group(1).lower()
        sw, sh = _get_screen_size()
        user32.ShowWindow(hwnd, SW_RESTORE)
        if side == "left":
            user32.MoveWindow(hwnd, 0, 0, sw // 2, sh, True)
        else:
            user32.MoveWindow(hwnd, sw // 2, 0, sw // 2, sh, True)
        return {"action": "window_snap", "reply": f"Snapped window to {side}."}

    if re.match(r"^(?:minimize all|show desktop)$", normalized, re.I):
        # Win+D simulation
        user32.keybd_event(0x5B, 0, 0, 0)  # Win down
        user32.keybd_event(0x44, 0, 0, 0)  # D down
        user32.keybd_event(0x44, 0, 2, 0)  # D up
        user32.keybd_event(0x5B, 0, 2, 0)  # Win up
        return {"action": "window_desktop", "reply": "Showing desktop."}

    return None
