from __future__ import annotations

from typing import List, Dict

import pandas as pd

from ..strategy import Strategy


class MovingAverageCrossStrategy(Strategy):
    """Simple moving average crossover strategy for a single symbol."""

    def __init__(self, symbol: str, short_window: int = 20, long_window: int = 50) -> None:
        if short_window >= long_window:
            raise ValueError("short_window must be less than long_window")
        self.symbol = symbol
        self.short_window = short_window
        self.long_window = long_window
        self.prices: List[float] = []
        self.in_position = False

    def on_bar(
        self,
        engine: "Engine",
        timestamp: pd.Timestamp,
        data: Dict[str, pd.Series],
    ) -> None:
        price = data[self.symbol]["Close"]
        self.prices.append(price)
        if len(self.prices) < self.long_window:
            return

        short_ma = pd.Series(self.prices[-self.short_window:]).mean()
        long_ma = pd.Series(self.prices[-self.long_window:]).mean()

        if short_ma > long_ma and not self.in_position:
            engine.buy(self.symbol, 1)
            self.in_position = True
        elif short_ma < long_ma and self.in_position:
            engine.sell(self.symbol, 1)
            self.in_position = False


__all__ = ["MovingAverageCrossStrategy"]
