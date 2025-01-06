
from dotenv import load_dotenv
from data_pipeline.twelve_data import TwelveDataClient
from data_pipeline.mongodb_accessor import StockDataMongoDB
from data_pipeline.utils import load_symbols_from_json
from strategy.lstm import StockPricePredictor

load_dotenv()

mongo_accessor = StockDataMongoDB()

df = mongo_accessor.get_stock_data("AMZN")

# Initialize the predictor
predictor = StockPricePredictor(df, time_step=7)  # Using 3 for this small dataset; use 60 for real data

# Preprocess data
predictor.preprocess_data()

# Create datasets
X, y = predictor.create_datasets()

# Train and evaluate the model
predictor.train_and_evaluate(X, y, splits=3, epochs=1000)

# Example prediction using the most recent data
recent_data = predictor.df[predictor.feature_columns].values[-predictor.time_step:]
prediction = predictor.predict(recent_data)
movement = 'Upward' if prediction == 1 else 'Downward'
print(f"Predicted next day's movement: {movement}")
