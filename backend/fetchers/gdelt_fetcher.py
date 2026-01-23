import requests
from datetime import datetime, timezone
import math


CREDIBLE_DOMAINS = {
    "reuters.com",
    "bloomberg.com",
    "cnbc.com",
    "marketwatch.com",
    "ft.com",
    "wsj.com",
    "investing.com",
    "kitco.com",
    "bbc.co.uk",
    "cnn.com",
}

POSITIVE_KEYWORDS = {
    "gold", "bullion", "futures", "spot", "ounce",
    "inflation", "fed", "yield", "dollar",
    "etf", "commodities", "safe haven"
}

NEGATIVE_KEYWORDS = {
    "jewelry", "ring", "necklace", "wedding",
    "fashion", "gift", "bracelet"
}

HALF_LIFE_HOURS = 24


def parse_gdelt_date(article):
    try:
        if "seendate" in article:
            return datetime.strptime(
                article["seendate"], "%Y%m%dT%H%M%SZ"
            ).replace(tzinfo=timezone.utc)

        if "publishedAt" in article:
            return datetime.fromisoformat(
                article["publishedAt"].replace("Z", "+00:00")
            )

        if "datetime" in article:
            return datetime.fromisoformat(
                article["datetime"].replace("Z", "+00:00")
            )
    except Exception:
        return None


def gold_relevance_score(title: str) -> float:
    title_l = title.lower()

    if any(bad in title_l for bad in NEGATIVE_KEYWORDS):
        return 0.0

    hits = sum(1 for k in POSITIVE_KEYWORDS if k in title_l)

    if "gold" not in title_l:
        return 0.0

    return min(1.0, hits / 4)


def freshness_weight(published_at: datetime) -> float:
    now = datetime.now(timezone.utc)
    hours = (now - published_at).total_seconds() / 3600
    return math.exp(-hours / HALF_LIFE_HOURS)


def fetch_gold_news_gdelt(max_records=50):
    url = "https://api.gdeltproject.org/api/v2/doc/doc"
    params = {
        "query": "gold stock",
        "mode": "artlist",
        "format": "json",
        "maxrecords": 200  # fetch extra, filter later
    }

    r = requests.get(url, params=params, timeout=15)
    if r.status_code != 200:
        return []

    data = r.json()
    articles = data.get("articles", [])

    cleaned = []

    for a in articles:
        if a.get("language") != "English":
            continue

        domain = a.get("domain", "")
        # if not any(domain.endswith(d) for d in CREDIBLE_DOMAINS):
        #     continue

        published_at = parse_gdelt_date(a)
        # if not published_at:
        #     continue

        title = a.get("title", "")
        relevance = gold_relevance_score(title)
        # if relevance == 0:
        #     continue

        freshness = freshness_weight(published_at)
        final_weight = relevance * freshness

        cleaned.append({
            "title": title,
            "source": domain,
            "publishedAt": published_at,
            "relevance": round(relevance, 3),
            "freshness": round(freshness, 3),
            "weight": round(final_weight, 3),
            "url": a.get("url")
        })
    print(articles)

    cleaned.sort(key=lambda x: x["publishedAt"], reverse=True)

    return cleaned[:max_records]
