import numpy as np

def generate_signal(price_df, sentiment_list, volume_flag):
    """
    Generate BUY / SELL / HOLD signal for gold using:
    - Trend (MA20 vs MA50)
    - RSI
    - Price position vs 30-day range
    - Sentiment (inverted for gold)
    - Volume trend flag
    """

    # ---------------------------
    # 1. Sentiment score (GOLD LOGIC)
    # ---------------------------
    avg_sentiment = np.mean([a["sentiment"] for a in sentiment_list])

    # Gold rises when fear rises → negative sentiment is bullish
    if avg_sentiment < -0.15:
        sentiment_score = +1
    elif avg_sentiment > 0.15:
        sentiment_score = -1
    else:
        sentiment_score = 0


    # ---------------------------
    # 2. Trend score (most important)
    # ---------------------------
    ma20 = price_df["MA_20"].iloc[-1]
    ma50 = price_df["MA_50"].iloc[-1]

    if ma20 > ma50:
        trend_score = 2     # strong uptrend
    elif ma20 < ma50:
        trend_score = -2    # strong downtrend
    else:
        trend_score = 0


    # ---------------------------
    # 3. RSI score (overbought/oversold)
    # ---------------------------
    rsi = price_df["RSI"].iloc[-1]

    if rsi < 40:
        rsi_score = +1      # healthy discounted buy zone
    elif rsi > 70:
        rsi_score = -1      # overbought sell zone
    else:
        rsi_score = 0


    # ---------------------------
    # 4. Price context (support/resistance)
    # ---------------------------
    close = price_df["Close"].iloc[-1]
    recent_min = price_df["Close"].rolling(30).min().iloc[-1]
    recent_max = price_df["Close"].rolling(30).max().iloc[-1]

    if close <= recent_min * 1.05:
        price_score = +1    # near support → buy area
    elif close >= recent_max * 0.97:
        price_score = -1    # near resistance → sell area
    else:
        price_score = 0


    # ---------------------------
    # 5. Volume trend
    # ---------------------------
    # volume_flag = True if volume spike exists
    if volume_flag:
        volume_score = +1
    else:
        volume_score = 0


    # ---------------------------
    # FINAL AGGREGATED SCORE
    # ---------------------------
    final_score = (
        trend_score +
        rsi_score +
        price_score +
        sentiment_score +
        volume_score
    )

    # ---------------------------
    # SIGNAL DECISION
    # ---------------------------
    if final_score >= 3:
        return "BUY"
    elif final_score <= -3:
        return "SELL"
    else:
        return "HOLD"
