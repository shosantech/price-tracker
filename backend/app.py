from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta

from fetchers.price_fetcher import fetch_gold_prices
from fetchers.news_fetcher import fetch_gold_news_past_week
from processors.technicals import compute_technicals
from processors.sentiment import compute_sentiment
from processors.sentiment import generate_sentiment
from fusion.decision_engine import generate_signal
from database.db import (
    init_db,
    save_gold_price,
    save_news,
    save_news_volume,
    load_past_volumes,
    load_past_avg_sentiments,
)

app = Flask(__name__)
CORS(app)  # Allow Electron app calls

init_db()


@app.route("/analyze", methods=["GET"])
def analyze():
    # Fetch gold prices
    price_df = fetch_gold_prices(period="1y", interval="1d")
    price_df = compute_technicals(price_df)

    # Fetch news
    articles, total_results = fetch_gold_news_past_week()

    # Load weekly volume history from DB
    past_volumes = load_past_volumes()
    past_avg_sentiments = load_past_avg_sentiments()  # load historical avg_sentiment from DB

    # Compute sentiment + volume spike
    sentiment_list, volume_flag, this_week, avg_weekly, volume_increase, past_avg_sentiments = compute_sentiment(
        articles, past_volumes, past_avg_sentiments
    )

    # Generate sentiment signal using historical avg_sentiment
    sentiment_signal, avg_sentiment = generate_sentiment(price_df, sentiment_list, volume_flag, past_avg_sentiments)

    # Save current week's avg_sentiment to DB
    week_start = (datetime.utcnow() - timedelta(days=datetime.utcnow().weekday())).strftime("%Y-%m-%d")
    save_news_volume(week_start, this_week, avg_sentiment)


    # Save gold price rows
    for _, row in price_df.iterrows():
        save_gold_price({
            "date": row["Date"].strftime("%Y-%m-%d"),
            "close": row["Close"],
            "volume": row["Volume"],
            "ma20": row.get("MA_20"),
            "ma50": row.get("MA_50"),
            "rsi": row.get("RSI")
        })

    # Save news to DB
    for article in sentiment_list:
        save_news(article)

    

    # Return structured JSON API result
    return jsonify({
    "week_start": week_start,
    "this_week_articles": int(this_week),
    "average_weekly_articles": float(avg_weekly),
    "volume_increase_percent": float(volume_increase),
    "volume_spike": bool(volume_flag),
    "sentiment_signal": sentiment_signal,
    "sentiment": sentiment_list,
})


if __name__ == "__main__":
    print("🔥 Flask API running at http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
