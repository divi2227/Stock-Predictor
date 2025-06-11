from app.fetch_data import get_stock_data
from app.plot_data import plot_closing_prices
from app.mongo_utils import store_in_mongo
from app.vector_utils import create_embedding_and_store

def main():
    ticker = "AAPL"

    # Step 1: Fetch stock data
    data = get_stock_data(ticker)
    print("Sample Data:")
    print(data.head())

    # Step 2: Plot the data
    plot_closing_prices(data, ticker)

    # Step 3: Insert data into MongoDB
    store_in_mongo(data)

    # Step 4: Store a sentence in Vector DB
    text = "Apple stock is expected to rise after product launch"
    create_embedding_and_store(text)

if __name__ == "__main__":
    main()
