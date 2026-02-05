from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta

from fetchers.price_fetcher import fetch_gold_prices
from fetchers.news_fetcher import fetch_gold_news_past_week

from processors.technicals import compute_technicals, generate_technical
from processors.sentiment import compute_sentiment, generate_sentiment
from fusion.combined_signal import generate_combined_signal


from database.db import (
    init_db,
    save_gold_price,
    save_news,
    save_news_volume,
    load_past_volumes,
    load_past_avg_sentiments,
    save_signal
)

app = Flask(__name__)
CORS(app)
init_db()


@app.route("/analyze", methods=["GET"])
def analyze():
    # --------------------------
    # 1. FETCH + PROCESS PRICES
    # --------------------------
    price_df = fetch_gold_prices(period="1y", interval="1d")
    price_df = compute_technicals(price_df)

    # Technical signal (weekly gold-focused)
    technical = generate_technical(price_df)
    print("this is the technical signal,", technical)
    technical_signal = technical["signal"]
    technical_confidence = technical["confidence"]

    # --------------------------
    # 2. NEWS + SENTIMENT
    # --------------------------
    articles = fetch_gold_news_past_week()
    past_volumes = load_past_volumes()
    past_avg_sentiments = load_past_avg_sentiments()

    (
        sentiment_list,
        volume_flag,
        this_week,
        avg_weekly,
        volume_increase,
        avg_sentiment,
        sentiment_std,
        past_avg_sentiments,
    ) = compute_sentiment(
        articles,
        past_volumes,
        past_avg_sentiments
    )

    sentiment_signal, _ = generate_sentiment(
        price_df,
        avg_sentiment,
        volume_flag,
        sentiment_std,
        past_avg_sentiments
    )
    sentiment_confidence = min(abs(avg_sentiment) * 100, 100)

    # --------------------------
    # 3. SAVE WEEKLY SENTIMENT
    # --------------------------
    week_start = (
        datetime.utcnow() - timedelta(days=datetime.utcnow().weekday())
    ).strftime("%Y-%m-%d")

    save_news_volume(week_start, this_week, avg_sentiment)

    # --------------------------
    # 4. SAVE PRICE HISTORY
    # --------------------------
    for _, row in price_df.iterrows():
        save_gold_price({
            "date": row["Date"].strftime("%Y-%m-%d"),
            "open": row["Open"],
            "high": row["High"],
            "low": row["Low"],
            "close": row["Close"],
            "volume": row["Volume"],
            "ma10": row.get("MA_10"),
            "ma20": row.get("MA_20"),
            "ma50": row.get("MA_50"),
            "ma200": row.get("MA_200"),
            "ema10": row.get("EMA_10"),
            "rsi": row.get("RSI"),
            "atr": row.get("ATR_14"),
        })

    # --------------------------
    # 5. SAVE NEWS
    # --------------------------
    for article in sentiment_list:
        save_news(article)

    # --------------------------
    # 6. COMBINED SIGNAL
    # --------------------------
    combined_signal = generate_combined_signal(
        technical,
        sentiment_signal,
        avg_sentiment
    )

    # --------------------------
    # 7. COMBINED CONFIDENCE
    # --------------------------
    # Weighted sum: 70% technical, 30% sentiment
    combined_confidence = round(
        (technical_confidence * 0.7) + (sentiment_confidence * 0.3),
        1
    )

     # --------------------------
    # 8. SAVE SIGNAL HISTORY
    # --------------------------
    

    save_signal({
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "price": price_df["Close"].iloc[-1],
        "technical_signal": technical_signal,
        "technical_confidence": technical_confidence,
        "sentiment_signal": sentiment_signal,
        "sentiment_confidence": sentiment_confidence,
        "combined_signal": combined_signal["signal"],
        "combined_confidence": combined_confidence,
        "regime": combined_signal["regime"],
        "explanation": combined_signal["explanation"]
    })

    # --------------------------
    # 9. API RESPONSE
    # --------------------------
    return jsonify({
        "week_start": week_start,
        "this_week_articles": int(this_week),
        "average_weekly_articles": float(avg_weekly),
        "volume_increase_percent": float(volume_increase),
        "news_volume_spike": bool(volume_flag),

        "technical": technical,
        "technical_signal": technical_signal,
        "technical_confidence": technical_confidence,

        "sentiment_signal": sentiment_signal,
        "sentiment_confidence": sentiment_confidence,

        "combined_signal": combined_signal,
        "combined_confidence": combined_confidence,

        "sentiment_articles": sentiment_list
    })


if __name__ == "__main__":
    print("🔥 Flask API running at http://127.0.0.1:5000")
    app.run(debug=True)
