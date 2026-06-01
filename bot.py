import os
import requests
import time
import traceback

# ================== CONFIG ==================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHANNEL_ID")
X_BEARER_TOKEN = os.environ.get("X_BEARER_TOKEN")

LAST_POST_FILE = "last_post_id.txt"

# Trump Truth Social
TRUMP_ACCOUNT_ID = "107780257626128497"
TRUTH_API_URL = f"https://truthsocial.com/api/v1/accounts/{TRUMP_ACCOUNT_ID}/statuses"

# Elon Musk
ELON_USER_ID = "44196397"

# ===========================================

def get_last_post_id():
    try:
        if os.path.exists(LAST_POST_FILE):
            with open(LAST_POST_FILE, "r") as f:
                return f.read().strip()
    except:
        pass
    return None

def set_last_post_id(post_id):
    try:
        with open(LAST_POST_FILE, "w") as f:
            f.write(str(post_id))
    except Exception as e:
        print(f"Error saving last_post_id: {e}")

def send_telegram_message(message):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Telegram config missing!")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        print("✅ Telegram sent successfully")
    except Exception as e:
        print(f"❌ Telegram error: {e}")

# ===================== TRUMP =====================
def check_trump_posts():
    print("🔍 Checking Trump posts...")
    headers = {"User-Agent": "Mozilla/5.0"}
    params = {"limit": 5}

    try:
        resp = requests.get(TRUTH_API_URL, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        posts = resp.json()

        last_id = get_last_post_id()
        print(f"Last known Trump ID: {last_id}")

        new_posts = []
        for post in posts:
            post_id = str(post.get("id"))
            if post_id and post_id != last_id:
                new_posts.append(post)
            else:
                break  # Stop when we hit the last known post

        if new_posts:
            print(f"Found {len(new_posts)} new Trump post(s)")
            for post in reversed(new_posts):
                content = post.get("content", "").replace("<p>", "").replace("</p>", "").replace("<br>", "\n\n").strip()
                
                message = f"""
🇺🇸 <b>Donald J. Trump</b>

{content}

🔗 https://truthsocial.com/@realDonaldTrump/posts/{post['id']}

──────────────────
🇲🇲 <b>ဒေါ်နယ်ဒ် ထရမ့်</b>

{content}
                """.strip()

                send_telegram_message(message)
                time.sleep(2)

            set_last_post_id(new_posts[0]["id"])
        else:
            print("No new Trump posts.")

    except Exception as e:
        print(f"❌ Truth Social Error: {e}")
        traceback.print_exc()

# ===================== ELON =====================
def check_elon_posts():
    if not X_BEARER_TOKEN:
        print("❌ X_BEARER_TOKEN not found in environment")
        return

    print("🔍 Checking Elon Musk posts...")
    url = f"https://api.twitter.com/2/users/{ELON_USER_ID}/tweets"
    headers = {"Authorization": f"Bearer {X_BEARER_TOKEN}"}
    params = {"max_results": 5, "tweet.fields": "created_at"}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        posts = data.get("data", [])

        last_id = get_last_post_id()
        print(f"Last known Elon ID: {last_id}")

        new_posts = []
        for post in posts:
            post_id = str(post.get("id"))
            if post_id and post_id != last_id:
                new_posts.append(post)
            else:
                break

        if new_posts:
            print(f"Found {len(new_posts)} new Elon post(s)")
            for post in reversed(new_posts):
                text = post.get("text", "").replace('\n', '\n\n')
                
                message = f"""
🚀 <b>Elon Musk</b>

{text}

🔗 https://x.com/elonmusk/status/{post['id']}

──────────────────
🇲🇲 <b>အီလွန် မတ်စ်</b>

{text}
                """.strip()

                send_telegram_message(message)
                time.sleep(2)

            set_last_post_id(new_posts[0]["id"])
        else:
            print("No new Elon posts.")

    except Exception as e:
        print(f"❌ X (Twitter) Error: {e}")
        traceback.print_exc()

# ================== MAIN ==================
if __name__ == "__main__":
    print("🚀 Trump + Elon Alert Bot Started...")
    check_trump_posts()
    check_elon_posts()
    print("✅ Bot finished running.")
🔗 https://x.com/elonmusk/status/{post['id']}

──────────────────
🇲🇲 <b>အီလွန် မတ်စ်</b>

{text}
                """.strip()

                send_telegram_message(message)
                time.sleep(2)

            set_last_post_id(new_posts[0]["id"])

    except Exception as e:
        print(f"❌ X Error: {e}")

# ================== MAIN ==================
if __name__ == "__main__":
    print("🚀 Trump + Elon Alert Bot Started...")
    check_trump_posts()
    check_elon_posts()
    print("✅ Bot finished.")
