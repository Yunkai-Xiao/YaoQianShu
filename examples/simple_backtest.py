from __future__ import annotations

from pathlib import Path

from src import DataStore, DataPortal, Engine, MovingAverageCrossStrategy
from src.analysis import analyze


def main() -> None:
    store = DataStore(Path("market_data"))
    portal = DataPortal(store, ["NVDA"])
    strategy = MovingAverageCrossStrategy("NVDA", short_window=120, long_window=180)
    engine = Engine(portal, strategy, starting_cash=10_000.0)
    results = engine.run()
    report = analyze(results)
    print(report)


if __name__ == "__main__":
    main()
