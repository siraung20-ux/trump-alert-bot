import tweepy
import telebot
from openai import OpenAI
import os
import sys

# Secrets များယူခြင်း
X_BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

TARGET_USERNAME = "realDonaldTrump"

def main():
    print(f"--- Starting Bot Diagnostic ---")
    print(f"Target: @{TARGET_USERNAME}")
    
    # 1. Telegram Connection Check
    try:
        bot = telebot.TeleBot(BOT_TOKEN)
        print(f"✅ Telegram Bot Token is valid.")
    except Exception as e:
        print(f"❌ Telegram Init Error: {e}")
        return

    # 2. X API Connection Check
    try:
        client = tweepy.Client(bearer_token=X_BEARER_TOKEN)
        user = client.get_user(username=TARGET_USERNAME)
        user_id = user.data.id
        print(f"✅ X API Success. User ID for @{TARGET_USERNAME} is {user_id}")
    except Exception as e:
        print(f"❌ X API Error (Reading User): {e}")
        print("Note: If you are on X API 'Free' tier, you might not be able to read tweets.")
        return

    # 3. Fetch Tweets
    try:
        # ပထမဆုံးအကြိမ်မှာ အဟောင်းတွေပါ ဆွဲထုတ်ဖို့ since_id ကို ခေတ္တပိတ်ထားပါမယ်
        print("Fetching latest tweets...")
        tweets = client.get_users_tweets(
            id=user_id, 
            max_results=5, 
            tweet_fields=['created_at', 'text']
        )
        
        if not tweets.data:
            print("❓ No tweets found for this user.")
            return
            
        print(f"Found {len(tweets.data)} tweets.")

        for tweet in reversed(tweets.data):
            print(f"Processing Tweet ID: {tweet.id}")
            
            # OpenAI Summary (Optional check)
            summary = "AI Summary processing..."
            try:
                client_ai = OpenAI(api_key=OPENAI_API_KEY)
                response = client_ai.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": f"Summarize: {tweet.text}"}],
                    max_tokens=100
                )
                summary = response.choices[0].message.content
            except Exception as e:
                print(f"⚠️ OpenAI Error: {e}")
                summary = "Summary unavailable."

            # Telegram ပို့ခြင်း
            try:
                # CHANNEL_ID မှာ @ ပါမပါ စစ်ဆေးခြင်း
                target_chat = CHANNEL_ID
                if not str(target_chat).startswith(('@', '-')):
                    target_chat = f"@{target_chat}"
                
                message = f"🔔 *Post from @{TARGET_USERNAME}*\n\n{tweet.text}\n\n📝 *AI Summary:*\n{summary}\n\n🔗 [View on X](https://twitter.com/{TARGET_USERNAME}/status/{tweet.id})"
                bot.send_message(target_chat, message, parse_mode="Markdown")
                print(f"✅ Message sent to Telegram: {tweet.id}")
            except Exception as e:
                print(f"❌ Telegram Send Error: {e}")
                print(f"Current CHANNEL_ID value: {CHANNEL_ID}")

    except Exception as e:
        print(f"❌ General Error: {e}")

if __name__ == "__main__":
    main()
    
