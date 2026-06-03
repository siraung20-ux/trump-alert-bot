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


def get_last(file):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""


def save_last(file, value):
    with open(file, "w", encoding="utf-8") as f:
        f.write(value)


def translate_burmese(text):

    if not text:
        return ""

    # Gemini
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""
Translate into natural Burmese.

Rules:
- Burmese only
- Keep names unchanged
- No explanations
- Preserve meaning

Text:
{text}
"""
        )

        if response.text:
            print("Translation: Gemini")
            return response.text.strip()

    except Exception as e:
        print("Gemini Error:", e)

    # OpenRouter
    try:
        response = openrouter_client.chat.completions.create(
            model="deepseek/deepseek-chat-v3-0324:free",
            messages=[
                {
                    "role": "system",
                    "content": "Translate into natural Burmese only."
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
                    "content": "Translate into natural Burmese only."
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

    return text


def send_telegram(message):

    try:
        r = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": CHANNEL_ID,
                "text": message,
                "disable_web_page_preview": True
            },
            timeout=30
        )

        print("Telegram:", r.status_code)

    except Exception as e:
        print("Telegram Error:", e)


def valid_title(title):

    if not title:
        return False

    title = title.strip()

    if not title:
        return False

    if "[No Title]" in title:
        return False

    return True


# ==================================
# TRUMP RSS
# ==================================

try:

    feed = feedparser.parse(RSS_URL)

    if feed.entries:

        newest_link = feed.entries[0].link
        last_id = get_last(LAST_FILE)

        print("Trump Latest:", newest_link)
        print("Trump Last Saved:", last_id)

        if not last_id:

            save_last(LAST_FILE, newest_link)
            print("First Trump Run")

        elif newest_link != last_id:

            new_posts = []

            for entry in feed.entries:

                if entry.link == last_id:
                    break

                new_posts.append(entry)

            new_posts.reverse()

            print("Trump New Posts:", len(new_posts))

            for entry in new_posts:

                title = getattr(entry, "title", "").strip()

                if not valid_title(title):
                    print("Skipped:", entry.link)
                    continue

                mm = translate_burmese(title)

                message = f"""🚨 TRUMP TRUTH UPDATE

🇺🇸 English:
{title}

🇲🇲 Burmese:
{mm}

🔗 Source:
{entry.link}
"""

                send_telegram(message)

                print("Trump Sent:", entry.link)

            save_last(LAST_FILE, newest_link)

        else:

            print("No New Trump Post")

except Exception as e:

    print("Trump RSS Error:", e)


# ==================================
# AL JAZEERA RSS
# ==================================

try:

    feed = feedparser.parse(ALJAZEERA_RSS)

    if feed.entries:

        newest_link = feed.entries[0].link
        last_id = get_last(ALJAZEERA_LAST_FILE)

        print("AJ Latest:", newest_link)
        print("AJ Last Saved:", last_id)

        if not last_id:

            save_last(ALJAZEERA_LAST_FILE, newest_link)
            print("First AJ Run")

        elif newest_link != last_id:

            new_posts = []

            for entry in feed.entries:

                if entry.link == last_id:
                    break

                new_posts.append(entry)

            new_posts.reverse()

            print("AJ New Posts:", len(new_posts))

            for entry in new_posts:

                title = getattr(entry, "title", "").strip()

                if not valid_title(title):
                    continue

                mm = translate_burmese(title)

                message = f"""🌍 BREAKING NEWS

🇺🇸 English:
{title}

🇲🇲 Burmese:
{mm}

🔗 Source:
{entry.link}
"""

                send_telegram(message)

                print("AJ Sent:", entry.link)

            save_last(ALJAZEERA_LAST_FILE, newest_link)

        else:

            print("No New Al Jazeera News")

except Exception as e:

    print("Al Jazeera RSS Error:", e)

print("Bot Finished Successfully")
