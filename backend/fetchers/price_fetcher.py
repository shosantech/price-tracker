import yfinance as yf
import pandas as pd

def fetch_gold_prices(period="1y", interval="1d"):
    ticker = yf.Ticker("GC=F")  # Gold Futures
    df = ticker.history(period=period, interval=interval)

    if df.empty:
        raise Exception("Failed to fetch gold prices from Yahoo Finance.")

    df = df[['Close', 'Volume']]
    df.reset_index(inplace=True)
    return df
