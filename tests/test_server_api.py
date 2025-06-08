from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd
from fastapi.testclient import TestClient

from src import DataStore
import src.server as server


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


def test_symbols_endpoint(tmp_path, monkeypatch):
    _write_sample_csv(tmp_path, "AAA", [1, 2])
    _write_sample_csv(tmp_path, "BBB", [3, 4])

    ds = DataStore(tmp_path)
    monkeypatch.setattr(server, "store", ds)
    monkeypatch.setattr(server, "DATA_ROOT", Path(tmp_path))
    server._PORTALS.clear()

    client = TestClient(server.app)
    resp = client.get("/symbols")
    assert resp.status_code == 200
    assert resp.json() == {"symbols": ["AAA", "BBB"]}


def test_backtest_multiple_symbols(tmp_path, monkeypatch):
    _write_sample_csv(tmp_path, "AAA", [1, 2, 3])
    _write_sample_csv(tmp_path, "BBB", [1, 1, 1])

    ds = DataStore(tmp_path)
    monkeypatch.setattr(server, "store", ds)
    monkeypatch.setattr(server, "DATA_ROOT", Path(tmp_path))
    server._PORTALS.clear()
    server.refresh_strategies()

    client = TestClient(server.app)
    resp = client.post(
        "/backtest",
        json={"symbols": ["AAA", "BBB"], "strategy": "AlphaWeightStrategy"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["history"]) == 3
