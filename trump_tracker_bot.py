import tweepy
import telebot
from openai import OpenAI
import os

# GitHub Secrets မှ Variable များယူခြင်း
X_BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

TARGET_USERNAME = "realDonaldTrump"

def get_user_id(client, username):
    user = client.get_user(username=username)
    return user.data.id

def summarize_tweet(text):
    try:
        client_ai = OpenAI(api_key=OPENAI_API_KEY)
        response = client_ai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes tweets professionally in a concise way."},
                {"role": "user", "content": f"Summarize this tweet and provide key takeaways: {text}"}
            ]
        )
        return response.choices[0].message.content
    except:
        return "Summary not available."

def main():
    client = tweepy.Client(bearer_token=X_BEARER_TOKEN)
    bot = telebot.TeleBot(BOT_TOKEN)
    
    try:
        user_id = get_user_id(client, TARGET_USERNAME)
        
        # ပို့ပြီးသား ID ကို ဖတ်ခြင်း
        last_id = None
        if os.path.exists("last_id.txt"):
            with open("last_id.txt", "r") as f:
                last_id = f.read().strip()

        # Post အသစ်များ ဆွဲယူခြင်း
        tweets = client.get_users_tweets(
            id=user_id, 
            since_id=last_id, 
            max_results=5, 
            tweet_fields=['created_at', 'text']
        )

        if tweets.data:
            for tweet in reversed(tweets.data):
                summary = summarize_tweet(tweet.text)
                message = f"🔔 *New Post from @{TARGET_USERNAME}*\n\n{tweet.text}\n\n📝 *AI Summary:*\n{summary}\n\n🔗 [View on X](https://twitter.com/{TARGET_USERNAME}/status/{tweet.id})"
                bot.send_message(CHANNEL_ID, message, parse_mode="Markdown")
                
                # ID အသစ်ကို သိမ်းခြင်း
                with open("last_id.txt", "w") as f:
                    f.write(str(tweet.id))
            print("Successfully sent new updates.")
        else:
            print("No new tweets found.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()

