from __future__ import annotations

from typing import Dict
import pandas as pd

from ..strategy import Strategy


class MACDStrategy(Strategy):
    """Buy when MACD crosses above signal, sell on opposite cross."""

    def __init__(self, symbol: str) -> None:
        self.symbol = symbol
        self.prev_macd: float | None = None
        self.prev_signal: float | None = None
        self.in_position = False

    def on_bar(
        self,
        engine: "Engine",
        timestamp: pd.Timestamp,
        data: Dict[str, pd.Series],
    ) -> None:
        row = data[self.symbol]
        macd = row.get("MACD")
        signal = row.get("Signal")
        if macd is None or signal is None:
            return
        if self.prev_macd is not None and self.prev_signal is not None:
            if self.prev_macd < self.prev_signal and macd > signal and not self.in_position:
                engine.buy(self.symbol, 1)
                self.in_position = True
            elif self.prev_macd > self.prev_signal and macd < signal and self.in_position:
                engine.sell(self.symbol, 1)
                self.in_position = False
        self.prev_macd = macd
        self.prev_signal = signal
