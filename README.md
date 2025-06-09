# YaoQianShu


This repository includes a small backtesting framework. The key pieces are:

- `Strategy`: abstract base class. Implement `on_bar(engine, timestamp, data)`
  and use `engine.buy` / `engine.sell` inside.
- `Engine`: orchestrates a strategy over historical data from `DataPortal`.
- `DataPortal` / `DataStore`: load market data from CSV or Parquet files.

Below is a minimal example showing how to create a strategy and run it on
sample data.

## Install dependencies

```bash
pip install pandas pyarrow yfinance
```

## Example strategy

```python
from src import DataStore, DataPortal, Engine, Strategy, analyze
import pandas as pd

class BuyOnceStrategy(Strategy):
    def __init__(self):
        self.done = False

    def on_bar(self, engine, timestamp, data):
        if not self.done:
            engine.buy('AAA', 1)
            self.done = True
```

## Prepare data

Save a CSV file under a directory (for example `data/AAA.csv`) with columns
`Open`, `High`, `Low`, `Close`, `Adj Close` and `Volume`. The tests in this
repository use the following snippet:

```python
closes = [1.0, 2.0, 3.0]
df = pd.DataFrame({
    'Open': closes,
    'High': closes,
    'Low': closes,
    'Close': closes,
    'Adj Close': closes,
    'Volume': 1000,
}, index=pd.date_range('2020-01-01', periods=len(closes), freq='D'))
df.to_csv('data/AAA.csv', date_format='%Y-%m-%d')
```

## Run the backtest

```python
store = DataStore('data')
portal = DataPortal(store, ['AAA'])
strategy = BuyOnceStrategy()
engine = Engine(portal, strategy, starting_cash=10.0)
results = engine.run()
report = analyze(results)
print(results)
print(report)
```

Running the above code will print the portfolio value over time and a summary
statistics report.

## Fetch real data

You can download historical prices from Yahoo Finance using the bundled script:

```bash
PYTHONPATH=. python src/scripts/fetch_data.py --root market_data --symbols SPY --start 2020-01-01 --end 2020-02-01
```

This creates `market_data/SPY.parquet` (and a CSV fallback) which the example
backtest will consume.

## Run the moving average example

With data in place, execute the built-in moving average crossover strategy. You
can run the script directly or inspect `examples/simple_backtest.py` for a
minimal programmatic example:

```bash
PYTHONPATH=. python src/scripts/run_backtest.py --root market_data --symbol SPY --short 5 --long 20 --cash 10000
```

The script prints a `Report` object summarizing total return, annual return,
Sharpe ratio and maximum drawdown.

## FastAPI server

You can also interact with the backtester through a small REST API. Start the
server with:

```bash
uvicorn src.server:app --reload
```

Endpoints:

- `GET /data/{symbol}` – return OHLCV data for a symbol.
- `GET /symbols` – list available symbols on disk.
- `POST /fetch` – download new data via Yahoo Finance and store it.
- `GET /strategies` – discover available strategy classes.
- `POST /indicator` – register an indicator for subsequent backtests. Example:

```json
{"symbol": "SPY", "name": "sma", "params": {"window": 10}}
```

- `POST /backtest` – run a strategy and return the results. Example payload:

```json
{
  "symbol": "SPY",
  "strategy": "moving_average",
  "params": {"short_window": 5, "long_window": 20}
}
```

The response contains the trade history along with a performance report.

## Frontend UI

A small React interface is located under `frontend/black-dashboard-react-master`.
Install its dependencies (they are already checked in) and start the dev server:

```bash
cd frontend/black-dashboard-react-master
npm start
```

The React app communicates with the FastAPI service (running on
`localhost:8000`) and provides two tabs:

1. **Backtest** – select one or more symbols and a strategy, run a backtest and
   view price data, trade markers, portfolio equity and a small table of
   performance metrics. Hold Ctrl/Cmd to pick multiple symbols for portfolio
   strategies such as ``AlphaWeightStrategy``.
2. **Fetch Data** – download new symbols via Yahoo Finance and add them to the
   local datastore.
