from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd

from src import DataStore, DataPortal, Engine
from src.strategies import PullbackStrategy


def _write_sample_csv(root: Path, symbol: str, closes: List[float]):
    dates = pd.date_range("2020-01-01", periods=len(closes), freq="D")
    df = pd.DataFrame(
        {
            "Open": closes,
            "High": closes,
            "Low": closes,
            "Close": closes,
            "Adj Close": closes,
            "Volume": 1000,
        },
        index=dates,
    )
    df.to_csv(root / f"{symbol}.csv", date_format="%Y-%m-%d")


def test_pullback_strategy(tmp_path: Path):
    closes = [100, 102, 98, 97, 104, 98, 110]
    _write_sample_csv(tmp_path, "XXX", closes)
    store = DataStore(tmp_path)
    portal = DataPortal(store, ["XXX"])
    strat = PullbackStrategy(
        "XXX",
        buy_threshold=0.03,
        sell_threshold=0.04,
        trade_qty=10,
        sell_pct=0.5,
    )
    engine = Engine(portal, strat, starting_cash=10000.0)
    results = engine.run()

    assert len(engine.trades) == 4
    assert engine.portfolio.positions["XXX"] == 8
    final_value = results["value"].iloc[-1]
    assert final_value > 10000.0
