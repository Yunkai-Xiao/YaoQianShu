import os
from pymongo import MongoClient

# 1. Connect to MongoDB

from pymongo import MongoClient
import pandas as pd

class StockDataMongoDB:
    def __init__(self, db_name="stock_data", collection_name="daily_prices"):
        pwd = os.getenv("MONGODB_PASSWORD")
        uri = f"mongodb+srv://yunkxiao:{pwd}@cluster0.w7avz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
        # Initialize MongoDB connection
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        print(f"Connected to MongoDB: {db_name}.{collection_name}")

    def insert_stock_data(self, symbol, data):
        """
        Insert stock market data into MongoDB.
        
        :param symbol: Stock symbol (e.g., "AAPL").
        :param data: A dictionary or DataFrame containing the stock data.
        """
        # Check if the input is a DataFrame, convert it to a list of dictionaries
        if isinstance(data, pd.DataFrame):
            data["symbol"] = symbol  # Add symbol column to DataFrame
            stock_data = data.to_dict(orient="records")
        elif isinstance(data, list):  # If already a list of dictionaries
            for item in data:
                item["symbol"] = symbol  # Add symbol to each record
            stock_data = data
        else:
            raise ValueError("Data should be a pandas DataFrame or a list of dictionaries")

        # Insert the data into MongoDB
        result = self.collection.insert_many(stock_data)
        print(f"Inserted {len(result.inserted_ids)} documents into MongoDB.")
    
    def close_connection(self):
        """ Close MongoDB connection. """
        self.client.close()
        print("MongoDB connection closed.")
