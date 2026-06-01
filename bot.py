import os
import requests
from openai import OpenAI

BEARER = os.environ["X_BEARER_TOKEN"]
TG_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TG_CHAT = os.environ["TELEGRAM_CHANNEL_ID"]
OPENAI_KEY = os.environ["OPENAI_API_KEY"]

client = OpenAI(api_key=OPENAI_KEY)

TRUMP_ID = "25073877"  # realDonaldTrump

def get_latest_tweet():
    url = f"https://api.twitter.com/2/users/{TRUMP_ID}/tweets"
    headers = {"Authorization": f"Bearer {BEARER}"}
    params = {"max_results": 5}

    r = requests.get(url, headers=headers, params=params)
    data = r.json()

    if "data" in data:
        return data["data"][0]  # latest tweet
    return None


def translate(text):
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Translate to natural Burmese. No extra text."},
            {"role": "user", "content": text}
        ]
    )
    return res.choices[0].message.content


def send_telegram(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": TG_CHAT,
        "text": text,
        "parse_mode": "HTML"
    })


def format_msg(en, mm):
    return f"""🇺🇸 Trump New Post

{en}

🇲🇲 Burmese:
{mm}
"""


def run():
    tweet = get_latest_tweet()
    if not tweet:
        return

    text = tweet["text"]
    mm = translate(text)

    msg = format_msg(text, mm)
    send_telegram(msg)


if __name__ == "__main__":
    run()
