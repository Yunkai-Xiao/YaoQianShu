from __future__ import annotations

from pathlib import Path
import pandas as pd

from src import DataStore, DataPortal, Engine, analyze
from src.strategies import SupportFTStrategy


def main() -> None:
    store = DataStore(Path("market_data"))
    portal = DataPortal(store, ["NVDA"])
    # trade 5%% of portfolio each trade
    strategy = SupportFTStrategy("NVDA", trade_pct=0.5)
    engine = Engine(portal, strategy, starting_cash=10_000_000.0)
    results = engine.run(start=pd.Timestamp("2000-01-01"), end=pd.Timestamp("2016-01-01"))
    report = analyze(results)
    print(report)


if __name__ == "__main__":
    main()
