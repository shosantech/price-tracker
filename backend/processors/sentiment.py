from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime, timezone
import numpy as np
from difflib import SequenceMatcher


analyzer = SentimentIntensityAnalyzer()

HIGH_IMPACT_ARTICLE_THRESHOLD = 10
MIN_ARTICLES_FOR_SENTIMENT = 5

SENTIMENT_BUY_THRESHOLD = 0.35
SENTIMENT_SELL_THRESHOLD = -0.35

MAX_SENTIMENT_WEIGHT = 0.4   # sentiment can never dominate
TECHNICAL_WEIGHT = 0.6


CREDIBLE_SOURCES = {
    "reuters": 1.5,
    "bloomberg": 1.5,
    "financial times": 1.4,
    "wsj": 1.4,
    "cnbc": 1.3,
    "livemint": 1.2,
    "barchart": 1.1,
}

GOLD_KEYWORDS = [
    "gold", "bullion", "precious metal", "fed", "inflation",
    "interest rates", "central bank", "usd", "dollar"
]

EQUITY_TERMS = [
    "nyse:", "nasdaq:", "shares", "stock",
    "price target", "earnings", "equity"
]


def is_similar(a, b, threshold=0.85):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() >= threshold

def deduplicate_articles(scored_articles):
    deduped = []

    for art in sorted(scored_articles, key=lambda x: x["final_score"], reverse=True):
        if not any(is_similar(art["title"], d["title"]) for d in deduped):
            deduped.append(art)

    return deduped

def equity_penalty(title):
    title = title.lower()
    return 0.7 if any(t in title for t in EQUITY_TERMS) else 1.0


INSTITUTIONAL_TERMS = [
    "purchase", "buying spree", "accumulation",
    "added to reserves", "holdings increased"
]

PRICE_TARGET_TERMS = [
    "price target", "raises target", "cuts target",
    "forecast", "outlook"
]

MACRO_TERMS = [
    "inflation", "interest rates", "fed",
    "central bank", "geopolitical", "war",
    "sanctions", "recession"
]


def topic_relevance_adjustment(title: str) -> float:
    t = title.lower()

    if any(x in t for x in INSTITUTIONAL_TERMS):
        return 0.7
    if any(x in t for x in PRICE_TARGET_TERMS):
        return 0.6
    if any(x in t for x in MACRO_TERMS):
        return 1.3

    return 1.0


def score_article(article):
    """Score a single article with soft relevance weighting"""

    title = article["title"]

    # --- Sentiment ---
    sentiment = analyzer.polarity_scores(title)["compound"]

    # --- Credibility ---
    credibility = CREDIBLE_SOURCES.get(article.get("source", "").lower(), 1.0)

    # --- Keyword relevance ---
    title_l = title.lower()
    relevance_hits = sum(1 for k in GOLD_KEYWORDS if k in title_l)
    relevance = 1 + min(relevance_hits * 0.2, 1.0)

    # --- Topic soft filter ---
    relevance *= topic_relevance_adjustment(title)

    # --- Recency ---
    try:
        published_at = article["publishedAt"]
        if isinstance(published_at, str):
            published_at = datetime.fromisoformat(published_at.replace("Z", "+00:00"))

        hours_ago = (datetime.now(timezone.utc) - published_at).total_seconds() / 3600
        recency = max(0.3, 1 - (hours_ago / 168))
    except Exception:
        recency = 0.6

    equity_weight = equity_penalty(title)

    final_score = sentiment * credibility * relevance * recency * equity_weight

    return {
        **article,
        "sentiment": sentiment,
        "credibility": credibility,
        "relevance": relevance,
        "recency": recency,
        "final_score": final_score
    }




