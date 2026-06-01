import os
import requests
import json
import time

TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHANNEL_ID")
# Truth Social Real API endpoint for realDonaldTrump
API_URL = "https://truthsocial.com/api/v1/accounts/107780257626128497/statuses"
LAST_POST_FILE = "last_post_id.txt"

def get_last_post_id():
    if os.path.exists(LAST_POST_FILE):
        with open(LAST_POST_FILE, "r") as f:
            return f.read().strip()
    return None

def set_last_post_id(post_id):
    with open(LAST_POST_FILE, "w") as f:
        f.write(str(post_id))

def send_telegram_message(message):
    if not TOKEN or not CHAT_ID:
        print("Telegram BOT_TOKEN or CHANNEL_ID not set.")
        return

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print(f"Telegram message sent.")
    except requests.exceptions.RequestException as e:
        print(f"Error sending Telegram message: {e}")

def check_for_new_posts():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(API_URL, headers=headers)
        response.raise_for_status()
        posts = response.json()
    except Exception as e:
        print(f"Error fetching Truth Social API: {e}")
        return

    if not posts:
        print("No posts found.")
        return

    last_post_id = get_last_post_id()
    
    if last_post_id is None:
        print("First run: saving latest post ID.")
        set_last_post_id(posts[0]['id'])
        return

    new_posts = []
    for post in posts:
        if str(post['id']) == last_post_id:
            break
        new_posts.append(post)

    if new_posts:
        for post in reversed(new_posts):
            # Clean content from HTML tags
            content = post.get('content', '').replace('<p>', '').replace('</p>', '\n').replace('<br />', '\n')
            # Handle ReTruthed posts
            if post.get('reblog'):
                reblog = post['reblog']
                reblog_content = reblog.get('content', '').replace('<p>', '').replace('</p>', '\n').replace('<br />', '\n')
                message = f"<b>Trump ReTruthed:</b>\n\n{reblog_content}\n\n<a href='{reblog['url']}'>View on Truth Social</a>"
            else:
                message = f"<b>Trump Post အသစ်တက်လာပါပြီ!</b>\n\n{content}\n\n<a href='{post['url']}'>View on Truth Social</a>"
            
            send_telegram_message(message)
            time.sleep(1)
        
        set_last_post_id(posts[0]['id'])
    else:
        print("No new posts.")

if __name__ == "__main__":
    check_for_new_posts()
    
