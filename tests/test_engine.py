from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd
import pytest

from src import DataPortal, DataStore, Engine, Strategy


def _write_sample_csv(root: Path, symbol: str, closes: List[float]):
    dates = pd.date_range("2020-01-01", periods=len(closes), freq="D")
    df = pd.DataFrame(
        {
            "Open": closes,
            "High": [c * 1.02 for c in closes],
            "Low": [c * 0.98 for c in closes],
            "Close": closes,
            "Adj Close": closes,
            "Volume": 1000,
        },
        index=dates,
    )
    df.to_csv(root / f"{symbol}.csv", date_format="%Y-%m-%d")


class BuyOnceStrategy(Strategy):
    def __init__(self):
        self.done = False

    def on_bar(self, engine: Engine, timestamp: pd.Timestamp, data: Dict[str, pd.Series]) -> None:
        if not self.done:
            for sym in data.keys():
                engine.buy(sym, 1)
            self.done = True


def test_engine_buy_and_hold(tmp_path: Path):
    _write_sample_csv(tmp_path, "AAA", [1.0, 2.0, 3.0])
    store = DataStore(tmp_path)
    portal = DataPortal(store, ["AAA"])
    strat = BuyOnceStrategy()
    engine = Engine(portal, strat, starting_cash=10.0)
    results = engine.run()

    assert len(results) == 3
    # After first bar we spent 1 at price 1
    assert engine.portfolio.positions["AAA"] == 1
    assert pytest.approx(engine.portfolio.cash, rel=1e-6) == 9.0

    final_value = results.iloc[-1]["value"]
    assert pytest.approx(final_value, rel=1e-6) == 12.0
