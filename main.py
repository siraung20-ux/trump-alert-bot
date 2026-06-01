import tweepy
import telebot
import openai
import time
import os

# --- Configuration (Secrets/Environment Variables မှ ဆွဲယူခြင်း) ---
X_BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")
X_API_KEY = os.getenv("X_API_KEY")
X_API_SECRET = os.getenv("X_API_SECRET")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
X_ACCESS_SECRET = os.getenv("X_ACCESS_SECRET")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Target User (Donald Trump)
TARGET_USERNAME = "realDonaldTrump"

# Initialize Clients
client = tweepy.Client(
    bearer_token=X_BEARER_TOKEN,
    consumer_key=X_API_KEY,
    consumer_secret=X_API_SECRET,
    access_token=X_ACCESS_TOKEN,
    access_token_secret=X_ACCESS_SECRET
)

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
openai.api_key = OPENAI_API_KEY

def get_user_id(username):
    user = client.get_user(username=username)
    return user.data.id

def get_latest_tweets(user_id, since_id=None):
    try:
        tweets = client.get_users_tweets(
            id=user_id, 
            since_id=since_id, 
            max_results=5,
            tweet_fields=['created_at', 'text']
        )
        return tweets.data
    except Exception as e:
        print(f"Error fetching tweets: {e}")
        return None

def summarize_tweet(text):
    try:
        from openai import OpenAI
        client_ai = OpenAI(api_key=OPENAI_API_KEY)
        response = client_ai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes tweets professionally in a concise way."},
                {"role": "user", "content": f"Summarize this tweet and provide key takeaways: {text}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error summarizing: {e}")
        return "Summary not available."

def main():
    print(f"Bot started and monitoring @{TARGET_USERNAME} using Secrets...")
    
    try:
        user_id = get_user_id(TARGET_USERNAME)
    except Exception as e:
        print(f"Could not find user or API error: {e}")
        return

    last_tweet_id = None
    if os.path.exists("last_id.txt"):
        with open("last_id.txt", "r") as f:
            last_tweet_id = f.read().strip()

    while True:
        try:
            tweets = get_latest_tweets(user_id, since_id=last_tweet_id)
            if tweets:
                for tweet in reversed(tweets):
                    print(f"New tweet found: {tweet.id}")
                    summary = summarize_tweet(tweet.text)
                    
                    message = f"🔔 *New Post from @{TARGET_USERNAME}*\n\n"
                    message += f"{tweet.text}\n\n"
                    message += f"📝 *AI Summary:*\n{summary}\n\n"
                    message += f"🔗 [View on X](https://twitter.com/{TARGET_USERNAME}/status/{tweet.id})"
                    
                    bot.send_message(TELEGRAM_CHANNEL_ID, message, parse_mode="Markdown")
                    
                    last_tweet_id = tweet.id
                    with open("last_id.txt", "w") as f:
                        f.write(str(last_tweet_id))
            
            time.sleep(300)
        except Exception as e:
            print(f"Loop Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
    
