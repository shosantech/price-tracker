import requests
from datetime import datetime, timedelta
from config.settings import NEWS_API_KEY

def fetch_gold_news_past_week():
    url = "https://newsapi.org/v2/everything"

    # Only get news from the past 7 days
    today = datetime.utcnow()
    week_ago = today - timedelta(days=7)
    from_param = week_ago.strftime("%Y-%m-%dT%H:%M:%SZ")  # ISO 8601 format

    params = {
        "q": "gold price OR gold stock OR gold market OR gold trading OR gold futures OR gold bullion OR gold investment OR gold ounce OR gold expected OR gold gains",
        "searchIn": "title,description",
        "language": "en",
        "from": from_param,
        "pageSize": 50,
        "sortBy": "publishedAt",
        "apiKey": NEWS_API_KEY
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Error fetching gold news: {e}")
        return [], 0

    total_results = data.get("totalResults", 0)
    articles = []

    for a in data.get("articles", []):
        articles.append({
            "source": a.get("source", {}).get("name", "Unknown"),
            "publishedAt": a.get("publishedAt"),
            "title": a.get("title"),
            "url": a.get("url")
        })

    # Sort from most recent to oldest just in case
    articles.sort(key=lambda x: x["publishedAt"], reverse=True)

    return articles, total_results

if __name__ == "__main__":
    articles, total_results = fetch_gold_news_past_week()
    print(f"Total results in past week: {total_results}\n")
    for i, article in enumerate(articles, start=1):
        print(f"{i}. {article['source']} - {article['title']} - {article['publishedAt']}")
        print(f"URL: {article['url']}\n")
