import tweepy
import time
import json

# Twitter API credentials
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET")
BEARER_TOKEN = os.getenv("BEARER_TOKEN")

# Account to monitor
TARGET_ACCOUNT = os.getenv("TARGET_ACCOUNT")

# File to store processed tweet IDs
PROCESSED_FILE = "processed_tweets.json"

def load_processed_tweets():
    """Load the list of already processed tweet IDs"""
    try:
        with open(PROCESSED_FILE, 'r') as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()

def save_processed_tweets(processed):
    """Save the list of processed tweet IDs"""
    with open(PROCESSED_FILE, 'w') as f:
        json.dump(list(processed), f)

def initialize_api():
    """Initialize Twitter API v2 client"""
    client = tweepy.Client(
        bearer_token=BEARER_TOKEN,
        consumer_key=API_KEY,
        consumer_secret=API_SECRET,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_TOKEN_SECRET,
        wait_on_rate_limit=True
    )
    return client

def get_user_id(client, username):
    """Get user ID from username"""
    try:
        user = client.get_user(username=username)
        return user.data.id
    except Exception as e:
        print(f"Error getting user ID: {e}")
        return None

def check_for_quote_tweets(client, user_id, processed_tweets):
    """Check for new quote tweets from the target account"""
    try:
        # Get recent tweets from the target user
        tweets = client.get_users_tweets(
            id=user_id,
            max_results=10,
            tweet_fields=['referenced_tweets', 'created_at'],
            expansions=['referenced_tweets.id']
        )
        
        if not tweets.data:
            print("No new tweets found")
            return []
        
        quote_tweets = []
        
        for tweet in tweets.data:
            # Skip if already processed
            if tweet.id in processed_tweets:
                continue
            
            # Check if this is a quote tweet
            if tweet.referenced_tweets:
                for ref in tweet.referenced_tweets:
                    if ref.type == "quoted":
                        quote_tweets.append({
                            'quote_tweet_id': tweet.id,
                            'original_tweet_id': ref.id
                        })
                        print(f"Found quote tweet! Quote ID: {tweet.id}, Original ID: {ref.id}")
        
        return quote_tweets
    
    except Exception as e:
        print(f"Error checking tweets: {e}")
        return []

def follow_user_if_not_following(client, user_id):
    """Follow a user if not already following"""
    try:
        # Check if already following
        client.follow_user(user_id)
        print(f"Successfully followed user ID: {user_id}")
        return True
    except tweepy.errors.Forbidden as e:
        print(f"Already following or can't follow: {e}")
        return False
    except Exception as e:
        print(f"Error following user: {e}")
        return False

def get_tweet_author(client, tweet_id):
    """Get the author user ID of a tweet"""
    try:
        tweet = client.get_tweet(tweet_id, expansions=['author_id'])
        if tweet.data and tweet.includes and 'users' in tweet.includes:
            return tweet.includes['users'][0].id
        return None
    except Exception as e:
        print(f"Error getting tweet author: {e}")
        return None

def retweet_original(client, original_tweet_id):
    """Retweet the original quoted tweet"""
    try:
        client.retweet(original_tweet_id)
        print(f"Successfully retweeted: {original_tweet_id}")
        return True
    except tweepy.errors.Forbidden as e:
        print(f"Already retweeted or can't retweet: {e}")
        return False
    except Exception as e:
        print(f"Error retweeting: {e}")
        return False

def main():
    """Main bot loop"""
    print("Starting Twitter Quote Retweet Bot...")
    
    # Initialize API
    client = initialize_api()
    
    # Get target user ID
    user_id = get_user_id(client, TARGET_ACCOUNT)
    if not user_id:
        print(f"Could not find user: {TARGET_ACCOUNT}")
        return
    
    print(f"Monitoring @{TARGET_ACCOUNT} (ID: {user_id})")
    
    # Load processed tweets
    processed_tweets = load_processed_tweets()
    print(f"Loaded {len(processed_tweets)} previously processed tweets")
    
    # Main loop
    while True:
        try:
            print(f"\nChecking for new quote tweets... ({time.strftime('%Y-%m-%d %H:%M:%S')})")
            
            # Check for new quote tweets
            quote_tweets = check_for_quote_tweets(client, user_id, processed_tweets)
            
            # Process each quote tweet
            for qt in quote_tweets:
                print(f"Processing quote tweet {qt['quote_tweet_id']}...")
                
                # Get the author of the original tweet
                author_id = get_tweet_author(client, qt['original_tweet_id'])
                
                if author_id:
                    # Follow the author if not already following
                    print(f"Checking follow status for author {author_id}...")
                    follow_user_if_not_following(client, author_id)
                    time.sleep(1)  # Small delay after follow
                
                # Retweet the original
                if retweet_original(client, qt['original_tweet_id']):
                    # Mark as processed
                    processed_tweets.add(qt['quote_tweet_id'])
                    save_processed_tweets(processed_tweets)
                    print("✓ Successfully processed and saved")
                else:
                    # Still mark as processed to avoid retrying
                    processed_tweets.add(qt['quote_tweet_id'])
                    save_processed_tweets(processed_tweets)
                
                # Small delay between retweets
                time.sleep(2)
            
            if not quote_tweets:
                print("No new quote tweets to process")
            
            # Wait before checking again (5 minutes)
            print(f"Waiting 5 minutes before next check...")
            time.sleep(300)
            
        except KeyboardInterrupt:
            print("\nBot stopped by user")
            break
        except Exception as e:
            print(f"Error in main loop: {e}")
            print("Waiting 5 minutes before retrying...")
            time.sleep(300)

if __name__ == "__main__":
    main()
