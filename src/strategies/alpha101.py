from __future__ import annotations

from typing import Dict

import pandas as pd

from ..strategy import Strategy
from ..alphas.alpha101 import ALPHAS


class Alpha101Strategy(Strategy):
    """Example strategy using a combination of Alpha101 signals."""

    def __init__(self, symbol: str) -> None:
        self.symbol = symbol
        self.history = pd.DataFrame()

    def on_bar(
        self,
        engine: "Engine",
        timestamp: pd.Timestamp,
        data: Dict[str, pd.Series],
    ) -> None:
        row = data[self.symbol]
        self.history = pd.concat([self.history, row.to_frame().T])
        scores = []
        for name, func in ALPHAS.items():
            try:
                series = func(self.history)
                value = series.iloc[-1]
                if pd.notna(value):
                    scores.append(float(value))
            except Exception:
                continue
        if not scores:
            return
        score = sum(scores)
        if score > 0:
            engine.buy(self.symbol, 1)
        elif score < 0:
            engine.sell(self.symbol, 1)


__all__ = ["Alpha101Strategy"]
