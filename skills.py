import re

DEFAULT_SKILLS = {
    "research": {
        "description": "Search the web and summarize top findings.",
        "example": "use research skill to compare local Ollama vision models",
    },
    "vision": {
        "description": "Inspect the current screen and describe what Kora sees.",
        "example": "use vision skill to analyze my screen",
    },
    "ocr": {
        "description": "Extract and read text from your screen.",
        "example": "extract text from screen",
    },
    "automation": {
        "description": "Save or replay a reusable workflow.",
        "example": "save this workflow as morning setup",
    },
    "clipboard": {
        "description": "Read or write text to the system clipboard.",
        "example": "read clipboard / copy to clipboard hello world",
    },
    "files": {
        "description": "Create, move, rename, delete, or list files.",
        "example": "create file notes.txt / list files in Desktop",
    },
    "media": {
        "description": "Play, pause, skip, or control volume.",
        "example": "pause / next track / volume up 5",
    },
    "weather": {
        "description": "Get current weather for any location.",
        "example": "weather in Tokyo",
    },
    "dictionary": {
        "description": "Look up word definitions or translate text.",
        "example": "define serendipity / translate hello to spanish",
    },
    "news": {
        "description": "Fetch latest headlines.",
        "example": "top news / tech news",
    },
    "summarize_url": {
        "description": "Summarize any web page content.",
        "example": "summarize url https://example.com",
    },
    "code": {
        "description": "Run Python code snippets.",
        "example": "run python print(2+2)",
    },
    "export": {
        "description": "Export conversation logs to a file.",
        "example": "export chat as md",
    },
    "window": {
        "description": "Minimize, maximize, or snap windows.",
        "example": "minimize window / snap window to left",
    },
    "persona": {
        "description": "Switch personality style.",
        "example": "list personas / set persona to concise",
    },
    "theme": {
        "description": "Switch GUI appearance themes.",
        "example": "list themes / set theme to ruby",
    },
    "plugins": {
        "description": "Load and manage drop-in skill plugins.",
        "example": "list plugins / reload plugins",
    },
    "system": {
        "description": "Check system health like CPU, RAM, and Battery.",
        "example": "how is my system? / check system status",
    },
    "process": {
        "description": "List running apps or force close specific processes.",
        "example": "what is running? / kill chrome",
    },
    "network": {
        "description": "Check internet connectivity, ping hosts, or find your public IP.",
        "example": "ping google.com / what is my ip?",
    },
    "stopwatch": {
        "description": "Start, stop, lap, or check a high-precision stopwatch.",
        "example": "start stopwatch / lap time / how long has it been?",
    },
    "web_monitor": {
        "description": "Check if a website is up or down and measure its speed.",
        "example": "is github.com up? / check status of google.com",
    },
    "briefing": {
        "description": "Get a unified report of weather, news, and your tasks for today.",
        "example": "good morning / daily briefing",
    },
    "focus": {
        "description": "Help you stay productive by monitoring distracting apps.",
        "example": "start focus mode for 45 minutes / deep work",
    },
}

LIST_SKILLS_PATTERN = re.compile(r"^(?:list|show|what are)\s+skills$", re.IGNORECASE)
SKILL_COMMAND_PATTERN = re.compile(
    r"^(?:use|run)\s+([a-zA-Z0-9_-]+)\s+skill(?:\s+to)?\s+(.+)$",
    re.IGNORECASE,
)


def describe_skills():
    entries = []
    for name, skill in DEFAULT_SKILLS.items():
        entries.append(f"{name}: {skill['description']}")
    return "Available skills: " + " | ".join(entries)


def is_skill_list_request(text):
    return bool(LIST_SKILLS_PATTERN.match(" ".join(str(text).strip().split())))


def parse_skill_command(text):
    normalized = " ".join(str(text).strip().split())
    match = SKILL_COMMAND_PATTERN.match(normalized)
    if not match:
        return None
    skill_name = match.group(1).lower()
    payload = match.group(2).strip()
    if skill_name not in DEFAULT_SKILLS:
        return None
    return {"skill": skill_name, "payload": payload}
