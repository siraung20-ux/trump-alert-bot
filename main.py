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


# =========================
# LAST ID SYSTEM
# =========================

def get_last(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return f.read().strip()
    return ""


def save_last(file, value):
    with open(file, "w") as f:
        f.write(value)


# =========================
# BURMESE TRANSLATION (API CHAIN)
# =========================

def translate_burmese(text):

    # Gemini
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""
Translate into natural Burmese.

Rules:
- Burmese only
- No explanation
- Keep names

Text:
{text}
"""
        )
        if response.text:
            print("Translation: Gemini")
            return response.text.strip()
    except Exception as e:
        print("Gemini Error:", e)

    # OpenRouter fallback
    try:
        response = openrouter_client.chat.completions.create(
            model="google/gemini-2.0-flash-exp:free",
            messages=[
                {"role": "system", "content": "Translate into natural Burmese only."},
                {"role": "user", "content": text}
            ]
        )
        result = response.choices[0].message.content.strip()
        print("Translation: OpenRouter")
        return result
    except Exception as e:
        print("OpenRouter Error:", e)

    # DeepSeek fallback
    try:
        response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Translate into natural Burmese only."},
                {"role": "user", "content": text}
            ]
        )
        result = response.choices[0].message.content.strip()
        print("Translation: DeepSeek")
        return result
    except Exception as e:
        print("DeepSeek Error:", e)

    return text


# =========================
# TELEGRAM
# =========================

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


# =========================
# TRUMP RSS (ALL POSTS)
# =========================

try:
    feed = feedparser.parse(RSS_URL)

    if feed.entries:
        last_id = get_last(LAST_FILE)

        if not last_id:
            save_last(LAST_FILE, feed.entries[0].link)
            print("First run (Trump)")
        else:
            new_posts = []

            for entry in reversed(feed.entries):
                if entry.link != last_id:
                    new_posts.append(entry)

            if new_posts:
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
                    print("Sent:", entry.link)

                save_last(LAST_FILE, feed.entries[0].link)
            else:
                print("No new Trump posts")

except Exception as e:
    print("Trump RSS Error:", e)


# =========================
# AL JAZEERA RSS (ALL POSTS)
# =========================

try:
    aj_feed = feedparser.parse(ALJAZEERA_RSS)

    if aj_feed.entries:
        last_aj = get_last(ALJAZEERA_LAST_FILE)

        if not last_aj:
            save_last(ALJAZEERA_LAST_FILE, aj_feed.entries[0].link)
            print("First run (AJ)")
        else:
            new_aj = []

            for entry in reversed(aj_feed.entries):
                if entry.link != last_aj:
                    new_aj.append(entry)

            if new_aj:
                for entry in new_aj:

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
                    print("Sent AJ:", entry.link)

                save_last(ALJAZEERA_LAST_FILE, aj_feed.entries[0].link)
            else:
                print("No new Al Jazeera posts")

except Exception as e:
    print("Al Jazeera RSS Error:", e)

print("Bot Finished Successfully")
