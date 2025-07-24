from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
import requests
from io import StringIO
import yfinance as yf
from fetch_data import get_stock_data
from mongo_utils import store_in_mongo, store_factors, fetch_all_docs
import openai
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()  # 👈 this loads environment variables from .env

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


app = Flask(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.0.0 Safari/537.36"
    )
}

@app.route("/")
def index():
    return render_template("index.html")

def normalize_gainers_losers(df):
    rename_map = {}
    if "Last Price" in df.columns:
        rename_map["Last Price"] = "Price (Intraday)"
    if "Change %" in df.columns:
        rename_map["Change %"] = "% Change"
    if rename_map:
        df = df.rename(columns=rename_map)
    return df

@app.route("/api/top-gainers", methods=["GET"])
def top_gainers():
    try:
        url = "https://finance.yahoo.com/gainers"
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        html = response.text
        tables = pd.read_html(StringIO(html))
        if not tables:
            raise Exception("No tables found on Yahoo Finance gainers page.")
        df = normalize_gainers_losers(tables[0])

        symbols = df["Symbol"].head(5).tolist()
        results = []
        for sym in symbols:
            try:
                info = yf.Ticker(sym).fast_info
                price = info.get("last_price", None)
            except Exception as e:
                print(f"⚠️ Could not fetch price for {sym}: {e}")
                price = None
            change_val = df.loc[df["Symbol"] == sym, "% Change"].values
            change_str = change_val[0] if len(change_val) > 0 else "-"
            results.append({"Symbol": sym, "Price": price if price else "-", "% Change": change_str})

        return jsonify(results)
    except Exception as e:
        print(f"❌ Error fetching gainers: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/top-losers", methods=["GET"])
def top_losers():
    try:
        url = "https://finance.yahoo.com/losers"
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        html = response.text
        tables = pd.read_html(StringIO(html))
        if not tables:
            raise Exception("No tables found on Yahoo Finance losers page.")
        df = normalize_gainers_losers(tables[0])

        symbols = df["Symbol"].head(5).tolist()
        results = []
        for sym in symbols:
            try:
                info = yf.Ticker(sym).fast_info
                price = info.get("last_price", None)
            except Exception as e:
                print(f"⚠️ Could not fetch price for {sym}: {e}")
                price = None
            change_val = df.loc[df["Symbol"] == sym, "% Change"].values
            change_str = change_val[0] if len(change_val) > 0 else "-"
            results.append({"Symbol": sym, "Price": price if price else "-", "% Change": change_str})

        return jsonify(results)
    except Exception as e:
        print(f"❌ Error fetching losers: {e}")
        return jsonify({"error": str(e)}), 500

US_TICKERS = ["AAPL","MSFT","GOOGL","AMZN","META","NVDA","TSLA","JPM","V","JNJ"]
IN_TICKERS = ["RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS"]
EU_TICKERS = ["ADS.DE","BMW.DE","SAP.DE","DTE.DE"]
HK_TICKERS = ["0700.HK","0941.HK","0005.HK"]
JP_TICKERS = ["7203.T","6758.T","9984.T"]

def get_market_tickers(market):
    return {
        "US": US_TICKERS,
        "IN": IN_TICKERS,
        "EU": EU_TICKERS,
        "HK": HK_TICKERS,
        "JP": JP_TICKERS
    }.get(market, [])

