import os
import requests
import time

# Config
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHANNEL_ID")
X_BEARER_TOKEN = os.environ.get("X_BEARER_TOKEN")

LAST_FILE = "last_post_id.txt"

def get_last_id():
    try:
        if os.path.exists(LAST_FILE):
            with open(LAST_FILE, "r") as f:
                return f.read().strip()
    except:
        pass
    return "0"

def save_last_id(post_id):
    try:
        with open(LAST_FILE, "w") as f:
            f.write(str(post_id))
    except:
        pass

def send_to_telegram(text):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Telegram config missing")
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        }
        requests.post(url, json=data, timeout=10)
        print("✅ Sent to Telegram")
    except Exception as e:
        print("Telegram send failed:", e)

print("🚀 Bot started...")

# === TRUMP ===
print("Checking Trump on Truth Social...")
try:
    url = "https://truthsocial.com/api/v1/accounts/107780257626128497/statuses?limit=3"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    r.raise_for_status()
    posts = r.json()

    last_id = get_last_id()
    for post in posts:
        pid = str(post.get("id"))
        if pid != last_id and pid != "0":
            content = post.get("content", "").replace("<p>", "").replace("</p>", "").replace("<br>", "\n")
            msg = f"""🇺🇸 <b>Donald J. Trump</b>

{content}

🔗 https://truthsocial.com/@realDonaldTrump/posts/{pid}

──────────────────
🇲🇲 <b>ဒေါ်နယ်ဒ် ထရမ့်</b>

{content}"""
            send_to_telegram(msg)
            save_last_id(pid)
            break
except Exception as e:
    print("Trump Error:", str(e))

# === ELON ===
print("Checking Elon on X...")
if X_BEARER_TOKEN:
    try:
        url = "https://api.twitter.com/2/users/44196397/tweets?max_results=3"
        headers = {"Authorization": f"Bearer {X_BEARER_TOKEN}"}
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()
        posts = data.get("data", [])

        last_id = get_last_id()
        for post in posts:
            pid = str(post.get("id"))
            if pid != last_id and pid != "0":
                text = post.get("text", "").replace("\n", "\n\n")
                msg = f"""🚀 <b>Elon Musk</b>

{text}

🔗 https://x.com/elonmusk/status/{pid}

──────────────────
🇲🇲 <b>အီလွန် မတ်စ်</b>

{text}"""
                send_to_telegram(msg)
                save_last_id(pid)
                break
    except Exception as e:
        print("Elon Error:", str(e))
else:
    print("No X Bearer Token provided")

print("✅ Bot finished")
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
