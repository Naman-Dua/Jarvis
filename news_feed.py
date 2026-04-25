"""News headlines from RSS feeds — no API key needed."""

import re
import requests
from bs4 import BeautifulSoup

NEWS_PATTERNS = [
    re.compile(r"^(?:(?:latest|top|today(?:'s)?|current)\s+)?(?:news|headlines)(?: (?:about|on) (.+))?$", re.I),
    re.compile(r"^what(?:'s| is) (?:happening|going on|in the news)(?: (?:about|with) (.+))?$", re.I),
]

RSS_FEEDS = {
    "general": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    "tech": "https://feeds.feedburner.com/TechCrunch/",
    "world": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
}


def is_news_request(text):
    normalized = " ".join(str(text).strip().split())
    return any(p.match(normalized) for p in NEWS_PATTERNS)


def _extract_topic(text):
    normalized = " ".join(str(text).strip().split())
    for pattern in NEWS_PATTERNS:
        m = pattern.match(normalized)
        if m and m.groups() and m.group(1):
            return m.group(1).strip()
    return None


def fetch_headlines(feed_url, limit=5):
    try:
        r = requests.get(feed_url, timeout=8, headers={
            "User-Agent": "Mozilla/5.0"
        })
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "xml")
        items = soup.find_all("item", limit=limit)
        headlines = []
        for item in items:
            title = item.find("title")
            if title:
                headlines.append(title.get_text(strip=True))
        return headlines
    except Exception:
        return []


def handle_news_command(text):
    topic = _extract_topic(text)

    if topic and "tech" in topic.lower():
        feed = RSS_FEEDS["tech"]
    elif topic and "world" in topic.lower():
        feed = RSS_FEEDS["world"]
    else:
        feed = RSS_FEEDS["general"]

    headlines = fetch_headlines(feed, limit=5)
    if headlines:
        numbered = ". ".join(f"{i+1}. {h}" for i, h in enumerate(headlines))
        return {"action": "news", "reply": f"Top headlines: {numbered}"}
    return {"action": "news", "reply": "Could not fetch news right now."}
