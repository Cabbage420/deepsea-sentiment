import sqlite3

conn = sqlite3.connect("reddit_data.db")
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS reddit_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    comment TEXT,
    sentiment TEXT,
    polarity REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

conn.commit()
conn.close()
print("Database initialized ✅")