def compute_sentiment(articles, past_volumes, past_avg_sentiments=None):

    # -------------------------
    # 1. Score every article
    # -------------------------
    scored_articles = []
    for a in articles:
        if not a.get("title"):
            continue
        scored_articles.append(score_article(a))

    this_week = len(scored_articles)
    avg_weekly = np.mean([v[1] for v in past_volumes]) if past_volumes else this_week

    volume_increase = (
        ((this_week - avg_weekly) / avg_weekly) * 100
        if avg_weekly else 0
    )
    volume_flag = volume_increase >= 20

    # -------------------------
    # 2. Deduplicate headlines
    # -------------------------
    scored_articles = deduplicate_articles(scored_articles)

    # -------------------------
    # 3. Rank by impact
    # -------------------------
    scored_articles.sort(
        key=lambda x: abs(x["final_score"]),
        reverse=True
    )

    # -------------------------
    # 4. Split influence roles
    # -------------------------
    top_5 = scored_articles[:5]
    top_10 = scored_articles[:10]

    # Direction → strongest signals
    directional_avg = (
        np.mean([a["final_score"] for a in top_5])
        if top_5 else 0.0
    )

    # Confidence → broader pressure
    confidence_avg = (
        np.mean([a["final_score"] for a in top_10])
        if top_10 else 0.0
    )

    # -------------------------
    # 5. Sentiment dispersion
    # -------------------------
    sentiment_std = (
        np.std([a["final_score"] for a in top_10])
        if len(top_10) >= 3 else 0.0
    )

    avg_sentiment = directional_avg


    # -------------------------
    # 6. Store history
    # -------------------------
    if past_avg_sentiments is None:
        past_avg_sentiments = []
    past_avg_sentiments.append(avg_sentiment)

    return (
    scored_articles,
    volume_flag,
    this_week,
    avg_weekly,
    volume_increase,
    avg_sentiment,
    sentiment_std,
    past_avg_sentiments,
    )


def generate_sentiment(price_df, avg_sentiment, volume_flag, sentiment_std, past_sentiments=None):
    """
    Generates a signal using ranked news sentiment + technical context.
    History adjusts confidence, not direction.
    """
    

    # -------------------------------------------------
    # 1. Historical normalization (soft, continuous)
    # -------------------------------------------------
    if past_sentiments and len(past_sentiments) >= 3:
        hist_mean = np.mean(past_sentiments)
        hist_std = np.std(past_sentiments) + 1e-6
        z_score = (avg_sentiment - hist_mean) / hist_std

        # Clamp extreme z-scores
        z_score = np.clip(z_score, -2.5, 2.5)

        # Normalize to [-1, 1]
        sentiment_component = z_score / 2.5
    else:
        # No history → trust raw sentiment (but clamp)
        sentiment_component = np.clip(avg_sentiment, -1, 1)
        z_score = None

    # -------------------------------------------------
    # 2. Volume confirmation (boost, not filter)
    # -------------------------------------------------
    if volume_flag:
        sentiment_component *= 1.15

    # -------------------------------------------------
    # 3. Technical trend
    # -------------------------------------------------
    ma20 = price_df["MA_20"].iloc[-1]
    ma50 = price_df["MA_50"].iloc[-1]
    trend_component = 1 if ma20 > ma50 else -1 if ma20 < ma50 else 0

    # -------------------------------------------------
    # 4. RSI context
    # -------------------------------------------------
    rsi = price_df["RSI"].iloc[-1]
    if rsi < 30:
        rsi_component = 1
    elif rsi > 70:
        rsi_component = -1
    else:
        rsi_component = 0

    # -------------------------------------------------
    # 5. Price location (range-aware)
    # -------------------------------------------------
    close = price_df["Close"].iloc[-1]
    recent_min = price_df["Close"].rolling(30).min().iloc[-1]
    recent_max = price_df["Close"].rolling(30).max().iloc[-1]

    if close <= recent_min * 1.03:
        price_component = 1
    elif close >= recent_max * 0.97:
        price_component = -1
    else:
        price_component = 0

    # Dispersion penalty (uncertainty dampener)
    if sentiment_std > 0.25:
        sentiment_component *= 0.7
    elif sentiment_std < 0.12:
        sentiment_component *= 1.1

    # -------------------------------------------------
    # 6. Weighted fusion
    # -------------------------------------------------
    final_score = (
    1.4 * sentiment_component +
    1.0 * trend_component +
    0.6 * rsi_component +
    0.6 * price_component
)

    # Gold asymmetry: fear > optimism
    if final_score < 0:
        final_score *= 1.15
    else:
        final_score *= 0.95

    # -------------------------------------------------
    # 7. Decision bands
    # -------------------------------------------------
    if final_score >= 1.2:
        signal = "BUY"
    elif final_score <= -1.2:
        signal = "SELL"
    else:
        signal = "HOLD"

    print(
        f"DEBUG | sentiment={avg_sentiment:.3f} "
        f"| z={round(z_score,2) if z_score is not None else 'n/a'} "
        f"| final={round(final_score,2)} "
        f"| signal={signal}"
    )

    return signal, avg_sentiment