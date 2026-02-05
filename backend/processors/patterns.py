def detect_candlestick_patterns(df):
    """
    Detects key reversal / continuation patterns.
    Returns dict of pattern signals.
    """
    latest = df.iloc[-1]
    prev = df.iloc[-2]

    patterns = {}

    body = abs(latest["Close"] - latest["Open"])
    range_ = latest["High"] - latest["Low"]

    # ---------- ENGULFING ----------
    if (
        latest["Close"] > latest["Open"] and
        prev["Close"] < prev["Open"] and
        latest["Close"] > prev["Open"] and
        latest["Open"] < prev["Close"]
    ):
        patterns["bullish_engulfing"] = 1

    elif (
        latest["Close"] < latest["Open"] and
        prev["Close"] > prev["Open"] and
        latest["Open"] > prev["Close"] and
        latest["Close"] < prev["Open"]
    ):
        patterns["bearish_engulfing"] = -1

    # ---------- PIN BAR ----------
    upper_wick = latest["High"] - max(latest["Close"], latest["Open"])
    lower_wick = min(latest["Close"], latest["Open"]) - latest["Low"]

    if lower_wick > body * 2 and upper_wick < body:
        patterns["bullish_pinbar"] = 1
    elif upper_wick > body * 2 and lower_wick < body:
        patterns["bearish_pinbar"] = -1

    # ---------- BREAKOUT ----------
    recent_high = df["High"].rolling(20).max().iloc[-2]
    recent_low = df["Low"].rolling(20).min().iloc[-2]

    if latest["Close"] > recent_high:
        patterns["breakout_up"] = 1
    elif latest["Close"] < recent_low:
        patterns["breakout_down"] = -1

    return patterns