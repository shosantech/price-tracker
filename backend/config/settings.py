import os
from dotenv import load_dotenv

load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")

DEFAULT_SYMBOL = "GC=F"  # Gold Futures symbol on Yahoo Finance

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "market_data.db")

