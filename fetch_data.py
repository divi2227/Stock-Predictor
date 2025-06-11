import yfinance as yf
import pandas as pd

def get_stock_data(ticker, start="2022-01-01", end="2024-12-31"):
    """
    Fetch historical stock data from Yahoo Finance.
    """
    data = yf.download(ticker, start=start, end=end)
    return data
