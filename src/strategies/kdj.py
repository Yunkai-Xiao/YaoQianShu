from __future__ import annotations

from typing import Dict

import pandas as pd

from ..strategy import Strategy


class KDJStrategy(Strategy):
    """Trading strategy using the KDJ indicator."""

    def __init__(self, symbol: str) -> None:
        self.symbol = symbol
        self.prev_k: float | None = None
        self.prev_d: float | None = None
        self.in_position = False

    def on_bar(
        self,
        engine: "Engine",
        timestamp: pd.Timestamp,
        data: Dict[str, pd.Series],
    ) -> None:
        row = data[self.symbol]
        k = row.get("K")
        d = row.get("D")
        j = row.get("J")
        if k is None or d is None or j is None:
            return
        if self.prev_k is not None and self.prev_d is not None:
            if self.prev_k < self.prev_d and k > d and j < 20 and not self.in_position:
                engine.buy(self.symbol, 1)
                self.in_position = True
            elif self.prev_k > self.prev_d and k < d and j > 80 and self.in_position:
                engine.sell(self.symbol, 1)
                self.in_position = False
        self.prev_k = k
        self.prev_d = d


__all__ = ["KDJStrategy"]
