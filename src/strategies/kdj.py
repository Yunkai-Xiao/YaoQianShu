from __future__ import annotations

from typing import Dict

import pandas as pd

from ..strategy import Strategy


class KDJStrategy(Strategy):
    """Trading strategy using the KDJ indicator with SMA exits and ATR stop."""

    def __init__(
        self,
        symbol: str,
        sma_window: int = 60,
        atr_window: int = 9,
        stop_mult: float = 2.0,
    ) -> None:
        self.symbol = symbol
        self.sma_window = sma_window
        self.atr_window = atr_window
        self.stop_mult = stop_mult
        self.prev_k: float | None = None
        self.prev_d: float | None = None
        self.in_position = False
        self.entry_price: float | None = None
        self.history = pd.DataFrame()

    def on_bar(
        self,
        engine: "Engine",
        timestamp: pd.Timestamp,
        data: Dict[str, pd.Series],
    ) -> None:
        row = data[self.symbol]
        self.history = pd.concat([self.history, row.to_frame().T])
        k = row.get("K")
        d = row.get("D")
        j = row.get("J")
        if k is None or d is None or j is None:
            return
        close = row["Close"]
        sma = self.history["Close"].rolling(self.sma_window).mean().iloc[-1]
        sma60 = self.history["Close"].rolling(20).mean().iloc[-1]

        high = self.history["High"]
        low = self.history["Low"]
        prev_close = self.history["Close"].shift()
        tr = pd.concat(
            [high - low, (high - prev_close).abs(), (low - prev_close).abs()],
            axis=1,
        ).max(axis=1)
        atr = tr.rolling(self.atr_window).mean().iloc[-1]

        if self.prev_k is not None and self.prev_d is not None:
            if (
                # self.prev_k < self.prev_d
                # and k > d
                # and j < 20
                close > sma60
                and sma60 > sma
                and j < 20
                and not self.in_position
            ):
                engine.buy(self.symbol, 50)
                self.in_position = True
                self.entry_price = float(close)
            elif self.in_position:
                stop = (
                    self.entry_price - self.stop_mult * atr
                    if self.entry_price is not None and not pd.isna(atr)
                    else None
                )
                if close < sma or (stop is not None and close <= stop):
                    engine.sell(self.symbol, 50)
                    self.in_position = False
                    self.entry_price = None
        self.prev_k = k
        self.prev_d = d


__all__ = ["KDJStrategy"]
