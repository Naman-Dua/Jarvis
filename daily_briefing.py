from weather import fetch_weather
from news_feed import fetch_headlines, RSS_FEEDS
from datetime import datetime

def get_daily_briefing(reminder_manager):
    """Generate a combined report of weather, news, and tasks."""
    now = datetime.now()
    
    # 1. Weather
    weather = fetch_weather() # Default location
    weather_snippet = f"Currently, it is {weather}." if weather else "I couldn't fetch the weather right now."
    
    # 2. Tasks
    tasks_snippet = reminder_manager.describe_today(now)
    
    # 3. News
    headlines = fetch_headlines(RSS_FEEDS["general"], limit=3)
    if headlines:
        news_snippet = "The top news headlines are: " + ". ".join(headlines)
    else:
        news_snippet = "I couldn't fetch the news right now."
        
    briefing = (
        f"Good day! Here is your daily briefing. "
        f"{weather_snippet} "
        f"{tasks_snippet} "
        f"{news_snippet} "
        f"I'm ready for any other tasks you have."
    )
    return briefing

def is_briefing_request(text):
    import re
    patterns = [
        r"^(?:good )?(?:morning|afternoon|evening|day)$",
        r"(?:daily )?briefing",
        r"what(?:'s| is) (?:my |the )?day look like",
        r"how is my day",
    ]
    normalized = text.lower().strip()
    return any(re.search(p, normalized) for p in patterns)

def handle_briefing_command(text, reminder_manager):
    if is_briefing_request(text):
        return {"action": "daily_briefing", "reply": get_daily_briefing(reminder_manager)}
    return None
