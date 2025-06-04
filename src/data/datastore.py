"""Datastore & DataPortal – core read‑only access layer."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Tuple

import pandas as pd

from .series import DataSeries
logger = logging.getLogger(__name__)

###############################################################################

# DataStore – on‑disk Parquet/CSV with LRU in‑memory cache

###############################################################################


class DataStore:
    """
    Simple file‑system backed OHLCV store.

    Notes
    -----
    * Stores one file per *symbol* (``<SYMBOL>.parquet`` or ``.csv``).
    * Keeps up to ``cache_size`` DataFrames in RAM; evicts FIFO beyond that.
    """

    def __init__(self, root: str | Path, *, cache_size: Optional[int] = 5):
        self.root = Path(root).expanduser().resolve()
        self.cache_size = cache_size
        self._cache: Dict[str, pd.DataFrame] = {}
        logger.debug("DataStore @ %s (cache=%s)", self.root, cache_size)

    # ------------------------------ public API ----------------------------

    def load(self, symbol: str, *, reload: bool = False) -> pd.DataFrame:
        key = symbol.upper()
        if reload or key not in self._cache:
            df = self._read_file(self._resolve_path(key))
            self._insert_cache(key, df)
        return self._cache[key]

    # ---------------------------- private helpers ------------------------

    def _resolve_path(self, symbol: str) -> Path:
        for ext in (".parquet", ".csv"):
            p = self.root / f"{symbol}{ext}"
            if p.exists():
                return p
        raise FileNotFoundError(f"Data for {symbol} not found in {self.root}")

    @staticmethod
    def _read_file(path: Path) -> pd.DataFrame:
        if path.suffix == ".parquet":
            df = pd.read_parquet(path)
        elif path.suffix == ".csv":
            df = pd.read_csv(path, index_col=0, parse_dates=[0])
        else:
            raise ValueError(f"Unsupported file type: {path.suffix}")
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("Index must be DatetimeIndex")
        df.sort_index(inplace=True)
        return df

    def _insert_cache(self, key: str, df: pd.DataFrame):
        # FIFO eviction
        if self.cache_size is not None and len(self._cache) >= self.cache_size:
            oldest = next(iter(self._cache))
            logger.debug("Cache full – evicting %s", oldest)
            self._cache.pop(oldest)
        self._cache[key] = df


###############################################################################

# DataPortal – yields aligned bars to the engine

###############################################################################


@dataclass
class DataPortal:
    datastore: DataStore
    symbols: List[str]
    _index: pd.DatetimeIndex = field(init=False, repr=False)
    _series: Dict[str, DataSeries] = field(init=False, repr=False)

    def __post_init__(self):
        self._series = {
            sym: DataSeries(self.datastore.load(sym)) for sym in self.symbols
        }
        self._index = self._series[self.symbols[0]].data.index
        logger.debug("DataPortal created with %d bars", len(self._index))

    # ------------------------------------------------------------------
    def register_indicator(
        self,
        name: str,
        func: Callable[[pd.DataFrame], pd.Series | pd.DataFrame],
        symbols: Optional[List[str]] = None,
    ) -> None:
        for sym in symbols or self.symbols:
            self._series[sym].register_indicator(name, func)

    def unregister_indicator(self, name: str, symbols: Optional[List[str]] = None) -> None:
        for sym in symbols or self.symbols:
            self._series[sym].unregister_indicator(name)

    # --------------------------------------------------------------------
    def iter_bars(
        self,
        *,
        start: Optional[pd.Timestamp] = None,
        end: Optional[pd.Timestamp] = None,
    ) -> Iterable[Tuple[pd.Timestamp, Dict[str, pd.Series]]]:
        enhanced = {sym: ds.enhance() for sym, ds in self._series.items()}
        for ts in self._index:
            if start and ts < start:
                continue
            if end and ts > end:
                break
            yield ts, {sym: self._select_row(enhanced[sym], ts, sym) for sym in self.symbols}

    def get_bar(self, ts: pd.Timestamp, symbol: str):
        return self._select_row(self._series[symbol].enhance(), ts, symbol)

    # ------------------------------------------------------------------
    @staticmethod
    def _select_row(df: pd.DataFrame, ts: pd.Timestamp, symbol: str) -> pd.Series:
        row = df.loc[ts]
        if isinstance(row.index, pd.MultiIndex):
            for level in range(row.index.nlevels):
                if symbol in row.index.get_level_values(level):
                    return row.xs(symbol, level=level)
        return row
