"""External data acquisition helpers (Yahoo Finance, etc.)."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import pandas as pd

try:
    import yfinance as yf
except ImportError:  # pragma: no cover - optional dependency
    yf = None

from .datastore import DataStore

logger = logging.getLogger(__name__)

__all__ = ["download_history", "download_fundamentals"]


def download_history(
    symbol: str,
    *,
    start: str | pd.Timestamp = "2000-01-01",
    end: Optional[str | pd.Timestamp] = None,
    store: Optional[DataStore] = None,
    interval: str = "1h",
) -> pd.DataFrame:
    """Download daily OHLCV via Yahoo Finance and optionally save to DataStore."""
    if yf is None:
        raise ImportError("pip install yfinance to enable download_history")
    try:
        df = yf.download(symbol, start=start, end=end, progress=False, interval=interval)
    except Exception as exc:  # pragma: no cover - network errors
        logger.error("yfinance download failed: %s", exc)
        df = pd.DataFrame()
    if df.empty:
        # Fallback to daily interval when intraday data is unavailable
        if interval != "1d":
            df = yf.download(symbol, start=start, end=end, progress=False, interval="1d")
    if df.empty:
        raise ValueError(f"No data returned for {symbol}")
    df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ["_".join(map(str, c)) for c in df.columns]
    if any("_" in c for c in df.columns):
        df.columns = [c.split("_")[0] for c in df.columns]

    if store is not None:
        save_path = (Path(store.root) / f"{symbol.upper()}").with_suffix(".parquet")
        save_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            df.to_parquet(save_path)
        except Exception:  # Fallback to CSV when pyarrow is unavailable
            save_path = save_path.with_suffix(".csv")
            df.to_csv(save_path, date_format="%Y-%m-%d")
        logger.info("Saved %s rows for %s → %s", len(df), symbol, save_path)
    return df


def download_fundamentals(
    symbol: str,
    *,
    store: Optional[DataStore] = None,
) -> pd.DataFrame:
    """Fetch basic fundamental data using yfinance."""
    if yf is None:
        raise ImportError("pip install yfinance to enable download_fundamentals")
    ticker = yf.Ticker(symbol)
    info = ticker.get_info()
    df = pd.DataFrame([info])
    if store is not None:
        path = (Path(store.root) / f"{symbol.upper()}_fundamentals.csv")
        df.to_csv(path, index=False)
        logger.info("Saved fundamentals for %s → %s", symbol, path)
    return df
