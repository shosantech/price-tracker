import sqlite3
from config.settings import DB_PATH

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS gold_prices (
        date TEXT PRIMARY KEY,
        close REAL,
        volume REAL,
        ma20 REAL,
        ma50 REAL,
        rsi REAL
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        source TEXT,
        publishedAt TEXT,
        sentiment REAL
    )""")

    c.execute("""
CREATE TABLE IF NOT EXISTS news_volume (
    week_start TEXT PRIMARY KEY,
    total_articles INTEGER,
    average_sentiment REAL
)
""")

    conn.commit()
    conn.close()

def save_gold_price(data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO gold_prices (date, close, volume, ma20, ma50, rsi)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (data['date'], data['close'], data['volume'], data['ma20'], data['ma50'], data['rsi']))
    conn.commit()
    conn.close()

def save_news(data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO news (title, source, publishedAt, sentiment)
        VALUES (?, ?, ?, ?)
    """, (data['title'], data['source'], data['publishedAt'], data['sentiment']))
    conn.commit()
    conn.close()

def save_news_volume(week_start, total_articles, average_sentiment):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO news_volume (week_start, total_articles, average_sentiment)
        VALUES (?, ?, ?)
    """, (week_start, total_articles, average_sentiment))
    conn.commit()
    conn.close()

def load_past_volumes():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT week_start, total_articles, average_sentiment FROM news_volume ORDER BY week_start DESC")
    rows = c.fetchall()

    conn.close()

    # Return list of (week_start, count)
    return rows

# In database/db.py

def load_past_avg_sentiments():
    """
    Returns a list of past weekly average sentiments from the database.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT average_sentiment FROM news_volume ORDER BY week_start ASC")
    rows = cursor.fetchall()
    conn.close()

    # Each row is a tuple (avg_sentiment,), so extract the float
    return [row[0] for row in rows]

