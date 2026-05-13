"""Clipboard read/write using Windows native API (no extra packages)."""

import ctypes
import re
import subprocess
import os

CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002
GMEM_ZEROINIT = 0x0040

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

CLIPBOARD_HISTORY = []
MAX_HISTORY = 10

CLIPBOARD_PATTERNS = [
    re.compile(r"^(?:read|get|show|what(?:'s| is)(?: in)?) (?:my )?clipboard$", re.I),
    re.compile(r"^(?:paste|read) from clipboard$", re.I),
    re.compile(r"^(?:copy|set|write|put) (?:to )?clipboard\s+(.+)$", re.I),
    re.compile(r"^show (?:my )?clipboard history$", re.I),
    re.compile(r"^(?:save|read|get) (?:my )?clipboard image$", re.I),
    re.compile(r"^clipboard$", re.I),
]


def _add_to_history(text):
    if not text:
        return
    if text in CLIPBOARD_HISTORY:
        CLIPBOARD_HISTORY.remove(text)
    CLIPBOARD_HISTORY.insert(0, text)
    if len(CLIPBOARD_HISTORY) > MAX_HISTORY:
        CLIPBOARD_HISTORY.pop()


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
            val = ctypes.wstring_at(ptr)
            _add_to_history(val)
            return val
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
        _add_to_history(text)
        return True
    finally:
        user32.CloseClipboard()


def read_clipboard_image(output_path="clipboard_image.png"):
    ps_command = f"""
    Add-Type -AssemblyName System.Windows.Forms
    $img = [System.Windows.Forms.Clipboard]::GetImage()
    if ($img) {{
        $img.Save('{output_path}', [System.Drawing.Imaging.ImageFormat]::Png)
        Write-Output "SUCCESS"
    }} else {{
        Write-Output "NO_IMAGE"
    }}
    """
    try:
        output = subprocess.check_output(["powershell", "-Command", ps_command], text=True).strip()
        if "SUCCESS" in output:
            return os.path.abspath(output_path)
    except Exception:
        pass
    return None


def is_clipboard_request(text):
    normalized = " ".join(str(text).strip().split())
    return any(p.match(normalized) for p in CLIPBOARD_PATTERNS)


def handle_clipboard_command(text):
    normalized = " ".join(str(text).strip().split())

    if re.match(r"^show (?:my )?clipboard history$", normalized, re.I):
        if not CLIPBOARD_HISTORY:
            return {"action": "clipboard_history", "reply": "Your clipboard history is empty."}
        hist_str = "\n".join(f"{i+1}. {item[:50]}..." for i, item in enumerate(CLIPBOARD_HISTORY))
        return {"action": "clipboard_history", "reply": f"Clipboard History:\n{hist_str}"}

    if re.match(r"^(?:save|read|get) (?:my )?clipboard image$", normalized, re.I):
        img_path = read_clipboard_image()
        if img_path:
            return {"action": "clipboard_image", "reply": f"Saved clipboard image to {img_path}"}
        return {"action": "clipboard_image", "reply": "No image found in clipboard."}

    m = re.match(r"^(?:copy|set|write|put) (?:to )?clipboard\s+(.+)$", normalized, re.I)
    if m:
        content = m.group(1).strip()
        if write_clipboard(content):
            return {"action": "clipboard_write", "reply": f"Copied to clipboard: {content[:80]}"}
        return {"action": "clipboard_write", "reply": "Failed to write to clipboard."}
        
    # Read text
    if re.match(r"^(?:read|get|show|what(?:'s| is)(?: in)?) (?:my )?clipboard$|^(?:paste|read) from clipboard$|^clipboard$", normalized, re.I):
        content = read_clipboard()
        if content:
            preview = content[:200].strip()
            return {"action": "clipboard_read", "reply": f"Clipboard contains: {preview}"}
        return {"action": "clipboard_read", "reply": "Clipboard is empty."}
        
    return None
