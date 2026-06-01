import os
import requests
import feedparser

TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHANNEL_ID")
RSS_FEED_URL = "https://trumpstruth.org/feed"
LAST_POST_FILE = "last_post_link.txt"

def get_last_post_link():
    if os.path.exists(LAST_POST_FILE):
        with open(LAST_POST_FILE, "r") as f:
            return f.read().strip()
    return None

def set_last_post_link(link):
    with open(LAST_POST_FILE, "w") as f:
        f.write(link)

def send_telegram_message(message):
    if not TOKEN or not CHAT_ID:
        print("Telegram BOT_TOKEN or CHANNEL_ID not set.")
        return

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print(f"Telegram message sent: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending Telegram message: {e}")

def check_for_new_posts():
    feed = feedparser.parse(RSS_FEED_URL)
    if not feed.entries:
        print("No entries found in RSS feed.")
        return

    last_post_link = get_last_post_link()
    new_posts = []

    for entry in reversed(feed.entries):
        if entry.link == last_post_link:
            break
        new_posts.append(entry)

    if new_posts:
        for post in new_posts:
            message = f"<b>New Trump Post!</b>\n\n{post.title}\n\nRead more: {post.link}"
            send_telegram_message(message)
        set_last_post_link(new_posts[-1].link)
    else:
        print("No new posts.")

if __name__ == "__main__":
    check_for_new_posts()
    
