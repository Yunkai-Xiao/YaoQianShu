"""Unit tests for backtester.data package.

Run with ``pytest -q`` at repository root. The tests use the built‑in
``tmp_path`` fixture to create a throwaway data directory, so they do not
require network access or modify your real market data folder.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import List

import pandas as pd
import pytest

# Import the module under test – adjust import path as needed.
from src.data import DataStore, DataPortal

###############################################################################
# Helpers
###############################################################################

def _write_sample_csv(root: Path, symbol: str, closes: List[float]):
    dates = pd.date_range("2020-01-01", periods=len(closes), freq="D")
    df = pd.DataFrame({
        "Open": closes,
        "High": [c * 1.02 for c in closes],
        "Low": [c * 0.98 for c in closes],
        "Close": closes,
        "Adj Close": closes,
        "Volume": 1000,
    }, index=dates)
    df.to_csv(root / f"{symbol}.csv", date_format="%Y-%m-%d")

###############################################################################
# Test cases
###############################################################################

def test_datastore_load_and_cache(tmp_path: Path):
    """DataStore loads CSV and caches up to *cache_size* symbols."""
    _write_sample_csv(tmp_path, "AAA", [10.0, 10.5, 10.3])
    _write_sample_csv(tmp_path, "BBB", [20.0, 20.5, 21.0])

    store = DataStore(tmp_path, cache_size=1)

    # First load should read from disk
    df_a = store.load("AAA")
    assert len(df_a) == 3
    assert store._cache.keys() == {"AAA"}

    # Loading another symbol should evict the first (cache_size=1)
    _ = store.load("BBB")
    assert store._cache.keys() == {"BBB"}


def test_datastore_missing_symbol(tmp_path: Path):
    """Loading a non‑existent symbol raises FileNotFoundError."""
    store = DataStore(tmp_path)
    with pytest.raises(FileNotFoundError):
        store.load("MISSING")


def test_data_portal_iteration(tmp_path: Path):
    """DataPortal.iter_bars yields aligned bars across multiple symbols."""
    _write_sample_csv(tmp_path, "AAA", [1, 2, 3])
    _write_sample_csv(tmp_path, "BBB", [4, 5, 6])

    store = DataStore(tmp_path)
    portal = DataPortal(store, ["AAA", "BBB"])

    bars = list(portal.iter_bars())
    assert len(bars) == 3  # three days

    # Check first day contents
    ts, bar_dict = bars[0]
    assert {"AAA", "BBB"} == set(bar_dict)
    assert bar_dict["AAA"]["Close"] == 1
    assert bar_dict["BBB"]["Close"] == 4


def test_data_portal_get_bar(tmp_path: Path):
    """DataPortal.get_bar returns the Series for a single symbol/date."""
    _write_sample_csv(tmp_path, "ZZZ", [9.9, 10.1])
    store = DataStore(tmp_path)
    portal = DataPortal(store, ["ZZZ"])

    dt = pd.Timestamp(year=2020, month=1, day=2)
    series = portal.get_bar(dt, "ZZZ")
    assert pytest.approx(series["Close"], rel=1e-6) == 10.1


def test_datastore_list_symbols(tmp_path: Path):
    """list_symbols returns sorted symbol names from disk."""
    _write_sample_csv(tmp_path, "CCC", [1, 2])
    _write_sample_csv(tmp_path, "AAA", [1, 2])
    store = DataStore(tmp_path)
    assert store.list_symbols() == ["AAA", "CCC"]

###############################################################################
# Clean‑up utility (optional) – ensure tmp dirs removed on Windows
###############################################################################

def teardown_module(module):  # noqa: D401 – pytest hook
    pass
