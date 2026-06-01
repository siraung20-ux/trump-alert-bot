import os
import tweepy
import telebot
from openai import OpenAI

def test_connections():
    print("--- Starting API Connection Test ---")
    # Telegram Test
    try:
        bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))
        me = bot.get_me()
        print(f"✅ Telegram Bot: Success (Bot Name: {me.first_name})")
    except Exception as e:
        print(f"❌ Telegram Bot: Failed - {e}")

    # X Test
    try:
        client = tweepy.Client(bearer_token=os.getenv("X_BEARER_TOKEN"))
        user = client.get_user(username="realDonaldTrump")
        print(f"✅ X API: Success (Found User ID: {user.data.id})")
    except Exception as e:
        print(f"❌ X API: Failed - {e}")

    # OpenAI Test
    try:
        client_ai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client_ai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        print("✅ OpenAI API: Success")
    except Exception as e:
        print(f"❌ OpenAI API: Failed - {e}")

if __name__ == "__main__":
    test_connections()

