
import os
import re
import json
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

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

GEMINI_MODEL = "gemini-2.5-flash"

client = (
    genai.Client(api_key=GEMINI_API_KEY)
    if GEMINI_API_KEY else None
)

openrouter_client = (
    OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1"
    )
    if OPENROUTER_API_KEY else None
)

deepseek_client = (
    OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com"
    )
    if DEEPSEEK_API_KEY else None
)

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
# JSON PARSER
# ==================================

def parse_json(text):

    if not text:
        raise ValueError("Empty AI response")

    text = text.strip()

    # Remove markdown code fences
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Extract JSON object if extra text exists
    match = re.search(r"\{.*\}", text, re.DOTALL)

    if match:
        return json.loads(match.group())

    raise ValueError("Invalid JSON response")


# ==================================
# MARKET ANALYSIS PROMPT
# ==================================

def market_prompt(title, summary):

    return f"""
You are a professional financial news analyst.

Analyze the following news for possible financial market impact.

NEWS HEADLINE:
{title}

NEWS SUMMARY:
{summary[:2500]}

Return ONLY valid JSON with these fields:

{{
  "market_relevant": true,
  "category": "politics",
  "sentiment": "neutral",
  "importance": 1,
  "impact": "Short explanation of possible market impact."
}}

RULES:

1. market_relevant:
true if the news has a meaningful connection to:
Stocks, Crypto, Forex, Gold, Oil, Commodities,
Interest rates, Inflation, Trade or Global Economy.

false if there is no meaningful direct market connection.

2. category must be exactly one of:
politics
war_conflict
economy_trade
crypto
financial_markets
other

3. sentiment must be exactly one of:
bullish
bearish
neutral
unclear

Sentiment refers to the likely overall market impact,
not whether the news is good or bad politically.

4. importance must be an integer:
1 = LOW
2 = MEDIUM
3 = HIGH

5. impact:
Write one short sentence explaining the potential market impact.
Do not invent facts or price predictions.

6. If there is no direct market impact:
market_relevant = false
sentiment = neutral
importance = 1

7. Do not confuse speculation with confirmed facts.
"""


# ==================================
# VALIDATE ANALYSIS
# ==================================

def validate_analysis(data):

    if not isinstance(data, dict):
        raise ValueError("Response is not a JSON object")

    category_options = [
        "politics",
        "war_conflict",
        "economy_trade",
        "crypto",
        "financial_markets",
        "other"
    ]

    sentiment_options = [
        "bullish",
        "bearish",
        "neutral",
        "unclear"
    ]

    category = str(data.get("category", "other")).lower()
    sentiment = str(data.get("sentiment", "unclear")).lower()

    if category not in category_options:
        category = "other"

    if sentiment not in sentiment_options:
        sentiment = "unclear"

    market = data.get("market_relevant", False)

    if isinstance(market, str):
        market = market.lower() in ("true", "yes", "1")

    if not isinstance(market, bool):
        market = False

    try:
        importance = int(data.get("importance", 1))
    except (TypeError, ValueError):
        importance = 1

    importance = max(1, min(3, importance))

    impact = str(
        data.get("impact", "No direct market impact identified.")
    ).strip()

    if not market:
        sentiment = "neutral"
        importance = 1

    return {
        "market": market,
        "category": category,
        "sentiment": sentiment,
        "importance": importance,
        "impact": impact[:400]
    }


# ==================================
# GEMINI MARKET ANALYSIS
# ==================================

def analyze_gemini(prompt):

    if not client:
        raise ValueError("GEMINI_API_KEY missing")

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "temperature": 0.1,
            "max_output_tokens": 400
        }
    )

    return validate_analysis(parse_json(response.text))


# ==================================
# OPENROUTER MARKET ANALYSIS
# ==================================

def analyze_openrouter(prompt):

    if not openrouter_client:
        raise ValueError("OPENROUTER_API_KEY missing")

    response = openrouter_client.chat.completions.create(
        model="deepseek/deepseek-chat:free",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a financial news analyst. "
                    "Return only valid JSON."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=400
    )

    return validate_analysis(
        parse_json(response.choices[0].message.content)
    )


# ==================================
# DEEPSEEK MARKET ANALYSIS
# ==================================

