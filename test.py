import os
import requests

TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHANNEL_ID"]

msg = "✅ Trump Alert Bot Test Success!"

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

r = requests.post(
url,
json={
"chat_id": CHAT_ID,
"text": msg
}
)

print(r.text)
