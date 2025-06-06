from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd

from src import DataStore, DataPortal, Engine, KDJStrategy
from src.indicators import kdj


def _write_sample_csv(root: Path, symbol: str, closes: List[float]):
    dates = pd.date_range("2020-01-01", periods=len(closes), freq="D")
    df = pd.DataFrame(
        {
            "Open": closes,
            "High": [c + 1 for c in closes],
            "Low": [c - 1 for c in closes],
            "Close": closes,
            "Adj Close": closes,
            "Volume": 1000,
        },
        index=dates,
    )
    df.to_csv(root / f"{symbol}.csv", date_format="%Y-%m-%d")


def test_kdj_strategy(tmp_path: Path):
    closes = [float(i) for i in range(1, 20)]
    _write_sample_csv(tmp_path, "XXX", closes)
    store = DataStore(tmp_path)
    portal = DataPortal(store, ["XXX"])
    portal.register_indicator("KDJ", kdj)
    strat = KDJStrategy("XXX")
    engine = Engine(portal, strat, starting_cash=1000.0)
    results = engine.run()

    assert len(results) == len(closes)
    df = portal._series["XXX"].enhance()
    assert {"K", "D", "J"}.issubset(df.columns)
