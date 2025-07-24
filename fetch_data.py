import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# ✅ Optional mapping for different markets
MARKET_SUFFIXES = {
    "US": "",
    "IN": ".NS",
    "EU": ".DE",
    "HK": ".HK",
    "JP": ".T",
}

def get_stock_data(ticker: str, market: str = "US", period: str = "1mo", interval: str = "1d"):
    try:
        ticker = ticker.strip().upper()
        suffix = MARKET_SUFFIXES.get(market.upper(), "")
        full_ticker = f"{ticker}{suffix}"
        print(f"🌐 Market: {market} | Ticker: {full_ticker}")
        print(f"📅 Period: {period} | Interval: {interval}")

        raw = yf.download(full_ticker, period=period, interval=interval, progress=False)

        if isinstance(raw, tuple):
            raw = raw[0]

        if not isinstance(raw, pd.DataFrame) or raw.empty:
            print(f"⚠️ No data from yfinance for {full_ticker}")
            return []

        df = raw.reset_index()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = ["_".join([str(c) for c in col if c]).lower() for col in df.columns.values]
        else:
            df.columns = [str(c).lower() for c in df.columns]

        rename_map = {}
        for col in df.columns:
            if col.startswith("close"): rename_map[col] = "close"
            elif col.startswith("open"): rename_map[col] = "open"
            elif col.startswith("high"): rename_map[col] = "high"
            elif col.startswith("low"): rename_map[col] = "low"
            elif col.startswith("volume"): rename_map[col] = "volume"

        if rename_map:
            df = df.rename(columns=rename_map)
            print(f"✅ Renamed columns: {rename_map}")

        if "close" not in df.columns:
            print(f"❌ No 'close' column found. Columns: {list(df.columns)}")
            return []

        print(f"✅ Successfully fetched {len(df)} records for {full_ticker}.")
        return df.to_dict(orient="records")

    except Exception as e:
        print(f"💥 Exception in get_stock_data({ticker}): {e}")
        return []

