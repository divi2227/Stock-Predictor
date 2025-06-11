import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# Step 1: Define the stock ticker
ticker = "AAPL"  # Apple Inc.

# Step 2: Download historical stock data
data = yf.download(ticker, start="2022-01-01", end="2024-12-31")

# Step 3: Display sample data
print("Sample Data:")
print(data.head())

# Step 4: Optional - Plot the closing prices
data['Close'].plot(title=f"{ticker} Closing Prices", figsize=(10,5))
plt.xlabel("Date")
plt.ylabel("Price (USD)")
plt.grid(True)
plt.show()