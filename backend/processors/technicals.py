import pandas as pd
import numpy as np
from processors.patterns import detect_candlestick_patterns

# -----------------------------
# INDICATORS
# -----------------------------
def compute_technicals(df):
    """
    Compute key weekly technical indicators for gold:
    - Moving Averages (short, medium, long)
    - EMA short-term
    - RSI (momentum)
    - ATR / volatility
    """
    # Moving Averages
    df['MA_10'] = df['Close'].rolling(window=10).mean()
    df['MA_20'] = df['Close'].rolling(window=20).mean()
    df['MA_50'] = df['Close'].rolling(window=50).mean()
    df['MA_200'] = df['Close'].rolling(window=200).mean()
    df['EMA_10'] = df['Close'].ewm(span=10, adjust=False).mean()

    # RSI (momentum)
    df['RSI'] = compute_rsi(df['Close'], 14)

    # ATR-like volatility (rolling std)
    df['ATR_14'] = df['Close'].rolling(14).std()

    return df


def compute_rsi(series, window=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window).mean()
    rs = gain / (loss + 1e-6)
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
# RSI MULTI-LEVEL SIGNAL
# -----------------------------
def rsi_signal(rsi):
    if rsi < 30:
        return 2
    elif rsi < 40:
        return 1
    elif rsi > 70:
        return -2
    elif rsi > 60:
        return -1
    return 0


# -----------------------------
# TECHNICAL SIGNAL GENERATOR
# -----------------------------
def generate_technical(df, volume_flag=False):
    """
    Generate a weekly gold trade signal using:
    - Multi-length trend (MA10/20/50/200)
    - RSI (momentum)
    - Price structure (multi-window support/resistance)
    - Volatility dampening
    - Optional volume confirmation
    Returns a dict with signal, final score, confidence, and components.
    """

    latest = df.iloc[-1]

    # -------- TREND COMPONENTS --------
    trend_short = 1 if latest['MA_10'] > latest['MA_50'] else -1 if latest['MA_10'] < latest['MA_50'] else 0
    trend_medium = 1 if latest['MA_20'] > latest['MA_50'] else -1 if latest['MA_20'] < latest['MA_50'] else 0
    trend_long = 1 if latest['MA_50'] > latest['MA_200'] else -1 if latest['MA_50'] < latest['MA_200'] else 0
    trend_score = trend_short * 0.4 + trend_medium * 0.35 + trend_long * 0.25

    # -------- RSI COMPONENT --------
    rsi_score = rsi_signal(latest['RSI'])

    # -------- PRICE STRUCTURE --------
    structure_windows = [15, 30, 45, 60, 90]
    structure_weights = [0.1, 0.25, 0.3, 0.25, 0.1]
    price_score = sum(price_structure_flag(df, w) * structure_weights[i] for i, w in enumerate(structure_windows))
    structure_components = {f'price_structure_{w}': price_structure_flag(df, w) for w in structure_windows}

    # -------- VOLUME / CONFIRMATION --------
    volume_score = 1 if volume_flag else 0

    # -------- VOLATILITY DAMPENING --------
    atr = latest['ATR_14'] if not np.isnan(latest['ATR_14']) else 0
    volatility_factor = 1.0
    if atr > 0:
        # high volatility reduces confidence
        volatility_factor = max(0.5, min(1.0, 1.0 - (atr / latest['Close'])))

    # -------- FINAL SCORE --------
    final_score = (trend_score + rsi_score + price_score + volume_score) * volatility_factor

    # Gold asymmetry: fear > optimism
    if final_score < 0:
        final_score *= 1.1
    else:
        final_score *= 0.95

    # -------- DECISION --------
    if final_score >= 2.0:
        signal = "BUY"
    elif final_score <= -2.0:
        signal = "SELL"
    else:
        signal = "HOLD"

    # # ------- CANDLE PATTERNS --------
    # patterns = detect_candlestick_patterns(df)
    # pattern_score = sum(patterns.values())

    final_score = (trend_score + rsi_score + price_score + volume_score) * volatility_factor

    # -------- CONFIDENCE --------
    # Weighted sum of absolute component contributions
    weights = {"trend": 0.35, "rsi": 0.2, "price": 0.25, "volume": 0.1}
    weighted_sum = (
        abs(trend_score * weights["trend"]) +
        abs(rsi_score * weights["rsi"]) +
        abs(price_score * weights["price"]) +
        abs(volume_score * weights["volume"])
    )
    max_weighted = sum(weights.values()) * max(1, abs(final_score))  # scale with final_score
    technical_confidence = round(weighted_sum / max_weighted * 100 * volatility_factor, 1)
    

    return {
        "signal": signal,
        "score": round(final_score, 2),
        "confidence": technical_confidence,
        "components": {
            "trend_short": trend_short,
            "trend_medium": trend_medium,
            "trend_long": trend_long,
            "rsi": rsi_score,
            **structure_components,
            "volume": volume_score,
            "volatility_factor": round(volatility_factor, 3),
        }
    }
