import pandas as pd

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


# ----------------------------------------------------
# NEW TECHNICAL SIGNAL GENERATION (no sentiment)
# ----------------------------------------------------
def generate_technical_signal(df):
    """
    Creates a standalone BUY / HOLD / SELL based only on:
    - Trend (MA20 vs MA50)
    - RSI
    - Price relative to recent 30-day range
    """

    # latest row
    latest = df.iloc[-1]

    # ----- Trend -----
    ma20 = latest["MA_20"]
    ma50 = latest["MA_50"]

    if ma20 > ma50:
        trend_score = 2      # strong uptrend
    elif ma20 < ma50:
        trend_score = -2     # strong downtrend
    else:
        trend_score = 0

    # ----- RSI -----
    rsi = latest["RSI"]
    if rsi < 40:
        rsi_score = +1
    elif rsi > 70:
        rsi_score = -1
    else:
        rsi_score = 0

    # ----- Price Context (support/resistance) -----
    close = latest["Close"]
    recent_min = df["Close"].rolling(30).min().iloc[-1]
    recent_max = df["Close"].rolling(30).max().iloc[-1]

    if close <= recent_min * 1.05:
        price_score = +1
    elif close >= recent_max * 0.97:
        price_score = -1
    else:
        price_score = 0

    # ----- Final Technical Score -----
    final_score = trend_score + rsi_score + price_score

    if final_score >= 2:
        return "BUY"
    elif final_score <= -2:
        return "SELL"
    else:
        return "HOLD"

