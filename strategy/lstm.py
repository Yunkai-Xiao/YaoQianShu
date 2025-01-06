import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import TimeSeriesSplit
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import matplotlib.pyplot as plt
import ta  # Technical Analysis library

class StockPricePredictor:
    def __init__(self, dataframe, time_step=60):
        self.df = dataframe.copy()
        self.time_step = time_step
        self.model = None
        self.scaler = None
        self.feature_columns = []
        print("StockPricePredictor initialized.")

    def preprocess_data(self):
        # Ensure datetime is in datetime format and sorted
        self.df['datetime'] = pd.to_datetime(self.df['datetime'])
        self.df.sort_values('datetime', inplace=True)
        self.df.reset_index(drop=True, inplace=True)

        # Add technical indicators
        self.add_technical_indicators()

        # Create target variable for classification (1 for up, 0 for down)
        self.df['target'] = (self.df['close'].shift(-1) > self.df['close']).astype(int)

        # Drop the last row as it doesn't have a target
        self.df.dropna(inplace=True)

        # Select features for the model
        self.feature_columns = ['close', 'volume', 'RSI', 'MACD', 'MA50', 'MA200']
        self.df = self.df[self.feature_columns + ['target']]

        # Scale the features
        self.scaler = StandardScaler()
        self.df[self.feature_columns] = self.scaler.fit_transform(self.df[self.feature_columns])

        print("Data preprocessing completed.")

    def add_technical_indicators(self):
        # RSI
        self.df['RSI'] = ta.momentum.RSIIndicator(self.df['close']).rsi()

        # MACD
        macd = ta.trend.MACD(self.df['close'])
        self.df['MACD'] = macd.macd_diff()

        # Moving Averages
        self.df['MA50'] = self.df['close'].rolling(window=50).mean()
        self.df['MA200'] = self.df['close'].rolling(window=200).mean()

        # Fill NaN values
        self.df.fillna(method='bfill', inplace=True)

        print("Technical indicators added.")

    def create_datasets(self):
        X, y = [], []
        data = self.df[self.feature_columns].values
        targets = self.df['target'].values

        for i in range(self.time_step, len(data)):
            X.append(data[i - self.time_step:i])
            y.append(targets[i])

        X, y = np.array(X), np.array(y)
        print(f"Datasets created with {X.shape[0]} samples.")
        return X, y

    def build_model(self):
        self.model = Sequential()

        # First LSTM layer with 30 units and Dropout
        self.model.add(LSTM(40, return_sequences=True, input_shape=(self.time_step, len(self.feature_columns))))
        self.model.add(Dropout(0.2))

        # Second LSTM layer with 40 units and Dropout
        self.model.add(LSTM(50, return_sequences=True))
        self.model.add(Dropout(0.2))

        # Third LSTM layer with 50 units and Dropout
        self.model.add(LSTM(60, return_sequences=True))
        self.model.add(Dropout(0.2))

        # Fourth LSTM layer with 60 units (without return_sequences, as it's the last LSTM layer)
        self.model.add(LSTM(70))
        self.model.add(Dropout(0.2))

        # Dense layer for binary classification (using sigmoid activation)
        self.model.add(Dense(1, activation='sigmoid'))

        # Compile the model with the appropriate loss and optimizer
        self.model.compile(optimizer='adam', loss='mean_squared_error', metrics=['accuracy'])
        print("Model built with stacked LSTM layers.")

    def train_and_evaluate(self, X, y, splits=5, epochs=1000, batch_size=32):
        tscv = TimeSeriesSplit(n_splits=splits)
        accuracy_scores = []

        fold = 1
        for train_index, test_index in tscv.split(X):
            print(f"Training fold {fold}...")
            X_train, X_test = X[train_index], X[test_index]
            y_train, y_test = y[train_index], y[test_index]

            self.build_model()
            self.model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, verbose=0)

            # Evaluate
            y_pred = (self.model.predict(X_test) > 0.5).astype(int)
            acc = accuracy_score(y_test, y_pred)
            accuracy_scores.append(acc)
            print(f"Fold {fold} Accuracy: {acc * 100:.2f}%")
            fold += 1

        avg_accuracy = np.mean(accuracy_scores)
        print(f"Average Accuracy over {splits} folds: {avg_accuracy * 100:.2f}%")

    def predict(self, recent_data):
        """
        Predict the next day's movement (up/down).

        :param recent_data: numpy array of recent data with shape (time_step, num_features)
        """
        recent_data_scaled = self.scaler.transform(recent_data)
        recent_data_scaled = recent_data_scaled.reshape(1, self.time_step, len(self.feature_columns))
        prediction = (self.model.predict(recent_data_scaled) > 0.5).astype(int)
        return prediction[0][0]

    def plot_feature_importance(self):
        # Feature importance is not directly available for LSTM models.
        print("Feature importance is not directly available for LSTM models.")