from __future__ import annotations

from pathlib import Path

import pandas as pd
from src import DataStore, DataPortal, Engine
from src.strategies import FriendStrategy
from src.analysis import analyze


def main() -> None:
    store = DataStore(Path("market_data"))
    portal = DataPortal(store, ["SPY"])
    strategy = FriendStrategy("SPY")
    engine = Engine(portal, strategy, starting_cash=10_000.0)
    # Limit to one year of data to keep the example fast
    results = engine.run(start=pd.Timestamp("2015-01-01"), end=pd.Timestamp("2016-01-01"))
    report = analyze(results)
    print(report)


if __name__ == "__main__":
    main()
