import matplotlib.pyplot as plt

def plot_closing_prices(data, ticker):
    """
    Plot the closing price of the stock.
    """
    data['Close'].plot(title=f"{ticker} Closing Prices", figsize=(10, 5))
    plt.xlabel("Date")
    plt.ylabel("Price (USD)")
    plt.grid(True)
    plt.show()
