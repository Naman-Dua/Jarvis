import os
import tempfile

import mss
import ollama
SCREEN_REQUEST_PHRASES = (
    "what is on my screen",
    "what's on my screen",
    "what is on screen",
    "what's on screen",
    "what is on the screen",
    "what's on the screen",
    "analyze my screen",
    "analyse my screen",
    "analyze screen",
    "analyse screen",
    "analyze the screen",
    "analyse the screen",
    "describe my screen",
    "describe screen",
    "describe the screen",
    "read my screen",
    "read screen",
    "read the screen",
    "look at my screen",
    "look at screen",
    "look at the screen",
    "screen analysis",
    "check my screen",
    "check screen",
    "check the screen",
)
PREFERRED_VISION_MODELS = (
    "llama3.2-vision:11b",
    "llama3.2-vision:90b",
    "llama3.2-vision",
    "llava:13b",
    "llava:7b",
    "llava",
    "moondream",
    "minicpm-v",
)


def is_screen_request(text):
    normalized = " ".join(str(text).lower().split())
    return any(phrase in normalized for phrase in SCREEN_REQUEST_PHRASES)



def capture_screen():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp:
        screenshot_path = temp.name

    with mss.mss() as sct:
        sct.shot(mon=1, output=screenshot_path)

    return screenshot_path


def _installed_model_names():
    try:
        response = ollama.list()
    except Exception:
        return []

    models = getattr(response, "models", []) or []
    return [getattr(model, "model", "") for model in models]


def get_available_vision_model():
    installed = _installed_model_names()
    for preferred_model in PREFERRED_VISION_MODELS:
        if preferred_model in installed:
            return preferred_model

    for model_name in installed:
        lowered = model_name.lower()
        if any(keyword in lowered for keyword in ("vision", "llava", "moondream", "minicpm-v")):
            return model_name

    return None


def analyze_screen(query):
    screenshot_path = None
    try:
        screenshot_path = capture_screen()
        model_name = get_available_vision_model()

        if not model_name:
            return (
                "I captured your screen, but there is no vision-capable Ollama model installed yet. "
                "Install one like llama3.2-vision and then ask me again."
            )

        response = ollama.chat(
            model=model_name,
            messages=[{
                "role": "user",
                "content": (
                    "Describe what you see on this screenshot. "
                    "Then answer the following request: "
                    f"{query}"
                ),
                "images": [screenshot_path],
            }],
        )
        return response["message"]["content"].strip()
    except Exception as exc:
        return f"I could not analyze the screen yet. {exc}"
    finally:
        if screenshot_path and os.path.exists(screenshot_path):
            os.remove(screenshot_path)