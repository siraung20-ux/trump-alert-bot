import os
import requests
import time

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHANNEL_ID")
X_BEARER_TOKEN = os.environ.get("X_BEARER_TOKEN")

LAST_POST_FILE = "last_post_id.txt"

def get_last_id():
    if os.path.exists(LAST_POST_FILE):
        with open(LAST_POST_FILE) as f:
            return f.read().strip()
    return "0"

def save_last_id(pid):
    with open(LAST_POST_FILE, "w") as f:
        f.write(str(pid))

def send_msg(text):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Telegram token missing")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, json=data, timeout=10)
        print("Sent to Telegram")
    except:
        print("Telegram send failed")

# === TRUMP ===
print("Checking Trump...")
try:
    url = "https://truthsocial.com/api/v1/accounts/107780257626128497/statuses?limit=3"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    posts = r.json()
    
    last = get_last_id()
    for p in posts[:2]:   # နှစ်ခုပဲ စစ်မယ်
        if str(p["id"]) != last:
            content = p.get("content", "").replace("<p>", "").replace("</p>", "").replace("<br>", "\n")
            msg = f"""🇺🇸 <b>Donald J. Trump</b>\n\n{content}\n\n🔗 https://truthsocial.com/@realDonaldTrump/posts/{p["id"]}\n\n──────────────────\n🇲🇲 <b>ဒေါ်နယ်ဒ် ထရမ့်</b>\n\n{content}"""
            send_msg(msg)
            save_last_id(p["id"])
            break
except Exception as e:
    print("Trump Error:", e)

# === ELON ===
print("Checking Elon...")
if X_BEARER_TOKEN:
    try:
        url = "https://api.twitter.com/2/users/44196397/tweets?max_results=3"
        headers = {"Authorization": f"Bearer {X_BEARER_TOKEN}"}
        r = requests.get(url, headers=headers, timeout=15)
        data = r.json()
        posts = data.get("data", [])
        
        last = get_last_id()
        for p in posts:
            if str(p["id"]) != last:
                text = p["text"].replace("\n", "\n\n")
                msg = f"""🚀 <b>Elon Musk</b>\n\n{text}\n\n🔗 https://x.com/elonmusk/status/{p["id"]}\n\n──────────────────\n🇲🇲 <b>အီလွန် မတ်စ်</b>\n\n{text}"""
                send_msg(msg)
                save_last_id(p["id"])
                break
    except Exception as e:
        print("Elon Error:", e)
else:
    print("No X Bearer Token")

print("Bot finished")    params = {"max_results": 5, "tweet.fields": "created_at"}

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
