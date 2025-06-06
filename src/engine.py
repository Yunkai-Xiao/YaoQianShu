from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import pandas as pd

from .data import DataPortal
from .strategy import Strategy


@dataclass
class Portfolio:
    cash: float
    positions: Dict[str, int] = field(default_factory=dict)

    def value(self, prices: Dict[str, pd.Series]) -> float:
        return self.cash + sum(
            self.positions.get(sym, 0) * prices[sym]["Close"] for sym in prices
        )


@dataclass
class Trade:
    timestamp: pd.Timestamp
    symbol: str
    quantity: int
    price: float
    side: str


class Engine:
    """Simple backtesting engine."""

    def __init__(
        self,
        data_portal: DataPortal,
        strategy: Strategy,
        *,
        starting_cash: float = 1_000_000.0,
    ) -> None:
        self.data_portal = data_portal
        self.strategy = strategy
        self.portfolio = Portfolio(
            cash=starting_cash,
            positions={sym: 0 for sym in data_portal.symbols},
        )
        self._current_bar: Optional[Dict[str, pd.Series]] = None
        self._current_ts: Optional[pd.Timestamp] = None
        self.trades: List[Trade] = []

    # ------------------------------------------------------------------
    def buy(self, symbol: str, quantity: int) -> None:
        if self._current_bar is None:
            raise RuntimeError("No market data available")
        price = self._current_bar[symbol]["Close"]
        cost = price * quantity
        if cost > self.portfolio.cash:
            raise ValueError("Insufficient cash")
        self.portfolio.cash -= cost
        self.portfolio.positions[symbol] += quantity
        self.trades.append(
            Trade(
                timestamp=self._current_ts,
                symbol=symbol,
                quantity=quantity,
                price=float(price),
                side="buy",
            )
        )

    def sell(self, symbol: str, quantity: int) -> None:
        if self._current_bar is None:
            raise RuntimeError("No market data available")
        price = self._current_bar[symbol]["Close"]
        owned = self.portfolio.positions.get(symbol, 0)
        qty = min(quantity, owned)
        self.portfolio.positions[symbol] = owned - qty
        self.portfolio.cash += price * qty
        if qty:
            self.trades.append(
                Trade(
                    timestamp=self._current_ts,
                    symbol=symbol,
                    quantity=qty,
                    price=float(price),
                    side="sell",
                )
            )

    def run(
        self,
        *,
        start: Optional[pd.Timestamp] = None,
        end: Optional[pd.Timestamp] = None,
    ) -> pd.DataFrame:
        history: List[Dict[str, float]] = []
        for ts, bar in self.data_portal.iter_bars(start=start, end=end):
            self._current_bar = bar
            self._current_ts = ts
            self.strategy.on_bar(self, ts, bar)
            history.append(
                {
                    "timestamp": ts,
                    "value": self.portfolio.value(bar),
                    "cash": self.portfolio.cash,
                }
            )
        self._current_bar = None
        self._current_ts = None
        df = pd.DataFrame(history).set_index("timestamp")
        return df
