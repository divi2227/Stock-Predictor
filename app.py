from flask import Flask, render_template, request, jsonify
from mongo_utils import store_in_mongo  # Your existing functions
import pandas as pd
import os
from fetch_data import get_stock_data


app = Flask(__name__)

@app.route("/ping")
def ping():
    return "pong"

@app.route('/')
def index():
    """Serve the main UI"""
    return render_template('index.html')

@app.route('/api/stocks', methods=['GET'])
def get_stock():
    """Backend API endpoint"""
    ticker = request.args.get('ticker', 'AAPL').upper()
    
    # 1. Get data from MongoDB (using your existing function)
    data = get_stock_data(ticker)  # Implement this in mongo_utils.py
    
    # 2. Process data (example - replace with your actual prediction)
    df = pd.DataFrame(data)
    prediction = {
        'ticker': ticker,
        'current_price': df['close'].iloc[-1],
        'predicted': df['close'].iloc[-1] * 1.05,  # Mock prediction
        'history': df.tail(30).to_dict('records')
    }
    
    return jsonify(prediction)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # use PORT from Render, or 5000 locally
    app.run(host="0.0.0.0", port=port)
