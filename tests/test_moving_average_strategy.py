from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd
import pytest

from src import DataStore, DataPortal, Engine, MovingAverageCrossStrategy
from src.analysis import analyze


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


def test_moving_average_strategy(tmp_path: Path):
    closes = [1, 2, 3, 2, 1, 2, 3]
    _write_sample_csv(tmp_path, "XXX", closes)
    store = DataStore(tmp_path)
    portal = DataPortal(store, ["XXX"])
    strat = MovingAverageCrossStrategy("XXX", short_window=2, long_window=3)
    engine = Engine(portal, strat, starting_cash=100.0)
    results = engine.run()

    # Check final position and cash
    assert strat.in_position
    assert engine.portfolio.positions["XXX"] == 1
    assert pytest.approx(engine.portfolio.cash, rel=1e-6) == 95.0

    report = analyze(results)
    assert pytest.approx(report.final_value, rel=1e-6) == 98.0
    assert pytest.approx(report.total_return, rel=1e-6) == -0.02
    assert pytest.approx(report.max_drawdown, rel=1e-6) == -0.02
