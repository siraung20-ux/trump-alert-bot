import os
import requests
import feedparser
import json
from datetime import datetime
from openai import OpenAI

# --- Configuration --- #
TRUTH_SOCIAL_RSS_FEED = "https://trumpstruth.org/feed"
X_API_BASE_URL = "https://api.twitter.com/2/"

# GitHub Secrets မှ Environment Variables များ
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
X_BEARER_TOKEN = os.environ.get("X_BEARER_TOKEN")

openai_client = OpenAI(api_key=OPENAI_API_KEY)
LAST_POST_IDS_FILE = os.environ.get("LAST_POST_IDS_FILE", "last_post_ids.json")

def load_last_post_ids():
    if os.path.exists(LAST_POST_IDS_FILE):
        try:
            with open(LAST_POST_IDS_FILE, "r") as f:
                return json.load(f)
        except:
            return {"truth_social": None, "x": None}
    return {"truth_social": None, "x": None}

def save_last_post_ids(last_ids):
    with open(LAST_POST_IDS_FILE, "w") as f:
        json.dump(last_ids, f, indent=4)

def translate_to_burmese(text):
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that translates English to Burmese."},
                {"role": "user", "content": f"Translate the following English text to Burmese: {text}"}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[ဘာသာပြန်ရာတွင် အမှားရှိနေပါသည်: {e}]"

def send_telegram(text, image_url=None):
    if image_url:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        payload = {"chat_id": CHANNEL_ID, "photo": image_url, "caption": text[:1024], "parse_mode": "HTML"}
    else:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHANNEL_ID, "text": text, "parse_mode": "HTML"}
    
    try:
        requests.post(url, json=payload).raise_for_status()
    except Exception as e:
        print(f"Telegram Error: {e}")

def fetch_truth_social(last_id):
    feed = feedparser.parse(TRUTH_SOCIAL_RSS_FEED)
    new_posts = []
    current_latest = last_id
    for entry in feed.entries:
        post_id = entry.truth_originalId if hasattr(entry, 'truth_originalId') else entry.id
        if last_id and post_id == last_id: break
        if current_latest is None or post_id > current_latest: current_latest = post_id
        new_posts.append({"source": "Truth Social", "id": post_id, "text": entry.description, "link": entry.link, "timestamp": entry.published, "images": []})
    new_posts.reverse()
    return new_posts, current_latest

def fetch_x(last_id):
    ELON_MUSK_ID = "44196397"
    headers = {"Authorization": f"Bearer {X_BEARER_TOKEN}"}
    params = {"max_results": 5, "tweet.fields": "created_at,attachments", "expansions": "attachments.media_keys", "media.fields": "url"}
    if last_id: params["since_id"] = last_id
    
    try:
        res = requests.get(f"{X_API_BASE_URL}users/{ELON_MUSK_ID}/tweets", headers=headers, params=params)
        res.raise_for_status()
        data = res.json()
        new_posts = []
        current_latest = last_id
        if "data" in data:
            for tweet in data["data"]:
                post_id = tweet["id"]
                if current_latest is None or int(post_id) > int(current_latest): current_latest = post_id
                imgs = []
                if "attachments" in tweet and "media_keys" in tweet["attachments"] and "includes" in data:
                    for mk in tweet["attachments"]["media_keys"]:
                        for m in data["includes"].get("media", []):
                            if m["media_key"] == mk and m["type"] == "photo": imgs.append(m["url"])
                new_posts.append({"source": "X", "id": post_id, "text": tweet["text"], "link": f"https://x.com/elonmusk/status/{post_id}", "timestamp": tweet["created_at"], "images": imgs})
        new_posts.reverse()
        return new_posts, current_latest
    except Exception as e:
        print(f"X API Error: {e}")
        return [], last_id

def main():
    last_ids = load_last_post_ids()
    all_posts = []
    
    ts_posts, ts_id = fetch_truth_social(last_ids["truth_social"])
    all_posts.extend(ts_posts)
    last_ids["truth_social"] = ts_id
    
    x_posts, x_id = fetch_x(last_ids["x"])
    all_posts.extend(x_posts)
    last_ids["x"] = x_id

    for post in all_posts:
        translated = translate_to_burmese(post['text'])
        msg = f"<b>New from {post['source']}</b>\n\n{post['text']}\n\n<b>မြန်မာဘာသာပြန်:</b>\n{translated}\n\n<a href='{post['link']}'>Link</a>"
        if post['images']:
            send_telegram(msg, post['images'][0])
        else:
            send_telegram(msg)
            
    save_last_post_ids(last_ids)

if __name__ == "__main__":
    main()
    
