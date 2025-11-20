# reddit_collector.py
import praw
import requests
import json
import time
from datetime import datetime
from config import *

reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    user_agent=USER_AGENT
)

def fetch_posts(subreddit_name, limit=20):
    try:
        subreddit = reddit.subreddit(subreddit_name)
        posts_data = []
        for post in subreddit.new(limit=limit):
            posts_data.append({
                "post_id": post.id,
                "title": post.title[:300],  # limit text size
                "text": (post.selftext or "")[:1000],
                "author": str(post.author),
                "score": post.score,
                "num_comments": post.num_comments,
                "url": post.url,
                "created_utc": datetime.utcfromtimestamp(post.created_utc).strftime("%Y-%m-%d %H:%M:%S"),
                "subreddit": subreddit_name
            })
        print(f"✅ Fetched {len(posts_data)} posts from r/{subreddit_name}")
        return posts_data
    except Exception as e:
        print("❌ Error fetching Reddit posts:", e)
        return []

def save_to_json(data, filename='reddit_data.json'):
    try:
        with open(filename, 'a', encoding='utf-8') as f:
            for record in data:
                json.dump(record, f)
                f.write('\n')
        print(f'💾 Saved {len(data)} posts locally to {filename}')
    except Exception as e:
        print('❌ Error saving data locally:', e)

def send_to_db(json_data):
    try:
        response = requests.post(API_ENDPOINT, json=json_data, timeout=10)
        if response.status_code == 200:
            print(f'📤 Sent {len(json_data)} posts to DB | ✅ Success')
        else:
            print(f'⚠ Server responded with {response.status_code}: {response.text[:120]}')
    except Exception as e:
        print('❌ Error sending data to DB:', e)

def main():
    print('\n🌊 Reddit Data Collector')
    print(f'Collecting from: r/{SUBREDDIT}')
    print(f'Sending to API: {API_ENDPOINT}')
    print(f'Fetching every {FETCH_INTERVAL} seconds...\n')

    while True:
        posts = fetch_posts(SUBREDDIT, FETCH_LIMIT)
        if posts:
            if SAVE_LOCAL:
                save_to_json(posts)
            send_to_db(posts)
        else:
            print('⚠ No new posts this round.')
        time.sleep(FETCH_INTERVAL)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n🛑 Collector stopped by user.')
