"""Basic technical indicator functions."""

from __future__ import annotations

import pandas as pd


def volume(df: pd.DataFrame) -> pd.Series:
    """Return the traded volume."""
    return df["Volume"]


def sma(df: pd.DataFrame, window: int = 10) -> pd.Series:
    """Simple moving average of closing price."""
    return df["Close"].rolling(window).mean()


def ema(df: pd.DataFrame, window: int = 10) -> pd.Series:
    """Exponential moving average of closing price."""
    return df["Close"].ewm(span=window, adjust=False).mean()


def macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    """MACD indicator as DataFrame with columns MACD, Signal, Hist."""
    fast_ema = df["Close"].ewm(span=fast, adjust=False).mean()
    slow_ema = df["Close"].ewm(span=slow, adjust=False).mean()
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return pd.DataFrame({"MACD": macd_line, "Signal": signal_line, "Hist": hist})


def kdj(
    df: pd.DataFrame,
    n: int = 9,
    k_period: int = 3,
    d_period: int = 3,
) -> pd.DataFrame:
    """KDJ indicator with columns K, D, J."""
    low_n = df["Low"].rolling(n).min()
    high_n = df["High"].rolling(n).max()
    rsv = (df["Close"] - low_n) / (high_n - low_n) * 100
    k = rsv.ewm(com=k_period - 1, adjust=False).mean()
    d = k.ewm(com=d_period - 1, adjust=False).mean()
    j = 3 * k - 2 * d
    return pd.DataFrame({"K": k, "D": d, "J": j})


def atr(df: pd.DataFrame, window: int = 9) -> pd.Series:
    """Average True Range."""
    high_low = df["High"] - df["Low"]
    high_close = (df["High"] - df["Close"].shift()).abs()
    low_close = (df["Low"] - df["Close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(window).mean()


__all__ = ["volume", "sma", "ema", "macd", "kdj", "atr"]
