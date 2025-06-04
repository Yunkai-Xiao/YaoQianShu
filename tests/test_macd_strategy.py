from __future__ import annotations

from pathlib import Path

from src import (
    DataStore,
    DataPortal,
    Engine,
    download_history,
    MACDStrategy,
)
from src.indicators import macd


def test_macd_strategy_with_real_data(tmp_path: Path):
    store = DataStore(tmp_path)
    df = download_history("AAPL", start="2020-01-01", end="2020-02-01", store=store)
    portal = DataPortal(store, ["AAPL"])
    portal.register_indicator("MACD", macd)
    strat = MACDStrategy("AAPL")
    engine = Engine(portal, strat, starting_cash=10000.0)
    results = engine.run()

    assert len(results) == len(df)
    assert "MACD" in portal._series["AAPL"].enhance().columns