def analyze_deepseek(prompt):

    if not deepseek_client:
        raise ValueError("DEEPSEEK_API_KEY missing")

    response = deepseek_client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a financial news analyst. "
                    "Return only valid JSON."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=400
    )

    return validate_analysis(
        parse_json(response.choices[0].message.content)
    )


# ==================================
# MAIN ANALYSIS WITH FALLBACK
# ==================================

def analyze_news(title, summary=""):

    prompt = market_prompt(title, summary)

    providers = [
        ("Gemini", analyze_gemini),
        ("OpenRouter", analyze_openrouter),
        ("DeepSeek", analyze_deepseek)
    ]

    for provider_name, provider_function in providers:

        try:

            result = provider_function(prompt)

            print(f"Market Analysis: {provider_name} SUCCESS")
            print("Result:", result)

            return result

        except Exception as e:

            print(f"{provider_name} Analysis Error: {type(e).__name__}: {e}")

    print("ALL MARKET ANALYSIS PROVIDERS FAILED")

    return {
        "market": False,
        "category": "other",
        "sentiment": "unclear",
        "importance": 1,
        "impact": "Analysis unavailable. All AI providers failed."
    }


# ==================================
# FORMAT MARKET ANALYSIS
# ==================================

def format_analysis(result):

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

    importance_map = {
        1: "🟢 LOW",
        2: "🟡 MEDIUM",
        3: "🔴 HIGH"
    }

    if not result:
        return (
            "📊 MARKET ANALYSIS\n"
            "⚪ Analysis unavailable"
        )

    category = result["category"]
    sentiment = result["sentiment"]
    importance = result["importance"]

    market = "Yes" if result["market"] else "No"

    return f"""📊 MARKET ANALYSIS

💹 Market Relevant: {market}
📂 Category: {categories.get(category, "Other")}
📈 Sentiment: {sentiments.get(sentiment, "❔ Unclear")}
⚡ Importance: {importance_map.get(importance, "🟢 LOW")}

📝 Impact:
{result["impact"]}"""


# ==================================
# BURMESE TRANSLATION
# ==================================

def translate_burmese(text):

    if not text:
        return ""

    # Gemini
    if client:
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
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
    if openrouter_client:
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

            result = response.choices[0].message.content

            if result:
                print("Translation: OpenRouter")
                return result.strip()

        except Exception as e:
            print("OpenRouter Error:", e)

    # DeepSeek
    if deepseek_client:
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

            result = response.choices[0].message.content

            if result:
                print("Translation: DeepSeek")
                return result.strip()

        except Exception as e:
            print("DeepSeek Error:", e)

    return "ဘာသာပြန်ရန် ယာယီမရရှိနိုင်ပါ။"


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
        return False

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
        return True

    print(source_name, "Failed to send:", link)
    return False


# ==================================
# PROCESS RSS FEED
# ==================================

def process_feed(rss_url, last_file, source_name):

    try:

        feed = feedparser.parse(rss_url)

        if not feed.entries:
            print(source_name, "No RSS entries")
            return

        newest_link = feed.entries[0].link
        last_id = get_last(last_file)

        print(source_name, "Latest:", newest_link)
        print(source_name, "Last Saved:", last_id)

        if not last_id:

            save_last(last_file, newest_link)
            print("First Run:", source_name)
            return

        if newest_link == last_id:
            print("No New News:", source_name)
            return

        new_posts = []

        for entry in feed.entries:

            if getattr(entry, "link", "") == last_id:
                break

            new_posts.append(entry)

        new_posts.reverse()

        print(source_name, "New Posts:", len(new_posts))

        all_sent = True

        for entry in new_posts:

            sent = process_news(
                entry,
                source_name,
                ""
            )

            if not sent:
                all_sent = False

        # Save only when all posts were successfully sent
        if all_sent and new_posts:
            save_last(last_file, newest_link)
            print(source_name, "Tracking Updated")

        elif not new_posts:
            print(source_name, "Previous post not found in RSS feed")

    except Exception as e:

        print(source_name, "RSS Error:", e)


# ==================================
# MAIN
# ==================================

print("=================================")
print("TRUMP LIVE NEWS BOT STARTING")
print("=================================")

process_feed(
    RSS_URL,
    LAST_FILE,
    "TRUMP TRUTH UPDATE"
)

process_feed(
    ALJAZEERA_RSS,
    ALJAZEERA_LAST_FILE,
    "BREAKING NEWS"
)

print("=================================")
print("BOT FINISHED")
print("=================================")
            
