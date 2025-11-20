from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import sqlite3, hashlib, os

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'supersecretkey'

DB_PATH = "appdata.db"
analyzer = SentimentIntensityAnalyzer()

# ---------------------- DB SETUP ----------------------
def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        # user table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        # sentiment table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS sentiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                text TEXT NOT NULL,
                sentiment TEXT NOT NULL,
                polarity REAL NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

init_db()

# ---------------------- UTILS ----------------------
def hash_pw(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def analyze_text(text):
    """Enhanced VADER analyzer with manual negation fix for short sentences."""
    scores = analyzer.polarity_scores(text)
    compound = scores['compound']

    # Manual override: if strong negation words appear
    text_lower = text.lower()
    if any(word in text_lower for word in ["no ", "not ", "never ", "n't "]) and "hate" in text_lower:
        return "Negative", -0.8

    if compound >= 0.05:
        sentiment = 'Positive'
    elif compound <= -0.05:
        sentiment = 'Negative'
    else:
        sentiment = 'Neutral'

    return sentiment, compound



# ---------------------- ROUTES ----------------------
@app.route('/')
def login_page():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def do_login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    hashed_pw = hash_pw(password)

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_pw))
    user = cur.fetchone()
    conn.close()

    if user:
        session['user'] = username
        return redirect(url_for('dashboard'))
    return render_template('login.html', error='Invalid credentials')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            return render_template('signup.html', error='Enter username and password')

        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hash_pw(password)))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return render_template('signup.html', error='Username already exists')

        conn.close()
        return redirect(url_for('login_page'))

    return render_template('signup.html')


@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login_page'))

    username = session['user']

    conn = get_db_connection()
    cur = conn.cursor()

    # Reddit admin sees all
    if username == "reddit":
        cur.execute("SELECT text, sentiment, polarity FROM sentiments WHERE username='reddit' ORDER BY id DESC LIMIT 10")
    else:
        cur.execute("SELECT text, sentiment, polarity FROM sentiments WHERE username=? ORDER BY id DESC LIMIT 10", (username,))
    history = cur.fetchall()

    chart_data = {'Positive': 0, 'Negative': 0, 'Neutral': 0}
    for _, sentiment, _ in history:
        chart_data[sentiment] += 1

    conn.close()
    return render_template('dashboard.html', chart_data=chart_data, history=history)


@app.route('/analyze', methods=['POST'])
def analyze():
    if 'user' not in session:
        return redirect(url_for('login_page'))

    text = request.form.get('text', '').strip()
    if not text:
        return redirect(url_for('dashboard'))

    sentiment, polarity = analyze_text(text)
    username = session['user']

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO sentiments (username, text, sentiment, polarity) VALUES (?, ?, ?, ?)",
                (username, text, sentiment, polarity))
    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))


@app.route('/api/summary')
def api_summary():
    if 'user' not in session:
        return jsonify({'Positive': 0, 'Negative': 0, 'Neutral': 0})

    username = session['user']
    conn = get_db_connection()
    cur = conn.cursor()

    if username == "reddit":
        cur.execute("SELECT sentiment FROM sentiments WHERE username='reddit'")
    else:
        cur.execute("SELECT sentiment FROM sentiments WHERE username=?", (username,))
    all_sents = [row[0] for row in cur.fetchall()]
    conn.close()

    summary = {'Positive': 0, 'Negative': 0, 'Neutral': 0}
    for s in all_sents:
        summary[s] += 1

    return jsonify(summary)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))


@app.route('/ingest', methods=['POST'])
def ingest():
    """Accept Reddit posts, analyze via VADER, and store."""
    data = request.get_json(force=True)
    if not data:
        return jsonify({'status': 'error', 'message': 'No data received'}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    count = 0

    for post in data:
        try:
            text = post.get('title', '')[:1000]
            if not text.strip():
                continue

            sentiment, polarity = analyze_text(text)

            cur.execute("""
                INSERT INTO sentiments (username, text, sentiment, polarity)
                VALUES (?, ?, ?, ?)
            """, ('reddit', text, sentiment, polarity))
            count += 1
        except Exception as e:
            print("Error inserting post:", e)
            continue

    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'inserted': count}), 200


# ---------------------- MAIN ----------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=81, debug=True)
