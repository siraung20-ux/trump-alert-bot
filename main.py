import os
import feedparser
import requests
from google import genai

RSS_URL = "https://trumpstruth.org/feed"
ALJAZEERA_RSS = "https://www.aljazeera.com/xml/rss/all.xml"

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

client = genai.Client(api_key=GEMINI_API_KEY)

LAST_FILE = "last_post.txt"
ALJAZEERA_LAST_FILE = "last_aljazeera.txt"

KEYWORDS = [
    "trump",
    "iran",
    "israel",
    "usa",
    "america",
    "china",
    "crypto",
    "bitcoin",
    "ethereum",
    "war",
    "hezbollah"
]


def get_last_id():
    if os.path.exists(LAST_FILE):
        with open(LAST_FILE, "r") as f:
            return f.read().strip()
    return ""


def save_last_id(post_id):
    with open(LAST_FILE, "w") as f:
        f.write(post_id)


def get_last_aljazeera_id():
    if os.path.exists(ALJAZEERA_LAST_FILE):
        with open(ALJAZEERA_LAST_FILE, "r") as f:
            return f.read().strip()
    return ""


def save_last_aljazeera_id(post_id):
    with open(ALJAZEERA_LAST_FILE, "w") as f:
        f.write(post_id)


def translate_burmese(text):
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""
Translate this news or social media post into natural Burmese.

Rules:
- Return Burmese only
- Do not explain
- Do not summarize
- Keep names unchanged
- Preserve original meaning

Text:
{text}
"""
        )
        return response.text.strip()

    except Exception as e:
        print("Gemini Error:", e)
        return "ဘာသာပြန်မရပါ။"


def send_telegram(message):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": CHANNEL_ID,
            "text": message,
            "disable_web_page_preview": True
        },
        timeout=30
    )


# ==========================
# TRUMP RSS
# ==========================

try:
    feed = feedparser.parse(RSS_URL)

    if feed.entries:

        last_id = get_last_id()
        new_posts = []

        for entry in reversed(feed.entries):
            if entry.link > last_id:
                new_posts.append(entry)

        if not new_posts:
            print("No Trump Post")

        else:
            for entry in new_posts:

                mm = translate_burmese(entry.title)

                message = f"""🚨 TRUMP TRUTH UPDATE

🇺🇸 English:
{entry.title}

🇲🇲 Burmese:
{mm}

🔗 Source:
{entry.link}
"""

                send_telegram(message)

                print("Trump Sent:", entry.link)

            save_last_id(feed.entries[0].link)

except Exception as e:
    print("Trump RSS Error:", e)


# ==========================
# AL JAZEERA BREAKING NEWS
# ==========================

try:
    aj_feed = feedparser.parse(ALJAZEERA_RSS)

    if aj_feed.entries:

        last_aj = get_last_aljazeera_id()
        new_aj_posts = []

        for entry in reversed(aj_feed.entries):

            title = entry.title.lower()

            if any(keyword in title for keyword in KEYWORDS):

                if entry.link > last_aj:
                    new_aj_posts.append(entry)

        if not new_aj_posts:
            print("No Al Jazeera News")

        else:

            for entry in new_aj_posts:

                mm = translate_burmese(entry.title)

                message = f"""🌍 BREAKING NEWS

🇺🇸 English:
{entry.title}

🇲🇲 Burmese:
{mm}

🔗 Source:
{entry.link}
"""

                send_telegram(message)

                print("AJ Sent:", entry.link)

            save_last_aljazeera_id(new_aj_posts[-1].link)

except Exception as e:
    print("Al Jazeera RSS Error:", e)

print("Bot Finished Successfully")
