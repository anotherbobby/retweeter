import os
import time
from datetime import datetime, timezone
from dotenv import load_dotenv
import tweepy

load_dotenv()

BEARER_TOKEN = os.getenv('BEARER_TOKEN')
API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
ACCESS_TOKEN_SECRET = os.getenv('ACCESS_TOKEN_SECRET')

if not all([BEARER_TOKEN, API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET]):
    raise ValueError("Missing Twitter API environment variables")

client = tweepy.Client(
    bearer_token=BEARER_TOKEN,
    consumer_key=API_KEY,
    consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_TOKEN_SECRET
)

start_date = datetime(2025, 12, 10, tzinfo=timezone.utc)
end_date = datetime(2026, 1, 10, tzinfo=timezone.utc)
current_time = datetime.now(timezone.utc)

if current_time > end_date:
    print("The retweet period has ended.")
    exit()

query = "#cashie"

# Retweet past tweets in the period
try:
    tweets = client.search_recent_tweets(
        query=query,
        start_time=start_date,
        end_time=min(current_time, end_date),
        max_results=100,
        tweet_fields=['created_at']
    )
    if tweets.data:
        for tweet in tweets.data:
            try:
                client.retweet(tweet.id)
                print(f"Retweeted past tweet: {tweet.id}")
            except tweepy.TweepyException as e:
                print(f"Failed to retweet {tweet.id}: {e}")
except tweepy.TweepyException as e:
    print(f"Error searching past tweets: {e}")

# Continuously retweet new tweets until end_date
last_checked = current_time
while datetime.now(timezone.utc) < end_date:
    time.sleep(900)  # Check every 15 minutes
    now = datetime.now(timezone.utc)
    try:
        tweets = client.search_recent_tweets(
            query=query,
            start_time=last_checked,
            end_time=now,
            max_results=100,
            tweet_fields=['created_at']
        )
        if tweets.data:
            for tweet in tweets.data:
                if start_date <= tweet.created_at <= end_date:
                    try:
                        client.retweet(tweet.id)
                        print(f"Retweeted new tweet: {tweet.id}")
                    except tweepy.TweepyException as e:
                        print(f"Failed to retweet {tweet.id}: {e}")
        last_checked = now
    except tweepy.TweepyException as e:
        print(f"Error searching new tweets: {e}")

print("Retweet period ended.")