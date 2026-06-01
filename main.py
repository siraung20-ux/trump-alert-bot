import os
import feedparser
import requests
from openai import OpenAI

RSS_URL = "https://trumpstruth.org/feed"

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)

LAST_FILE = "last_post.txt"

def get_last_id():
if os.path.exists(LAST_FILE):
with open(LAST_FILE, "r") as f:
return f.read().strip()
return ""

def save_last_id(post_id):
with open(LAST_FILE, "w") as f:
f.write(post_id)

def translate_burmese(text):
try:
response = client.chat.completions.create(
model="gpt-4o-mini",
messages=[
{
"role": "system",
"content": """
You are a professional Burmese translator.

Rules:

- Translate naturally into Burmese.

- Keep names unchanged.

- Keep political meaning unchanged.

- Return Burmese translation only.
  """
  },
  {
  "role": "user",
  "content": text
  }
  ]
  )
  
    return response.choices[0].message.content.strip()
  
  except Exception as e:
  print(e)
  return "ဘာသာပြန်မရပါ။"

def send_telegram(message):
requests.post(
f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
json={
"chat_id": CHANNEL_ID,
"text": message
}
)

feed = feedparser.parse(RSS_URL)

if not feed.entries:
raise Exception("RSS Feed Empty")

latest = feed.entries[0]

post_id = latest.id
text = latest.title
link = latest.link

last_id = get_last_id()

if post_id != last_id:

mm = translate_burmese(text)

message = f"""🚨 TRUMP TRUTH UPDATE

🇺🇸 English:
{text}

🇲🇲 မြန်မာ:
{mm}

🔗 Source:
{link}
"""

send_telegram(message)

save_last_id(post_id)

print("New Post Sent")

else:
print("No New Post")
