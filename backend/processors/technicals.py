import pandas as pd

# -----------------------------
# INDICATORS
# -----------------------------
def compute_technicals(df):
    df['MA_20'] = df['Close'].rolling(window=20).mean()
    df['MA_50'] = df['Close'].rolling(window=50).mean()
    df['RSI'] = compute_rsi(df['Close'], 14)
    return df


def compute_rsi(series, window=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


# -----------------------------
# PRICE STRUCTURE FLAGS
# -----------------------------
def price_structure_flag(df, window):
    """
    Returns:
    +1  → near support (buy zone)
    -1  → near resistance (sell zone)
     0  → neutral
    """
    close = df["Close"].iloc[-1]
    low = df["Close"].rolling(window).min().iloc[-1]
    high = df["Close"].rolling(window).max().iloc[-1]

    if close <= low * 1.05:
        return 1
    elif close >= high * 0.97:
        return -1
    else:
        return 0


# -----------------------------
# TECHNICAL SIGNAL (60D ONLY)
# -----------------------------
# -----------------------------
# TECHNICAL SIGNAL (60D ONLY) WITH CONFIDENCE
# -----------------------------
def generate_technical(df, volume_flag=False):
    """
    Medium/long-term gold technical signal.
    Uses ONLY 60-day price structure for decision.
    Includes weighted confidence score based on components.
    """

    latest = df.iloc[-1]

    # -------- Trend (direction) --------
    if latest["MA_20"] > latest["MA_50"]:
        trend_score = 1
    elif latest["MA_20"] < latest["MA_50"]:
        trend_score = -1
    else:
        trend_score = 0

    # -------- RSI (timing) --------
    if latest["RSI"] < 40:
        rsi_score = 1
    elif latest["RSI"] > 70:
        rsi_score = -1
    else:
        rsi_score = 0

    # -------- Price Structure --------
    structure_15 = price_structure_flag(df, 15)
    structure_30 = price_structure_flag(df, 30)

    structure_45 = price_structure_flag(df, 45)
    structure_60 = price_structure_flag(df, 60)
    structure_90 = price_structure_flag(df, 90)
    price_score = structure_30  # for 60-day signal

    # -------- Volume --------
    volume_score = 1 if volume_flag else 0

    # -------- FINAL SIGNAL (60D only) --------
    final_score = trend_score + rsi_score + price_score + volume_score
    if final_score >= 2:
        signal = "BUY"
    elif final_score <= -2:
        signal = "SELL"
    else:
        signal = "HOLD"

    # -------- TECHNICAL CONFIDENCE --------
    weights = {"trend": 0.35, "rsi": 0.20, "price": 0.25, "volume": 0.10}
    weighted_sum = (
        abs(trend_score * weights["trend"]) +
        abs(rsi_score * weights["rsi"]) +
        abs(price_score * weights["price"]) +
        abs(volume_score * weights["volume"])
    )
    max_weighted = sum(weights.values())
    technical_confidence = round((weighted_sum / max_weighted) * 100, 1)

    return {
        "signal": signal,
        "score": final_score,
        "confidence": technical_confidence,
        "components": {
            "trend": trend_score,
            "rsi": rsi_score,
            "price_structure_15": structure_15,
            "price_structure_30": structure_30,
            "price_structure_45": structure_45,
            "price_structure_60": structure_60,
            "price_structure_90": structure_90,
            "volume": volume_score
        }
    }
