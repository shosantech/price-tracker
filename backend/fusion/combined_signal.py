# fusion/combined_signal.py

# fusion/combined_signal.py

def convert_signal_to_numeric(signal: str) -> float:
    signal = signal.upper()
    if signal == "BUY":
        return 1.0
    elif signal == "SELL":
        return -1.0
    return 0.0


def detect_regime(technical: dict) -> str:
    trend_strength = (
        abs(technical["components"].get("trend_short", 0)) +
        abs(technical["components"].get("trend_medium", 0)) +
        abs(technical["components"].get("trend_long", 0))
    )

    volatility = technical["components"].get("volatility_factor", 1)

    if trend_strength >= 2 and volatility > 0.9:
        return "TRENDING"
    else:
        return "RANGING"


def generate_explanation(technical, sentiment_signal, regime):
    reasons = []

    if technical["signal"] == "SELL":
        reasons.append("Price is overextended near resistance with high RSI.")
    elif technical["signal"] == "BUY":
        reasons.append("Price is near support with bullish structure.")

    if sentiment_signal == "BUY":
        reasons.append("News sentiment is strongly positive.")
    elif sentiment_signal == "SELL":
        reasons.append("News sentiment is negative and risk-off.")

    if regime == "RANGING":
        reasons.append("Market is in a ranging regime; mean-reversion dominates.")
    else:
        reasons.append("Market is in a trending regime; momentum dominates.")

    return " ".join(reasons)



def generate_combined_signal(technical: dict, sentiment_signal: str, avg_sentiment: float = 0.0):
    tech_score = technical.get("score", 0)
    tech_conf = technical.get("confidence", 100) / 100
    weighted_tech = tech_score * tech_conf * 0.6

    sent_numeric = convert_signal_to_numeric(sentiment_signal)
    sentiment_strength = max(min(abs(avg_sentiment), 1.0), 0.0) * 0.4
    weighted_sentiment = sent_numeric * sentiment_strength

    combined_score = weighted_tech + weighted_sentiment

    # Gold asymmetry
    if combined_score < 0:
        combined_score *= 1.15
    else:
        combined_score *= 0.95

    if combined_score >= 0.6:
        final_signal = "BUY"
    elif combined_score <= -0.6:
        final_signal = "SELL"
    else:
        final_signal = "HOLD"

    # ---------- REGIME ----------
    regime = detect_regime(technical)

    # ---------- ALIGNMENT ----------
    tech_dir = 1 if tech_score > 0 else -1 if tech_score < 0 else 0
    sent_dir = 1 if sent_numeric > 0 else -1 if sent_numeric < 0 else 0

    if tech_dir == sent_dir:
        alignment = 1.0
    elif sent_dir == 0 or tech_dir == 0:
        alignment = 0.8
    else:
        alignment = 0.5

    # ---------- CONFIDENCE ----------
    base_conf = min(abs(combined_score) * 100, 100)
    combined_confidence = round(base_conf * alignment, 1)

    explanation = generate_explanation(
        technical,
        sentiment_signal,
        regime
    )

    return {
        "signal": final_signal,
        "score": round(combined_score, 2),
        "confidence": combined_confidence,
        "regime": regime,
        "explanation": explanation
    }
