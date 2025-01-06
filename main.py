
from dotenv import load_dotenv
from data_pipeline.twelve_data import TwelveDataClient
from data_pipeline.mongodb_accessor import StockDataMongoDB
from data_pipeline.utils import load_symbols_from_json

load_dotenv()

client = TwelveDataClient()
mongo_accessor = StockDataMongoDB()

symbols = load_symbols_from_json("config/target_symbol.json")

for symbol in symbols:
    # Fetch real-time quote for Apple Inc.
    quote = client.get_quote(symbol)

    # History Data
    history_df = client.get_time_series(symbol, interval='1day', outputsize=5000)
    print(f"Stored symbol: {symbol}")
    print(history_df)

    mongo_accessor.insert_stock_data(symbol, history_df)

mongo_accessor.close_connection()