from pymongo import MongoClient
import os
import yfinance as yf
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime, timedelta

load_dotenv()

# MongoDB configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017")
DB_NAME = os.getenv("DB_NAME", "stock_prediction")
STOCK_COLLECTION = os.getenv("COLLECTION_NAME", "stocks")
FACTORS_COLLECTION = "stock_factors"

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[STOCK_COLLECTION]
factors_collection = db[FACTORS_COLLECTION]


def store_in_mongo(data: pd.DataFrame, ticker: str):
    """Store stock historical data into MongoDB."""
    if data is None or data.empty:
        print(" No data to insert.")
        return

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = ['_'.join(col).strip().lower() for col in data.columns.values]
    else:
        data.columns = [col.lower() for col in data.columns]

    data = data.reset_index()
    data['ticker'] = ticker.upper()
    records = data.to_dict('records')

    if records:
        collection.insert_many(records)
        print(f"✅ Inserted {len(records)} records for {ticker} into MongoDB.")


def get_stock_data(ticker: str, start=None, end=None):
    """Fetch historical stock data from MongoDB or Yahoo if not cached."""
    ticker = ticker.upper()
    if start is None:
        start = (datetime.today() - timedelta(days=30)).strftime("%Y-%m-%d")
    if end is None:
        end = datetime.today().strftime("%Y-%m-%d")

    print(f"📡 Checking MongoDB for {ticker} data from {start} to {end}...")
    docs = list(collection.find({"ticker": ticker}))
    if docs:
        print(f"✅ Found {len(docs)} records for {ticker} in MongoDB.")
        df = pd.DataFrame(docs)
        if "_id" in df.columns:
            df = df.drop(columns=["_id"])
        return df

    # Fetch from Yahoo if not in DB
    print(f"📡 No cached data. Fetching from Yahoo Finance for {ticker}...")
    try:
        raw = yf.download(ticker, start=start, end=end, group_by="ticker")
        if raw.empty:
            print("❌ No data from Yahoo Finance.")
            return pd.DataFrame()

        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = ['_'.join(col).strip().lower() for col in raw.columns.values]
        else:
            raw.columns = [col.lower() for col in raw.columns]

        raw = raw.reset_index()
        raw['ticker'] = ticker
        store_in_mongo(pd.DataFrame(raw), ticker)
        return pd.DataFrame(raw)

    except Exception as e:
        print(f"❌ Exception fetching data: {e}")
        return pd.DataFrame()


def store_factors(doc: dict):
    """Store calculated factors for a stock into a separate collection."""
    if not doc:
        return
    # Optional: add a timestamp
    doc["stored_at"] = datetime.utcnow()
    factors_collection.insert_one(doc)
    print(f"✅ Stored factors for {doc.get('symbol')} into {FACTORS_COLLECTION} collection.")


def fetch_all_docs(collection_name):
    collection = db[collection_name]
    docs = list(collection.find({}))
    # remove _id for JSON serialization
    for doc in docs:
        doc.pop("_id", None)
    return docs
