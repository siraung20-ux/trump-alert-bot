import os
import json
import feedparser
import requests
from openai import OpenAI

RSS_URL = "https://trumpstruth.org/feed"

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)

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
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Translate into natural Burmese. Return only Burmese."
                },
                {
                    "role": "user",
                    "content": text
                }
            ]
        )
        return r.choices[0].message.content.strip()
    except Exception:
        return "ဘာသာပြန်မရပါ။"


def send_telegram(msg):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": CHANNEL_ID,
            "text": msg
        }
    )


feed = feedparser.parse(RSS_URL)

if not feed.entries:
    raise Exception("RSS feed empty")

latest = feed.entries[0]

post_id = latest.id
title = latest.title

last_id = get_last_id()

if post_id != last_id:

    mm = translate_burmese(title)

    message = f"""🚨 Trump New Truth

🇺🇸 English:
{title}

🇲🇲 Burmese:
{mm}
"""

    send_telegram(message)

    save_last_id(post_id)

    print("New post sent")

else:
    print("No new post")
