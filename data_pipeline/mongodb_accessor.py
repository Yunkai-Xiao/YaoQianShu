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

    def get_stock_data(self, symbol):
        """
        Fetch all stock data for a given symbol from MongoDB.
        :param symbol: Stock symbol to fetch data for.
        :return: A pandas DataFrame containing the stock data.
        """
        # Query the collection for documents with the given symbol
        cursor = self.collection.find({"symbol": symbol})
        
        # Convert the cursor to a list of documents
        documents = list(cursor)
        
        # If documents are found, convert them to a DataFrame
        if documents:
            # Remove the '_id' field if not needed
            for doc in documents:
                doc.pop('_id', None)
            df = pd.DataFrame(documents)
            # Convert data types if necessary
            df['datetime'] = pd.to_datetime(df['datetime'])
            numeric_fields = ['open', 'high', 'low', 'close', 'volume']
            for field in numeric_fields:
                df[field] = pd.to_numeric(df[field], errors='coerce')
                
            df.drop_duplicates(subset='datetime', keep='first', inplace=True)
            # Sort by datetime
            df.sort_values('datetime', inplace=True)
            print(f"Fetched {len(df)} records for symbol '{symbol}'.")
            return df
        else:
            print(f"No records found for symbol '{symbol}'.")
            return pd.DataFrame()  # Return empty DataFrame if no records found

    def close_connection(self):
        """ Close MongoDB connection. """
        self.client.close()
        print("MongoDB connection closed.")
