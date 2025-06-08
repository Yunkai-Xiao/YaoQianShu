from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd

from src import DataStore, DataPortal, Engine, AlphaWeightStrategy


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


def test_alpha_weight_strategy(tmp_path: Path):
    _write_sample_csv(tmp_path, "AAA", [1, 2, 3])
    _write_sample_csv(tmp_path, "BBB", [1, 1, 1])
    store = DataStore(tmp_path)
    portal = DataPortal(store, ["AAA", "BBB"])
    strat = AlphaWeightStrategy(["AAA", "BBB"], alpha_name="alpha001")
    engine = Engine(portal, strat, starting_cash=90.0)
    results = engine.run()

    # After full run, portfolio should be fully invested with non-zero positions
    assert engine.portfolio.positions["AAA"] > 0
    assert engine.portfolio.positions["BBB"] > 0
    assert len(results) == 3
