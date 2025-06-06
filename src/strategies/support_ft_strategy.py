from __future__ import annotations

from typing import Dict
import pandas as pd
import numpy as np

from src.engine import Engine

from ..strategy import Strategy


class SupportFTStrategy(Strategy):
    """Simplified version of the complex freqtrade strategy.

    Parameters
    ----------
    symbol: str
        Trading symbol.
    trade_qty: int, optional
        Number of shares to trade per action when `trade_pct` is None.
    trade_pct: float | None, optional
        If provided, portion of portfolio value to use for each trade.
    """

    def __init__(self, symbol: str, trade_qty: int = 10, trade_pct: float | None = None) -> None:
        self.symbol = symbol
        self.trade_qty = trade_qty
        self.trade_pct = trade_pct
        self.history = pd.DataFrame()
        self.in_position = False

    # ------------------------------------------------------------------
    def _rsi(self, series: pd.Series, period: int) -> float:
        if len(series) < period + 1:
            return float("nan")
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
        prev = series.iloc[-length]
        if prev == 0:
            return 0.0
        return (series.iloc[-1] - prev) / prev

    def _ewo(self, df: pd.DataFrame, ema1: int = 50, ema2: int = 200) -> float:
        close = df["Close"]
        low = df["Low"]
        if len(close) < ema2:
            return 0.0
        ema_fast = close.ewm(span=ema1, adjust=False).mean().iloc[-1]
        ema_slow = close.ewm(span=ema2, adjust=False).mean().iloc[-1]
        return (ema_fast - ema_slow) / low.iloc[-1] * 100

    def _fisher(self, rsi: float) -> float:
        x = 0.1 * (rsi - 50)
        return (np.exp(2 * x) - 1) / (np.exp(2 * x) + 1)

    def _trade_qty(self, engine: "Engine", price: float) -> int:
        """Determine quantity based on settings."""
        if self.trade_pct is not None:
            portfolio_val = engine.portfolio.value(engine._current_bar)
            qty = int((portfolio_val * self.trade_pct) / price)
            print(max(qty, 1))
            return max(qty, 1)
        return self.trade_qty

    # ------------------------------------------------------------------
    def on_bar(
        self,
        engine: Engine,
        timestamp: pd.Timestamp,
        data: Dict[str, pd.Series],
    ) -> None:
        row = data[self.symbol]
        self.history = pd.concat([self.history, row.to_frame().T])
        df = self.history

        close = df["Close"]
        rsi = self._rsi(close, 14)
        rsi_fast = self._rsi(close, 4)
        ema16 = self._ema(close, 16)
        ema26 = self._ema(close, 26)
        ema12 = self._ema(close, 12)
        cti = self._cti(close)
        ewo = self._ewo(df)

        # simplified Bollinger lower band
        if len(close) >= 20:
            mid = close.rolling(20).mean().iloc[-1]
            std = close.rolling(20).std().iloc[-1]
            bb_lower = mid - 2 * std
        else:
            mid = close.mean()
            std = close.std(ddof=0)
            bb_lower = mid - 2 * std

        buy_dip = (
            row["Close"] < ema16 * 0.982
            and ewo < -10.0
            and cti < -0.9
            and rsi < 35
        )

        buy_uptrend = (
            ema26 > ema12
            and (ema26 - ema12) > row["Open"] * 0.025
            and row["Close"] < bb_lower
        )

        if not self.in_position and (buy_dip or buy_uptrend):
            qty = self._trade_qty(engine, row["Close"])
            engine.buy(self.symbol, qty)
            self.in_position = True
        elif self.in_position:
            fisher = self._fisher(rsi)
            if fisher > 0.4 or rsi_fast > 70:
                qty = self._trade_qty(engine, row["Close"])
                owned = engine.portfolio.positions.get(self.symbol, 0)
                qty = min(qty, owned)
                engine.sell(self.symbol, qty)
                if engine.portfolio.positions.get(self.symbol, 0) == 0:
                    self.in_position = False


__all__ = ["SupportFTStrategy"]


