def convert_to_score(signal):
    if signal == "BUY":
        return 1
    elif signal == "SELL":
        return -1
    return 0  # HOLD


def generate_combined_signal(technical_signal, sentiment_signal):
    """
    Weighted fusion:
    - Technical weight: 2
    - Sentiment weight: 1
    """

    tech_score = convert_to_score(technical_signal)
    sent_score = convert_to_score(sentiment_signal)

    final_score = (tech_score * 2) + (sent_score * 1)

    if final_score >= 2:
        return "BUY"
    elif final_score <= -2:
        return "SELL"
    else:
        return "HOLD"
    
    
