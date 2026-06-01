import os
import feedparser
import requests
from google import genai

RSS_URL = "https://trumpstruth.org/feed"

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

client = genai.Client(api_key=GEMINI_API_KEY)

LAST_FILE = "last_post.txt"


def get_last_id():
    if os.path.exists(LAST_FILE):
        with open(LAST_FILE, "r") as f:
            return f.read().strip()
    return ""


def save_last_id(post_id):
    with open(LAST_FILE, "w") as f:
        f.write(post_id)


def translate_burmese(text):
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""
Translate this social media post into natural Burmese.

Rules:
- Return Burmese only.
- Do not explain.
- Do not summarize.
- Keep names unchanged.
- Preserve original meaning and tone.

Post:
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
        }
    )


feed = feedparser.parse(RSS_URL)

if not feed.entries:
    raise Exception("RSS Feed Empty")

latest = feed.entries[0]

post_id = latest.id
text = latest.title
link = latest.link

last_id = get_last_id()
print("Latest RSS ID:", post_id)
print("Last Saved ID:", last_id)
print("Latest Title:", text)
if post_id != last_id:

    mm = translate_burmese(text)

    message = f"""🚨 TRUMP TRUTH UPDATE

🇺🇸 English:
{text}

🇲🇲 Burmese:
{mm}

🔗 Source:
{link}
"""

    send_telegram(message)

    save_last_id(post_id)

    print("New Post Sent")

else:
    print("No New Post")
