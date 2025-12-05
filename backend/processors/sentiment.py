from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime, timedelta
import numpy as np

analyzer = SentimentIntensityAnalyzer()

def calculate_weighted_sentiment(sentiment_list):
    credible_sources = ["Reuters", "Bloomberg", "CNBC", "BusinessLine", "The Times of India"]
    forward_keywords = ["expansion", "acquisition", "new contract", "market entry", "FDA approval"]

    weighted_sentiments = []
    for a in sentiment_list:
        score = a["sentiment"]
        weight = 2 if a["source"] in credible_sources else 1
        if any(kw.lower() in a["title"].lower() for kw in forward_keywords):
            weight *= 1.5
        weighted_sentiments.append(score * weight)

    return sum(weighted_sentiments) / max(len(weighted_sentiments), 1)

def compute_sentiment(articles, past_volumes, past_avg_sentiments=None):
    """
    Compute sentiment for a list of articles with weekly metrics.
    - articles: list of news dicts
    - past_volumes: list of tuples [(week_start, total_articles), ...]
    - past_avg_sentiments: list of floats of previous weeks' avg_sentiment
    Returns:
        sentiment_list, volume_flag, this_week, avg_weekly, volume_increase, past_avg_sentiments
    """

    sentiment_list = []
    for a in articles:
        score = analyzer.polarity_scores(a["title"])["compound"]
        sentiment_list.append({
            "title": a["title"],
            "source": a.get("source", "Unknown"),
            "publishedAt": a["publishedAt"],
            "sentiment": score
        })

    # Weekly metrics
    this_week = len(articles)
    avg_weekly = np.mean([v[1] for v in past_volumes]) if past_volumes else this_week

    # Detect volume spike
    volume_increase = ((this_week - avg_weekly) / avg_weekly) * 100 if avg_weekly else 0
    volume_flag = volume_increase >= 20  # Example threshold

    # Compute current week's average weighted sentiment
    current_avg_sentiment = calculate_weighted_sentiment(sentiment_list)

    # Append to historical sentiments
    if past_avg_sentiments is None:
        past_avg_sentiments = []
    past_avg_sentiments.append(current_avg_sentiment)

    return sentiment_list, volume_flag, this_week, avg_weekly, volume_increase, past_avg_sentiments

def generate_sentiment(price_df, sentiment_list, volume_flag, past_sentiments=None):
    """
    Generates a sentiment-based signal using current and optionally historical weekly sentiment.
    - price_df: dataframe with gold prices & technical indicators
    - sentiment_list: current week's articles sentiment
    - volume_flag: current week's volume spike flag
    - past_sentiments: list of avg_sentiment from past weeks
    """

    # 1. Current week's weighted sentiment
    avg_sentiment = calculate_weighted_sentiment(sentiment_list)

    # 2. Historical context adjustment (optional)
    if past_sentiments and len(past_sentiments) > 0:
        hist_mean = np.mean(past_sentiments)
        hist_std = np.std(past_sentiments)
        # Z-score of current sentiment
        z_score = (avg_sentiment - hist_mean) / (hist_std + 1e-6)
    else:
        z_score = 0  # No past data

    # 3. Sentiment score
    # Use z_score if historical data exists, else use absolute thresholds
    if past_sentiments:
        if z_score > 0.5:
            sentiment_score = 1
        elif z_score < -0.5:
            sentiment_score = -1
        else:
            sentiment_score = 0
    else:
        if avg_sentiment > 0.2:
            sentiment_score = 1
        elif avg_sentiment < -0.2:
            sentiment_score = -1
        else:
            sentiment_score = 0

    # 4. Technical score
    ma20 = price_df["MA_20"].iloc[-1]
    ma50 = price_df["MA_50"].iloc[-1]
    trend_score = 1 if ma20 > ma50 else -1 if ma20 < ma50 else 0

    rsi = price_df["RSI"].iloc[-1]
    rsi_score = 1 if rsi < 30 else -1 if rsi > 70 else 0

    # 5. Price context score
    close = price_df["Close"].iloc[-1]
    recent_min = price_df["Close"].rolling(30).min().iloc[-1]
    recent_max = price_df["Close"].rolling(30).max().iloc[-1]
    price_score = 1 if close <= recent_min * 1.05 else -1 if close >= recent_max * 0.95 else 0

    # 6. Combine scores
    final_score = sentiment_score + trend_score + rsi_score + price_score
    if final_score >= 2:
        signal = "BUY"
    elif final_score <= -2:
        signal = "SELL"
    else:
        signal = "HOLD"

    print("DEBUG: avg_sentiment:", avg_sentiment, 
          "z_score:", round(z_score, 2),
          "sentiment_score:", sentiment_score,
          "final_score:", final_score,
          "signal:", signal)

    return signal, avg_sentiment
