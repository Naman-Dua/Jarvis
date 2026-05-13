"""Window management — minimize, maximize, snap, resize, close, transparency, monitor moving."""

import ctypes
import re
import win32api
import win32gui
import win32con

user32 = ctypes.windll.user32

SW_MINIMIZE = 6
SW_MAXIMIZE = 3
SW_RESTORE = 9

HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
LWA_ALPHA = 0x00000002

WINDOW_PATTERNS = [
    re.compile(r"^minimize (?:the )?(?:current )?window$", re.I),
    re.compile(r"^maximize (?:the )?(?:current )?window$", re.I),
    re.compile(r"^restore (?:the )?(?:current )?window$", re.I),
    re.compile(r"^snap (?:the )?window (?:to )?(left|right)$", re.I),
    re.compile(r"^minimize all(?: windows)?$", re.I),
    re.compile(r"^show desktop$", re.I),
    re.compile(r"^(?:keep|pin) (?:the )?window (?:always )?on top$", re.I),
    re.compile(r"^(?:unpin|remove) (?:the )?window (?:from )?top$", re.I),
    re.compile(r"^make (?:the )?window (transparent|opaque)$", re.I),
    re.compile(r"^move (?:the )?window to (?:the )?(next|other) monitor$", re.I),
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
    hwnd = user32.GetForegroundWindow()
    title = _get_window_text(hwnd).upper()
    if "KORA" in title:
        GW_HWNDNEXT = 2
        next_hwnd = user32.GetWindow(hwnd, GW_HWNDNEXT)
        while next_hwnd:
            if user32.IsWindowVisible(next_hwnd):
                t = _get_window_text(next_hwnd).upper()
                if t and "KORA" not in t and "PROGRAM MANAGER" not in t:
                    return next_hwnd, False
            next_hwnd = user32.GetWindow(next_hwnd, GW_HWNDNEXT)
        return hwnd, True
    return hwnd, False

def _get_screen_size():
    w = user32.GetSystemMetrics(0)
    h = user32.GetSystemMetrics(1)
    return w, h

def set_always_on_top(hwnd, enable=True):
    flag = HWND_TOPMOST if enable else HWND_NOTOPMOST
    user32.SetWindowPos(hwnd, flag, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
    return True

def set_transparency(hwnd, alpha):
    style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED)
    user32.SetLayeredWindowAttributes(hwnd, 0, alpha, LWA_ALPHA)

def move_to_next_monitor(hwnd):
    monitors = win32api.EnumDisplayMonitors()
    if len(monitors) < 2:
        return False
        
    current_monitor = user32.MonitorFromWindow(hwnd, 2) # MONITOR_DEFAULTTONEAREST
    
    next_monitor_info = None
    for i, (hMonitor, hdc, rect) in enumerate(monitors):
        if hMonitor.handle == current_monitor:
            next_idx = (i + 1) % len(monitors)
            next_monitor_info = win32api.GetMonitorInfo(monitors[next_idx][0])
            break
            
    if not next_monitor_info:
        # Fallback to second monitor
        next_monitor_info = win32api.GetMonitorInfo(monitors[1][0])
        
    work_area = next_monitor_info['Work']
    rect = win32gui.GetWindowRect(hwnd)
    w = rect[2] - rect[0]
    h = rect[3] - rect[1]
    
    # Simple center on new monitor
    new_x = work_area[0] + (work_area[2] - work_area[0] - w) // 2
    new_y = work_area[1] + (work_area[3] - work_area[1] - h) // 2
    
    win32gui.MoveWindow(hwnd, new_x, new_y, w, h, True)
    return True

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
        user32.keybd_event(0x5B, 0, 0, 0)
        user32.keybd_event(0x44, 0, 0, 0)
        user32.keybd_event(0x44, 0, 2, 0)
        user32.keybd_event(0x5B, 0, 2, 0)
        return {"action": "window_desktop", "reply": "Showing desktop."}
        
    if re.match(r"^(?:keep|pin) (?:the )?window (?:always )?on top$", normalized, re.I):
        set_always_on_top(hwnd, True)
        return {"action": "window_pin", "reply": "Pinned window to top."}
        
    if re.match(r"^(?:unpin|remove) (?:the )?window (?:from )?top$", normalized, re.I):
        set_always_on_top(hwnd, False)
        return {"action": "window_unpin", "reply": "Unpinned window."}
        
    m = re.match(r"^make (?:the )?window (transparent|opaque)$", normalized, re.I)
    if m:
        action = m.group(1).lower()
        alpha = 180 if action == "transparent" else 255
        set_transparency(hwnd, alpha)
        return {"action": "window_transparency", "reply": f"Made window {action}."}
        
    if re.match(r"^move (?:the )?window to (?:the )?(next|other) monitor$", normalized, re.I):
        if move_to_next_monitor(hwnd):
            return {"action": "window_monitor", "reply": "Moved window to next monitor."}
        return {"action": "window_monitor", "reply": "I could only detect one monitor."}

    return None
