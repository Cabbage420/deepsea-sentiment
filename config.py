# config.py

# ================= Reddit API Credentials =================
CLIENT_ID = "l6bce9aekIy-uwgo7-i-pg"
CLIENT_SECRET = "JjcjuZBjeE6G-IeV66zS2Dl5R5_4eA"
USER_AGENT = "DBMS_Project:v1.0 (by u/ClassroomUnlucky981)"

# ================= Flask API Endpoint =================
# This must match your Flask app’s /ingest route in main.py
API_ENDPOINT = "http://127.0.0.1:81/ingest"

# ================= Reddit Fetch Settings =================
SUBREDDIT = "technology"   # change as needed
FETCH_LIMIT = 20           # Number of posts per batch
FETCH_INTERVAL = 60        # Time (seconds) between fetch cycles
SAVE_LOCAL = True          # Save JSON backup locally (for safety)

# ================= Notes =================
# - This collector sends data to your local Flask app on port 81.
# - SQLite (appdata.db) is automatically managed by Flask (no MySQL needed).
# - Make sure Flask is running before executing reddit_collector.py.
