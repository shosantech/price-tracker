import requests
from datetime import datetime, timedelta
from config.settings import NEWSDATA_API_KEY

def fetch_gold_news_past_week():
    url = "https://newsdata.io/api/1/news"

    params = {
        "apikey": NEWSDATA_API_KEY,
        "q": "gold price OR gold market OR gold investment OR gold bullion",
        "language": "en",
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Error fetching gold news: {e}")
        return []

    articles = []

    for a in data.get("results", []):
        articles.append({
            "source": a.get("source_id", "Unknown"),
            "publishedAt": a.get("pubDate"),  # keep raw
            "title": a.get("title") or "",
            "url": a.get("link"),
        })

    return articles


if __name__ == "__main__":
    articles, total_results = fetch_gold_news_past_week()
    print(f"Total results in past week: {total_results}\n")

    for i, article in enumerate(articles, start=1):
        print(
            f"{i}. {article['source']} - {article['title']} - {article['publishedAt']}"
        )
        print(f"URL: {article['url']}\n")
