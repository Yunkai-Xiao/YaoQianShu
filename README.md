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
pip install pandas pyarrow
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
