# app/__init__.py

from .fetch_data import get_stock_data
from .plot_data import plot_closing_prices
from .mongo_utils import store_in_mongo
from .vector_utils import create_embedding_and_store

__all__ = [
    "get_stock_data",
    "plot_closing_prices",
    "store_in_mongo",
    "create_embedding_and_store"
]
