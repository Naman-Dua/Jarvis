"""Clipboard read/write using Windows native API (no extra packages)."""

import ctypes
import re

CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002
GMEM_ZEROINIT = 0x0040

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

CLIPBOARD_PATTERNS = [
    re.compile(r"^(?:read|get|show|what(?:'s| is)(?: in)?) (?:my )?clipboard$", re.I),
    re.compile(r"^(?:paste|read) from clipboard$", re.I),
    re.compile(r"^(?:copy|set|write|put) (?:to )?clipboard\s+(.+)$", re.I),
    re.compile(r"^clipboard$", re.I),
]


def read_clipboard():
    if not user32.OpenClipboard(0):
        return None
    try:
        handle = user32.GetClipboardData(CF_UNICODETEXT)
        if not handle:
            return None
        ptr = kernel32.GlobalLock(handle)
        if not ptr:
            return None
        try:
            return ctypes.wstring_at(ptr)
        finally:
            kernel32.GlobalUnlock(handle)
    finally:
        user32.CloseClipboard()


def write_clipboard(text):
    text = str(text)
    if not user32.OpenClipboard(0):
        return False
    try:
        user32.EmptyClipboard()
        data = text.encode("utf-16-le") + b"\x00\x00"
        handle = kernel32.GlobalAlloc(GMEM_MOVEABLE | GMEM_ZEROINIT, len(data))
        ptr = kernel32.GlobalLock(handle)
        ctypes.memmove(ptr, data, len(data))
        kernel32.GlobalUnlock(handle)
        user32.SetClipboardData(CF_UNICODETEXT, handle)
        return True
    finally:
        user32.CloseClipboard()


def is_clipboard_request(text):
    normalized = " ".join(str(text).strip().split())
    return any(p.match(normalized) for p in CLIPBOARD_PATTERNS)


def handle_clipboard_command(text):
    normalized = " ".join(str(text).strip().split())

    for pattern in CLIPBOARD_PATTERNS:
        match = pattern.match(normalized)
        if not match:
            continue
        groups = match.groups()
        if groups and groups[0]:
            content = groups[0].strip()
            if write_clipboard(content):
                return {"action": "clipboard_write", "reply": f"Copied to clipboard: {content[:80]}"}
            return {"action": "clipboard_write", "reply": "Failed to write to clipboard."}
        else:
            content = read_clipboard()
            if content:
                preview = content[:200].strip()
                return {"action": "clipboard_read", "reply": f"Clipboard contains: {preview}"}
            return {"action": "clipboard_read", "reply": "Clipboard is empty."}

    return None
