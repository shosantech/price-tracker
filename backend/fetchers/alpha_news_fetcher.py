import requests
from datetime import datetime

ALPHA_API_KEY = "C20GC1NVI0TT6T6A"

GOLD_KEYWORDS = {
    "gold": 30,
    "gold stock": 30,
    "bullion": 20,
    "precious metal": 20,
    "precious metals": 20,
    "gold price": 25,
    "gold futures": 25,
    "central bank gold": 30,
    "inflation hedge": 20,
}

# NEGATIVE_KEYWORDS = {
#     "stock": -20,
#     "shares": -20,
#     "earnings": -30,
#     "company": -20,
#     "ceo": -20,
#     "revenue": -25,
#     "etf": -15,
#     "dividend": -25,
#     "guidance": -20,
#     "q1": -15,
#     "q2": -15,
#     "q3": -15,
#     "q4": -15,
# }

def gold_relevance_score(article):
    text = (
        (article.get("title", "") + " " + article.get("summary", ""))
        .lower()
    )

    score = 0

    for k, w in GOLD_KEYWORDS.items():
        if k in text:
            score += w

    # for k, w in NEGATIVE_KEYWORDS.items():
    #     if k in text:
    #         score += w

    return max(0, min(100, score))


def fetch_gold_news(limit=50, min_relevance=20):
    params = {
        "function": "NEWS_SENTIMENT",
        "sort": "LATEST",
        "limit": 2000,  # pull more, filter locally
        "apikey": ALPHA_API_KEY,
    }

    r = requests.get("https://www.alphavantage.co/query", params=params, timeout=15)
    data = r.json()
    print(data.get("feed", []))

    if "Information" in data:
        print("AlphaVantage error:", data["Information"])
        return []

    cleaned = []

    for a in data.get("feed", []):
        # --- Parse Alpha timestamp ---
        try:
            published_at = datetime.strptime(
                a["time_published"], "%Y%m%dT%H%M%S"
            )
        except Exception:
            continue

        relevance = gold_relevance_score(a)

        if relevance < min_relevance:
            continue

        cleaned.append({
            "title": a.get("title", ""),
            "source": a.get("source", "Unknown"),
            "publishedAt": published_at,
            "sentiment": float(a.get("overall_sentiment_score", 0.0)),
            "relevance": relevance,
            "url": a.get("url"),
        })

    # --- Sort by relevance first, then freshness ---
    cleaned.sort(
        key=lambda x: (x["publishedAt"]),
        reverse=True
    )

    return cleaned[:limit]