@app.route("/api/top-investments", methods=["GET"])
def top_investments():
    try:
        period = request.args.get("period","1y")
        interval = request.args.get("interval","1d")
        market = request.args.get("market","US")
        results = []

        for symbol in get_market_tickers(market):
            try:
                data = yf.download(symbol, period=period, interval=interval, progress=False)
                if data.empty: continue
                first_price = float(data["Close"].iloc[0])
                last_price = float(data["Close"].iloc[-1])
                roi = ((last_price-first_price)/first_price)*100
                returns = data["Close"].pct_change().dropna()
                volatility = float(returns.std()*(252**0.5)) if not returns.empty else None
                info = yf.Ticker(symbol).info
                pe_ratio = info.get("trailingPE")
                profit_margin = info.get("profitMargins")
                so = info.get("sharesOutstanding")
                fs = info.get("floatShares")
                dilution_score = ((so-fs)/so) if so and fs else None
                score = 0
                if roi: score += roi
                if profit_margin: score += profit_margin*100
                if pe_ratio and pe_ratio>0: score += (50/pe_ratio)
                if volatility: score -= volatility
                if dilution_score: score -= dilution_score*100

                factors_doc = {
                    "symbol": symbol,
                    "roi": round(roi,2),
                    "pe_ratio": pe_ratio,
                    "profit_margin": profit_margin,
                    "volatility": round(volatility,4) if volatility else None,
                    "dilution_score": round(dilution_score,4) if dilution_score else None,
                    "score": round(score,2),
                    "period": period,
                    "interval": interval,
                    "market": market
                }
                store_factors(factors_doc)
                results.append(factors_doc)
            except Exception as e:
                print(f"⚠️ Error {symbol}: {e}")
                continue

        top5 = sorted(results,key=lambda x:x.get("score",0),reverse=True)[:5]
        for doc in top5: doc.pop("_id",None)
        return jsonify(top5)
    except Exception as e:
        print(f"💥 Error in /api/top-investments: {e}")
        return jsonify({"error":str(e)}),500

openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/api/openai-recommendation", methods=["POST"])
def openai_recommendation():
    try:
        user_prompt = request.json.get("prompt", "")
        from mongo_utils import fetch_all_docs
        factors = fetch_all_docs("stock_factors")

        # Construct the base prompt with factors
        prompt = "Given the following stock factors (ROI, P/E ratio, Profit Margin, Volatility, Dilution Score):\n"
        for f in factors:
            prompt += f"Symbol: {f.get('symbol')}, ROI: {f.get('roi')}%, P/E: {f.get('pe_ratio')}, Profit Margin: {f.get('profit_margin')}, Volatility: {f.get('volatility')}, Dilution: {f.get('dilution_score')}\n"
        prompt += f"\nUser question: {user_prompt}\n\nGive a concise answer."

        # Use the new v1 interface with chat completions
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert stock advisor."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )

        answer = response.choices[0].message.content.strip()
        return jsonify({"recommendation": answer})
    except Exception as e:
        print(f"💥 Error in OpenAI recommendation: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/stocks", methods=["GET"])
def get_stock():
    try:
        ticker = request.args.get("ticker","AAPL").upper()
        market = request.args.get("market","US").upper()
        period = request.args.get("period","1mo")
        interval = request.args.get("interval","1d")
        print(f"📥 /api/stocks called with ticker: {ticker} | market: {market} | range: {period} | interval: {interval}")
        data = get_stock_data(ticker,market,period,interval)
        if not data: return jsonify({"error":"No data fetched"}),500
        df = pd.DataFrame(data)
        if df.empty: return jsonify({"error":"No data fetched, empty dataframe"}),500
        df.columns=[str(c).lower() for c in df.columns]
        rename_map={}
        for c in df.columns:
            if c.endswith("_close"): rename_map[c]="close"
            elif c.endswith("_open"): rename_map[c]="open"
            elif c.endswith("_high"): rename_map[c]="high"
            elif c.endswith("_low"): rename_map[c]="low"
            elif c.endswith("_volume"): rename_map[c]="volume"
        if rename_map:
            print(f"✅ Renamed columns: {rename_map}")
            df=df.rename(columns=rename_map)
        if "close" not in df.columns:
            return jsonify({"error":f"Unexpected data format: {list(df.columns)}"}),500
        current_price=float(df["close"].iloc[-1])
        predicted=current_price*1.05
        return jsonify({"ticker":ticker,"market":market,"current_price":current_price,"predicted":predicted,"history":df.tail(30).to_dict("records")})
    except Exception as e:
        print(f"💥 Exception in /api/stocks: {e}")
        return jsonify({"error":str(e)}),500

if __name__=="__main__":
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port,debug=True)
