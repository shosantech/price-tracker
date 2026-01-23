from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta

from fetchers.price_fetcher import fetch_gold_prices
from fetchers.news_fetcher import fetch_gold_news_past_week
# from fetchers.gdelt_fetcher import fetch_gold_news_gdelt
# from fetchers.alpha_news_fetcher import fetch_gold_news


from processors.technicals import compute_technicals, generate_technical
from processors.sentiment import compute_sentiment, generate_sentiment
from fusion import decision_engine
from fusion.combined_signal import generate_combined_signal

from database.db import (
    init_db,
    save_gold_price,
    save_news,
    save_news_volume,
    load_past_volumes,
    load_past_avg_sentiments,
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

    # Technical signal (60-day based)
    technical = generate_technical(price_df)
    
    technical_signal = technical["signal"]
    technical_confidence =technical["confidence"]


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
            "close": row["Close"],
            "volume": row["Volume"],
            "ma20": row["MA_20"],
            "ma50": row["MA_50"],
            "rsi": row["RSI"],
        })

    # --------------------------
    # 5. SAVE NEWS
    # --------------------------
    for article in sentiment_list:
        print("Saving article:", article)
        save_news(article)

    # --------------------------
    # 6. COMBINED SIGNAL
    # --------------------------
    combined_signal = generate_combined_signal(
    technical_signal,
    sentiment_signal
    )    
    # --------------------------
    # Combined confidence (weighted sum)
    # --------------------------

    combined_confidence = round(
        (technical_confidence * 0.7) + (sentiment_confidence * 0.3), 1
    )


    # 6️⃣ How confidence maps to behavior (recommended)
    # Confidence	Signal Meaning	Suggested Action
    # 85–100%	Strong alignment	Aggressive buy / add
    # 70–84%	Healthy trend	Buy / scale in
    # 55–69%	Mixed signals	Hold / small entries
    # 40–54%	Weak alignment	Wait
    # < 40%	Risky	Avoid / exit

    # So 70% BUY = lower-risk trend participation, not hype.


    # --------------------------
    # 7. API RESPONSE
    # --------------------------
    return jsonify({
        
    "week_start": week_start,
    "this_week_articles": int(this_week),
    "average_weekly_articles": float(avg_weekly),
    "volume_increase_percent": float(volume_increase),
    "news_volume_spike": bool(volume_flag),

    "technical": technical,
    "technical_confidence": technical["confidence"],
    "sentiment_signal": sentiment_signal,
    "combined_signal": combined_signal,
     "combined_confidence": combined_confidence,
    # "combined_score": combined_score,
    # "combined_confidence": combined_conf,

    "sentiment": sentiment_list,
})


## What Signal means:

## 1️⃣ Trend:     "Are we allowed to buy?"
## 2️⃣ Structure: "Is price favorable?"
## 3️⃣ RSI:       "Is momentum stretched?"
## 4️⃣ Volume:    "Is this move real?"

#Final clarity statement (lock this in)

##Trend decides direction
##Structure decides value
##RSI decides timing
##Volume decides confidence

##########

if __name__ == "__main__":
    print("🔥 Flask API running at http://127.0.0.1:5000")
    app.run(debug=True)
