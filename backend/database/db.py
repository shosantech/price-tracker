import sqlite3
from config.settings import DB_PATH

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS gold_prices (
            date TEXT PRIMARY KEY,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL,
            ma10 REAL,
            ma20 REAL,
            ma50 REAL,
            ma200 REAL,
            ema10 REAL,
            rsi REAL,
            atr REAL
        )
        """)


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
    
    c.execute("""CREATE TABLE IF NOT EXISTS signal_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    price REAL,
    technical_signal TEXT,
    technical_confidence REAL,
    sentiment_signal TEXT,
    sentiment_confidence REAL,
    combined_signal TEXT,
    combined_confidence REAL,
    regime TEXT,
    explanation TEXT
    );""")


    conn.commit()
    conn.close()

def save_gold_price(data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        INSERT OR REPLACE INTO gold_prices (
            date, open, high, low, close, volume,
            ma10, ma20, ma50, ma200, ema10, rsi, atr
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["date"],
        data["open"],
        data["high"],
        data["low"],
        data["close"],
        data["volume"],
        data.get("ma10"),
        data.get("ma20"),
        data.get("ma50"),
        data.get("ma200"),
        data.get("ema10"),
        data.get("rsi"),
        data.get("atr"),
    ))

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


# In database/db.py

def save_signal(data):
    """
    Save a combined signal entry into the signal_history table.
    Expects a dict with keys:
    - date, price, technical_signal, technical_confidence,
      sentiment_signal, sentiment_confidence, combined_signal,
      combined_confidence, regime, explanation
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        INSERT INTO signal_history (
            date, price,
            technical_signal, technical_confidence,
            sentiment_signal, sentiment_confidence,
            combined_signal, combined_confidence,
            regime, explanation
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("date"),
        data.get("price"),
        data.get("technical_signal"),
        data.get("technical_confidence"),
        data.get("sentiment_signal"),
        data.get("sentiment_confidence"),
        data.get("combined_signal"),
        data.get("combined_confidence"),
        data.get("regime"),
        data.get("explanation")
    ))

    conn.commit()
    conn.close()

