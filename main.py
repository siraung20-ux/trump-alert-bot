import os
import feedparser
import requests
from google import genai
from openai import OpenAI

RSS_URL = "https://trumpstruth.org/feed"
ALJAZEERA_RSS = "https://www.aljazeera.com/xml/rss/all.xml"

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]

client = genai.Client(api_key=GEMINI_API_KEY)

openrouter_client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

deepseek_client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

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
    "hezbollah",
    "lebanon",
    "gaza",
    "russia",
    "ukraine",
    "nato",
    "syria"
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

    # Gemini
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""
Translate this text into natural Burmese.

Rules:
- Return Burmese only
- Keep names unchanged
- Preserve meaning
- Do not explain

Text:
{text}
"""
        )

        result = response.text.strip()

        if result:
            print("Translation: Gemini")
            return result

    except Exception as e:
        print("Gemini Error:", e)

    # OpenRouter
    try:
        response = openrouter_client.chat.completions.create(
            model="google/gemini-2.0-flash-exp:free",
            messages=[
                {
                    "role": "system",
                    "content": "Translate into natural Burmese. Return Burmese only."
                },
                {
                    "role": "user",
                    "content": text
                }
            ]
        )

        result = response.choices[0].message.content.strip()

        if result:
            print("Translation: OpenRouter")
            return result

    except Exception as e:
        print("OpenRouter Error:", e)

    # DeepSeek
    try:
        response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": "Translate into natural Burmese. Return Burmese only."
                },
                {
                    "role": "user",
                    "content": text
                }
            ]
        )

        result = response.choices[0].message.content.strip()

        if result:
            print("Translation: DeepSeek")
            return result

    except Exception as e:
        print("DeepSeek Error:", e)

    print("Translation: Original English")
    return text


def send_telegram(message):
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": CHANNEL_ID,
                "text": message,
                "disable_web_page_preview": True
            },
            timeout=30
        )

    except Exception as e:
        print("Telegram Error:", e)


# ==================================
# TRUMP RSS
# ==================================

try:

    feed = feedparser.parse(RSS_URL)

    if feed.entries:

        last_id = get_last_id()

        if last_id == "":

            save_last_id(feed.entries[0].link)

            print("First Trump run completed")

        else:

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


# ==================================
# AL JAZEERA RSS
# ==================================

try:

    aj_feed = feedparser.parse(ALJAZEERA_RSS)

    if aj_feed.entries:

        last_aj = get_last_aljazeera_id()

        if last_aj == "":

            save_last_aljazeera_id(aj_feed.entries[0].link)

            print("First Al Jazeera run completed")

        else:

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

                save_last_aljazeera_id(aj_feed.entries[0].link)

except Exception as e:

    print("Al Jazeera RSS Error:", e)

print("Bot Finished Successfully")
