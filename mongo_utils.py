from pymongo import MongoClient
import os
import yfinance as yf
from dotenv import load_dotenv
from bson import ObjectId
import pandas as pd  # <-- Add this import

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = "stock_prediction"
COLLECTION_NAME = "historical_data"

def store_in_mongo(data):
    """
    Store stock data DataFrame into MongoDB.
    Handles MultiIndex columns by flattening them.
    """
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    # Flatten MultiIndex columns if they exist
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = ['_'.join(col).strip() for col in data.columns.values]

    # Reset index to convert 'Date' from index to column
    data = data.reset_index()

    # Convert to records and ensure all keys are strings
    records = data.to_dict('records')
    collection.insert_many(records)
    print(f"✅ Inserted {len(records)} records into MongoDB.")

def get_stock_data(ticker, start="2022-01-01", end="2024-12-31"):
    """
    Fetch historical stock data from Yahoo Finance.
    """
    data = yf.download(ticker, start=start, end=end)
    return data