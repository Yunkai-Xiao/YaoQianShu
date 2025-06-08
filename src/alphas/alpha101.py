"""Partial implementation of the 101 Alpha formulas.

Only a small subset of formulas is implemented to illustrate the
framework. New formulas can be added easily by extending the
``ALPHAS`` mapping.
"""
from __future__ import annotations

from typing import Callable, Dict

import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# Helper functions used by some formulas
# ---------------------------------------------------------------------------
def ts_rank(series: pd.Series, window: int) -> pd.Series:
    """Time-series rank of the last value within ``window`` bars."""
    return (
        series.rolling(window)
        .apply(lambda x: pd.Series(x).rank().iloc[-1], raw=False)
    )


def ts_sum(series: pd.Series, window: int) -> pd.Series:
    """Rolling sum."""
    return series.rolling(window).sum()


def ts_min(series: pd.Series, window: int) -> pd.Series:
    """Rolling minimum."""
    return series.rolling(window).min()


def ts_max(series: pd.Series, window: int) -> pd.Series:
    """Rolling maximum."""
    return series.rolling(window).max()


def delay(series: pd.Series, period: int) -> pd.Series:
    """Lagged series."""
    return series.shift(period)


def rank(series: pd.Series) -> pd.Series:
    """Cross-sectional rank."""
    return series.rank(pct=True)


def sma(series: pd.Series, window: int) -> pd.Series:
    """Simple moving average."""
    return series.rolling(window).mean()

def delta(series: pd.Series, period: int = 1) -> pd.Series:
    """Difference over ``period`` bars."""
    return series.diff(period)


def correlation(x: pd.Series, y: pd.Series, window: int) -> pd.Series:
    return x.rolling(window).corr(y)

# ---------------------------------------------------------------------------
# Alpha formulas
# ---------------------------------------------------------------------------

def alpha001(df: pd.DataFrame) -> pd.Series:
    """Simple momentum of close price."""
    close = df["Close"]
    return (close - close.shift(1)) / close.shift(1)


def alpha002(df: pd.DataFrame) -> pd.Series:
    """Intraday return ranked as percentile."""
    ret = (df["Close"] - df["Open"]) / df["Open"]
    return ret.rank(pct=True)


def alpha003(df: pd.DataFrame) -> pd.Series:
    """Negative correlation between high and volume."""
    corr = correlation(df["High"], df["Volume"], 10)
    return -corr.rank(pct=True)


def alpha004(df: pd.DataFrame) -> pd.Series:
    """Negative time-series rank of Low."""
    return -ts_rank(rank(df["Low"]), 9)


def alpha005(df: pd.DataFrame) -> pd.Series:
    """Open minus average VWAP times negative abs rank of close-VWAP."""
    part1 = rank(df["Open"] - ts_sum(df["VWAP"], 10) / 10)
    part2 = -abs(rank(df["Close"] - df["VWAP"]))
    return part1 * part2


def alpha006(df: pd.DataFrame) -> pd.Series:
    """Negative correlation between open and volume."""
    corr = correlation(df["Open"], df["Volume"], 10)
    return -corr


def alpha007(df: pd.DataFrame) -> pd.Series:
    """Volume spike momentum with 20-day average filter."""
    adv20 = sma(df["Volume"], 20)
    core = -ts_rank(abs(delta(df["Close"], 7)), 60) * np.sign(delta(df["Close"], 7))
    result = core.where(adv20 < df["Volume"], -1.0)
    return result


def alpha008(df: pd.DataFrame) -> pd.Series:
    """Ranked change in price/return interaction."""
    sum_open = ts_sum(df["Open"], 5)
    sum_ret = ts_sum(df["Close"].pct_change(), 5)
    delayed = delay(sum_open * sum_ret, 10)
    return -rank((sum_open * sum_ret) - delayed)


def alpha009(df: pd.DataFrame) -> pd.Series:
    """Conditional momentum/reversal of close."""
    d_close = delta(df["Close"], 1)
    cond1 = ts_min(d_close, 5) > 0
    cond2 = ts_max(d_close, 5) < 0
    result = -d_close
    result[cond1 | cond2] = d_close
    return result


def alpha010(df: pd.DataFrame) -> pd.Series:
    """Similar to alpha009 but using 4-day window."""
    d_close = delta(df["Close"], 1)
    cond1 = ts_min(d_close, 4) > 0
    cond2 = ts_max(d_close, 4) < 0
    result = -d_close
    result[cond1 | cond2] = d_close
    return rank(result)

ALPHAS: Dict[str, Callable[[pd.DataFrame], pd.Series]] = {
    "alpha001": alpha001,
    "alpha002": alpha002,
    "alpha003": alpha003,
    "alpha004": alpha004,
    "alpha005": alpha005,
    "alpha006": alpha006,
    "alpha007": alpha007,
    "alpha008": alpha008,
    "alpha009": alpha009,
    "alpha010": alpha010,
}


def compute_alpha(df: pd.DataFrame, name: str) -> pd.Series:
    """Compute a single alpha series by name."""
    func = ALPHAS.get(name)
    if func is None:
        raise NotImplementedError(f"{name} not implemented")
    return func(df)

__all__ = ["compute_alpha", "ALPHAS"]
