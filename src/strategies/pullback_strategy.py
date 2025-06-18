from __future__ import annotations

from typing import Dict

import pandas as pd

from ..strategy import Strategy


class PullbackStrategy(Strategy):
    """Buy after a drop from the recent high and sell after a rally from the
    recent low.

    Parameters
    ----------
    symbol: str
        Trading symbol.
    buy_threshold: float, optional
        Fractional drop from the recent high that triggers a buy. ``0.03`` means
        buy if price falls more than 3% from the highest seen price.
    sell_threshold: float, optional
        Fractional rise from the recent low that triggers a sell. ``0.04`` means
        sell if price rises more than 4% from the lowest seen price.
    trade_qty: int, optional
        Number of shares to buy each time the condition is met.
    sell_pct: float, optional
        Portion of the current position to sell when the sell condition is met.
    """

    def __init__(
        self,
        symbol: str,
        *,
        buy_threshold: float = 0.03,
        sell_threshold: float = 0.04,
        trade_qty: int = 1000,
        sell_pct: float = 0.07,
    ) -> None:
        self.symbol = symbol
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.trade_qty = trade_qty
        self.sell_pct = sell_pct
        self.recent_low: float | None = None
        self.recent_high: float | None = None

    # ------------------------------------------------------------------
    def on_bar(
        self,
        engine: "Engine",
        timestamp: pd.Timestamp,
        data: Dict[str, pd.Series],
    ) -> None:
        price = data[self.symbol]["Close"]

        if self.recent_high is None or price > self.recent_high:
            self.recent_high = float(price)
        if self.recent_low is None or price < self.recent_low:
            self.recent_low = float(price)

        # Buy if price dropped sufficiently from recent high
        if (
            self.recent_high is not None
            and price <= self.recent_high * (1 - self.buy_threshold)
        ):
            engine.buy(self.symbol, self.trade_qty)
            self.recent_high = float(price)

        # Sell a portion if price rallied sufficiently from recent low
        if (
            self.recent_low is not None
            and price >= self.recent_low * (1 + self.sell_threshold)
        ):
            owned = engine.portfolio.positions.get(self.symbol, 0)
            qty = int(owned * self.sell_pct)
            if qty > 0:
                engine.sell(self.symbol, qty)
            self.recent_low = float(price)


__all__ = ["PullbackStrategy"]
