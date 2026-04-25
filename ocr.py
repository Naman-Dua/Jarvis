"""Screenshot OCR using local vision model."""

import ollama
from screen_analysis import capture_screen, get_available_vision_model
import os
import re

OCR_PATTERNS = [
    re.compile(r"^(?:extract|read|get) (?:the )?text (?:from|on) (?:my )?screen$", re.I),
    re.compile(r"^ocr (?:the )?screen$", re.I),
    re.compile(r"^what does (?:the )?text on (?:my )?screen say$", re.I),
]

def is_ocr_request(text):
    normalized = " ".join(str(text).strip().split())
    return any(p.match(normalized) for p in OCR_PATTERNS)

def extract_screen_text():
    screenshot_path = None
    try:
        screenshot_path = capture_screen()
        model_name = get_available_vision_model()

        if not model_name:
            return "I need a vision model (like moondream or llama3.2-vision) to read your screen."

        response = ollama.chat(
            model=model_name,
            messages=[{
                "role": "user",
                "content": "Extract and list all the text you can see in this screenshot. Return only the text found.",
                "images": [screenshot_path],
            }],
        )
        return response["message"]["content"].strip()
    except Exception as exc:
        return f"Could not perform OCR. {exc}"
    finally:
        if screenshot_path and os.path.exists(screenshot_path):
            os.remove(screenshot_path)

def handle_ocr_command(text):
    result = extract_screen_text()
    return {"action": "ocr", "reply": f"Text found on screen:\n\n{result}"}
