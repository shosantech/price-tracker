import numpy as np

# -----------------------------
# TECHNICAL SIGNAL
# -----------------------------
def generate_technical_signal(price_df, volume_flag, price_period=60):
    """
    Generate BUY / SELL / HOLD signal based on technical indicators:
    - Trend (MA20 vs MA50)
    - RSI
    - Price vs N-day range (default 60)
    - Volume spike
    Returns: signal, weighted_score, confidence (0-1)
    """

    # ----- Trend -----
    ma20 = price_df["MA_20"].iloc[-1]
    ma50 = price_df["MA_50"].iloc[-1]
    trend = 1 if ma20 > ma50 else -1 if ma20 < ma50 else 0

    # ----- RSI -----
    rsi = price_df["RSI"].iloc[-1]
    rsi_score = 1 if rsi < 40 else -1 if rsi > 70 else 0

    # ----- Price Structure -----
    close = price_df["Close"].iloc[-1]
    recent_min = price_df["Close"].rolling(price_period).min().iloc[-1]
    recent_max = price_df["Close"].rolling(price_period).max().iloc[-1]
    price_score = 1 if close <= recent_min * 1.05 else -1 if close >= recent_max * 0.97 else 0

    # ----- Volume Spike -----
    volume_score = 1 if volume_flag else 0

    # ----- Weighted Score -----
    weights = {"trend": 0.35, "rsi": 0.20, "price": 0.25, "volume": 0.10}
    weighted_score = (
        trend*weights["trend"] +
        rsi_score*weights["rsi"] +
        price_score*weights["price"] +
        volume_score*weights["volume"]
    )

    # ----- Signal -----
    if weighted_score >= 0.6:
        signal = "BUY"
    elif weighted_score <= -0.6:
        signal = "SELL"
    else:
        signal = "HOLD"

    # ----- Confidence -----
    max_possible = sum(weights.values())  # max absolute weighted sum
    confidence = round(abs(weighted_score) / max_possible * 100, 1)  # percent

    return signal, weighted_score, confidence


# -----------------------------
# SENTIMENT SIGNAL
# -----------------------------
def generate_sentiment_signal(sentiment_list):
    avg_sentiment = np.mean([a["sentiment"] for a in sentiment_list])
    if avg_sentiment < -0.15:
        signal = "BUY"
    elif avg_sentiment > 0.15:
        signal = "SELL"
    else:
        signal = "HOLD"

    # Confidence as magnitude of sentiment
    confidence = round(min(abs(avg_sentiment)*100, 100),1)
    return signal, avg_sentiment, confidence


# -----------------------------
# COMBINED SIGNAL
# -----------------------------
def generate_combined_signal(price_df, sentiment_list, volume_flag, price_period=60):
    tech_signal, tech_score, tech_conf = generate_technical_signal(price_df, volume_flag, price_period)
    sent_signal, sent_score, sent_conf = generate_sentiment_signal(sentiment_list)

    # Weighted fusion: technical weight=2, sentiment weight=1
    combined_score = (tech_score*2) + (1 if sent_signal=="BUY" else -1 if sent_signal=="SELL" else 0)
    if combined_score >= 2:
        combined_signal = "BUY"
    elif combined_score <= -2:
        combined_signal = "SELL"
    else:
        combined_signal = "HOLD"

    # Combined confidence normalized
    max_possible = 2 + 1  # weights sum
    combined_confidence = round(abs(combined_score)/max_possible*100,1)

    return combined_signal, combined_score, combined_confidence
