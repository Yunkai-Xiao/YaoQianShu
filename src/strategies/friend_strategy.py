from __future__ import annotations

from typing import Dict, List
import pandas as pd

from ..strategy import Strategy


class FriendStrategy(Strategy):
    """Simplified version of the example freqtrade strategy."""

    def __init__(self, symbol: str) -> None:
        self.symbol = symbol
        self.history = pd.DataFrame()
        self.in_position = False

    # ------------------------------------------------------------------
    def _rsi(self, series: pd.Series, period: int) -> float:
        if len(series) < period + 1:
            return float('nan')
        delta = series.diff().dropna()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.rolling(period).mean().iloc[-1]
        avg_loss = loss.rolling(period).mean().iloc[-1]
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def _ema(self, series: pd.Series, period: int) -> float:
        if len(series) < period:
            return series.iloc[-1]
        return series.ewm(span=period, adjust=False).mean().iloc[-1]

    def _sma(self, series: pd.Series, period: int) -> float:
        if len(series) < period:
            return series.mean()
        return series.rolling(period).mean().iloc[-1]

    def _cti(self, series: pd.Series, length: int = 20) -> float:
        if len(series) < length + 1:
            return 0.0
        return (series.iloc[-1] - series.iloc[-length]) / series.iloc[-length]

    def _ewo(self, df: pd.DataFrame, ema1: int = 50, ema2: int = 200) -> float:
        close = df['Close']
        low = df['Low']
        if len(close) < ema2:
            return 0.0
        ema_fast = close.ewm(span=ema1, adjust=False).mean().iloc[-1]
        ema_slow = close.ewm(span=ema2, adjust=False).mean().iloc[-1]
        return (ema_fast - ema_slow) / low.iloc[-1] * 100

    # ------------------------------------------------------------------
    def on_bar(
        self,
        engine: "Engine",
        timestamp: pd.Timestamp,
        data: Dict[str, pd.Series],
    ) -> None:
        row = data[self.symbol]
        self.history = pd.concat([self.history, row.to_frame().T])
        df = self.history

        close = df['Close']
        rsi = self._rsi(close, 14)
        rsi_fast = self._rsi(close, 4)
        rsi_slow = self._rsi(close, 20)
        ema8 = self._ema(close, 8)
        ema16 = self._ema(close, 16)
        sma15 = self._sma(close, 15)
        cti = self._cti(close, 20)
        ewo = self._ewo(df)

        buy_ewo = (
            rsi_fast < 50
            and row['Close'] < ema8 * 0.956
            and ewo > -1.238
            and row['Close'] < ema16 * 0.986
            and rsi < 30
        )

        buy_1 = (
            rsi_slow < self._rsi(close[:-1], 20)
            and rsi_fast < 63
            and rsi > 16
            and row['Close'] < sma15 * 0.932
            and cti < -0.8
        )

        if not self.in_position and (buy_ewo or buy_1):
            engine.buy(self.symbol, 1)
            self.in_position = True
        elif self.in_position and rsi_fast > 70:
            engine.sell(self.symbol, 1)
            self.in_position = False


__all__ = ["FriendStrategy"]
