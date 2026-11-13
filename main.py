import os
import re
import html
import requests
import feedparser
from google import genai
from openai import OpenAI

# ==================================
# CONFIG
# ==================================

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

DECISION_URL = "https://generativelanguage.googleapis.com/v1beta/decisions"

LAST_FILE = "last_post.txt"
ALJAZEERA_LAST_FILE = "last_aljazeera.txt"


# ==================================
# LAST POST TRACKING
# ==================================

def get_last(file):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""


def save_last(file, value):
    with open(file, "w", encoding="utf-8") as f:
        f.write(value)


# ==================================
# GEMINI DECISION API
# ==================================

def find_decision(data, key):
    """Find a decision field even if the API response is nested."""

    if isinstance(data, dict):
        if key in data:
            return data[key]

        for value in data.values():
            result = find_decision(value, key)
            if result is not None:
                return result

    elif isinstance(data, list):
        for item in data:
            result = find_decision(item, key)
            if result is not None:
                return result

    return None


def decision_value(item, possible_keys):
    if isinstance(item, dict):
        for key in possible_keys:
            if key in item:
                return item[key]
    return item


def analyze_news(title, summary=""):

    text = f"""
Headline: {title}

Summary:
{summary}
"""

    questions = {
        "market_relevant": {
            "type": "noul",
            "description": (
                "Is this news relevant to financial markets, stocks, "
                "cryptocurrency, currencies, commodities, or investors?"
            )
        },

        "category": {
            "type": "choice",
            "options": [
                "politics",
                "war_conflict",
                "economy_trade",
                "crypto",
                "financial_markets",
                "other"
            ],
            "description": "Choose the main category of this news."
        },

        "sentiment": {
            "type": "choice",
            "options": [
                "bullish",
                "bearish",
                "neutral",
                "unclear"
            ],
            "description": (
                "What is the likely market impact sentiment of this news?"
            )
        },

        "importance": {
            "type": "score",
            "criteria": [
                "Low: Limited impact or routine news.",
                "Medium: Meaningful development with some market impact.",
                "High: Major geopolitical, economic, or financial event "
                "with potentially significant market impact."
            ],
            "description": "Rate the importance of this news."
        }
    }

    try:
        response = requests.post(
            DECISION_URL,
            headers={
                "x-goog-api-key": GEMINI_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "model": "gemini-decision-1",
                "input": text,
                "questions": questions
            },
            timeout=45
        )

        response.raise_for_status()
        data = response.json()

        market_item = find_decision(data, "market_relevant")
        category_item = find_decision(data, "category")
        sentiment_item = find_decision(data, "sentiment")
        importance_item = find_decision(data, "importance")

        market_score = decision_value(
            market_item, ["noul", "value", "score"]
        )

        category = decision_value(
            category_item, ["choice", "value", "result"]
        )

        sentiment = decision_value(
            sentiment_item, ["choice", "value", "result"]
        )

        importance_score = decision_value(
            importance_item, ["score", "value", "result"]
        )

        try:
            market_score = float(market_score)
        except (TypeError, ValueError):
            market_score = 0

        try:
            importance_score = float(importance_score)
        except (TypeError, ValueError):
            importance_score = 0

        print("Decision API: Success")
        print("Market Score:", market_score)
        print("Category:", category)
        print("Sentiment:", sentiment)
        print("Importance:", importance_score)

        return {
            "market": market_score >= 0.65,
            "market_score": market_score,
            "category": str(category or "other"),
            "sentiment": str(sentiment or "unclear"),
            "importance": importance_score
        }

    except Exception as e:
        print("Decision API Error:", e)
        return None


# ==================================
# FORMAT MARKET ANALYSIS
# ==================================

def format_analysis(result):

    if not result:
        return (
            "📊 MARKET ANALYSIS\n"
            "⚪ Analysis unavailable"
        )

    categories = {
        "politics": "Politics",
        "war_conflict": "War / Conflict",
        "economy_trade": "Economy / Trade",
        "crypto": "Crypto",
        "financial_markets": "Financial Markets",
        "other": "Other"
    }

    sentiments = {
        "bullish": "🟢 Bullish",
        "bearish": "🔴 Bearish",
        "neutral": "⚪ Neutral",
        "unclear": "❔ Unclear"
    }

    category = result["category"].lower()
    sentiment = result["sentiment"].lower()
    score = result["importance"]

    if score >= 1.5:
        importance = "🔴 HIGH"
    elif score >= 0.5:
        importance = "🟡 MEDIUM"
    else:
        importance = "🟢 LOW"

    market = "Yes" if result["market"] else "No"

    return f"""📊 MARKET ANALYSIS

💹 Market Relevant: {market}
📂 Category: {categories.get(category, category)}
📈 Sentiment: {sentiments.get(sentiment, "❔ Unclear")}
⚡ Importance: {importance}"""


# ==================================
# BURMESE TRANSLATION
# ==================================

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
- Preserve the original meaning
- Use natural, easy-to-understand Burmese

Text:
{text}
"""
        )

        if response.text:
            print("Translation: Gemini")
            return response.text.strip()

    except Exception as e:
        print("Gemini Translation Error:", e)

    # OpenRouter
    try:
        response = openrouter_client.chat.completions.create(
            model="deepseek/deepseek-chat:free",
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


# ==================================
# TELEGRAM
# ==================================

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

        if not r.ok:
            print("Telegram Error:", r.text)

        return r.ok

    except Exception as e:
        print("Telegram Error:", e)
        return False


# ==================================
# CLEAN RSS CONTENT
# ==================================

def clean_text(text):

    if not text:
        return ""

    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


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
# PROCESS NEWS
# ==================================

def process_news(entry, source_name, emoji):

    title = getattr(entry, "title", "").strip()

    if not valid_title(title):
        print("Skipped: Invalid title")
        return

    link = getattr(entry, "link", "").strip()

    summary = clean_text(
        getattr(entry, "summary", "")
    )

    print("--------------------------------")
    print("Processing:", title)

    # Market analysis
    analysis = analyze_news(title, summary)
    analysis_text = format_analysis(analysis)

    # Burmese translation
    mm = translate_burmese(title)

    message = f"""🚨 {source_name}

🇺🇸 English:
{title}

🇲🇲 Burmese:
{mm}

{analysis_text}

🔗 Source:
{link}"""

    sent = send_telegram(message)

    if sent:
        print(source_name, "Sent:", link)
    else:
        print(source_name, "Failed to send:", link)


# ==================================
# TRUMP TRUTH RSS
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

                process_news(
                    entry,
                    "TRUMP TRUTH UPDATE",
                    "🇺🇸"
                )

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
            print("First Al Jazeera Run")

        elif newest_link != last_id:

            new_posts = []

            for entry in feed.entries:

                if entry.link == last_id:
                    break

                new_posts.append(entry)

            new_posts.reverse()

            print("Al Jazeera New Posts:", len(new_posts))

            for entry in new_posts:

                process_news(
                    entry,
                    "BREAKING NEWS",
                    "🌍"
                )

            save_last(ALJAZEERA_LAST_FILE, newest_link)

        else:

            print("No New Al Jazeera News")

except Exception as e:

    print("Al Jazeera RSS Error:", e)


print("Bot Finished Successfully")

