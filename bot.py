import os
import requests
import time
import json
from openai import OpenAI

# ================== CONFIG ==================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHANNEL_ID")
X_BEARER_TOKEN = os.environ.get("X_BEARER_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

LAST_IDS_FILE = "last_ids.json"

# OpenAI Client
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# ===========================================

def translate_to_burmese(text):
    if not client or not text:
        return "ဘာသာပြန်ဆိုရန် မအောင်မြင်ပါ။"
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional translator. Translate the following post into natural, easy-to-read Burmese language. Return ONLY the translation."},
                {"role": "user", "content": text}
            ],
            max_tokens=800
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("Translation error:", e)
        return "ဘာသာပြန်ဆိုရာတွင် အမှားဖြစ်ပါသည်။"

def load_last_ids():
    if os.path.exists(LAST_IDS_FILE):
        try:
            with open(LAST_IDS_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_last_ids(data):
    with open(LAST_IDS_FILE, "w") as f:
        json.dump(data, f)

def send_telegram(message):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Telegram config missing")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
        print("✅ Sent to Telegram")
    except Exception as e:
        print("Telegram error:", e)

# ===================== MAIN JOB =====================
def check_posts():
    print("🚀 Starting check...")
    last_ids = load_last_ids()

    # === ELON MUSK ===
    if X_BEARER_TOKEN:
        try:
            print("Checking Elon Musk...")
            client_t = tweepy.Client(bearer_token=X_BEARER_TOKEN)  # tweepy import လုပ်မယ်
            response = client_t.get_users_tweets(
                id="44196397", max_results=5, tweet_fields=["created_at"]
            )
            if response.data:
                for tweet in reversed(response.data):
                    tid = str(tweet.id)
                    if tid != last_ids.get("elon"):
                        translated = translate_to_burmese(tweet.text)
                        msg = f"""
🚀 <b>Elon Musk</b>

🇲🇲 <b>ဗမာလို:</b>
{translated}

──────────────────
🇺🇸 <b>English:</b>
{tweet.text}

🔗 https://x.com/elonmusk/status/{tid}
                        """.strip()
                        send_telegram(msg)
                        last_ids["elon"] = tid
                        save_last_ids(last_ids)
                        time.sleep(3)
        except Exception as e:
            print("Elon Error:", e)

    # === TRUMP (Truth Social) ===
    try:
        print("Checking Donald Trump...")
        url = "https://truthsocial.com/api/v1/accounts/107780257626128497/statuses?limit=5"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        r.raise_for_status()
        posts = r.json()

        for post in reversed(posts):
            pid = str(post.get("id"))
            if pid != last_ids.get("trump"):
                content = post.get("content", "").replace("<p>", "").replace("</p>", "").replace("<br>", "\n")
                translated = translate_to_burmese(content)

                msg = f"""
🇺🇸 <b>Donald J. Trump</b>

🇲🇲 <b>ဗမာလို:</b>
{translated}

──────────────────
🇺🇸 <b>English:</b>
{content}

🔗 https://truthsocial.com/@realDonaldTrump/posts/{pid}
                """.strip()
                send_telegram(msg)
                last_ids["trump"] = pid
                save_last_ids(last_ids)
                time.sleep(3)
    except Exception as e:
        print("Trump Error:", e)

    print("✅ Check completed.")

# ================== RUN ==================
if __name__ == "__main__":
    import tweepy  # ဒီနေရာမှာ import လုပ်မယ်
    check_posts()
