"""DataSeries holding price data and calculating indicators."""
from __future__ import annotations

from typing import Callable, Dict, Optional

import pandas as pd


class DataSeries:
    def __init__(self, data: pd.DataFrame) -> None:
        if not isinstance(data.index, pd.DatetimeIndex):
            raise ValueError("Index must be DatetimeIndex")
        self.data = data.sort_index().copy()
        self._indicators: Dict[str, Callable[[pd.DataFrame], pd.Series | pd.DataFrame]] = {}
        self._cache: Optional[pd.DataFrame] = None

    # ------------------------------------------------------------------
    def register_indicator(
        self, name: str, func: Callable[[pd.DataFrame], pd.Series | pd.DataFrame]
    ) -> None:
        self._indicators[name] = func
        self._cache = None

    def unregister_indicator(self, name: str) -> None:
        self._indicators.pop(name, None)
        self._cache = None

    # ------------------------------------------------------------------
    def enhance(self) -> pd.DataFrame:
        if self._cache is not None:
            return self._cache
        df = self.data.copy()
        for name, func in self._indicators.items():
            result = func(df)
            if isinstance(result, pd.Series):
                df[name] = result
            else:
                for col in result.columns:
                    df[col] = result[col]
        self._cache = df
        return df
