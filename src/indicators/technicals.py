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


__all__ = ["volume", "sma", "ema", "macd"]
