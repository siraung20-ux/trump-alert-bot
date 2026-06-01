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

print("TOTAL POSTS:", len(feed.entries))

for i in range(min(5, len(feed.entries))):
    print(i, feed.entries[i].link)

if not feed.entries:
    raise Exception("RSS Feed Empty")

latest = feed.entries[0]

post_id = latest.id
text = latest.title
link = latest.link

last_id = get_last_id()

new_posts = []

for entry in reversed(feed.entries):
    if entry.link > last_id:
        new_posts.append(entry)

if not new_posts:
    print("No New Post")
else:
    for entry in new_posts:

        post_id = entry.link
        text = entry.title
        link = entry.link

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

        print("Sent:", post_id)

    save_last_id(feed.entries[0].link)
