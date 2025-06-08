from __future__ import annotations

from typing import Dict, List

import pandas as pd

from ..strategy import Strategy
from ..alphas.alpha101 import compute_alpha


class AlphaWeightStrategy(Strategy):
    """Allocate portfolio weights based on Alpha101 values across symbols."""

    def __init__(self, symbols: List[str], alpha_name: str = "alpha001") -> None:
        self.symbols = symbols
        self.alpha_name = alpha_name
        self.history: Dict[str, pd.DataFrame] = {sym: pd.DataFrame() for sym in symbols}

    # ------------------------------------------------------------------
    def on_bar(
        self,
        engine: "Engine",
        timestamp: pd.Timestamp,
        data: Dict[str, pd.Series],
    ) -> None:
        # Append latest rows to history
        for sym in self.symbols:
            row = data[sym]
            self.history[sym] = pd.concat([self.history[sym], row.to_frame().T])

        scores: Dict[str, float] = {}
        for sym in self.symbols:
            try:
                series = compute_alpha(self.history[sym], self.alpha_name)
                val = series.iloc[-1]
                if pd.notna(val):
                    scores[sym] = float(val)
            except Exception:
                continue

        if not scores:
            return

        # Convert scores to long-only weights via rank
        ranks = pd.Series(scores).rank(pct=True)
        total = ranks.sum()
        if total == 0:
            return
        weights = {sym: ranks[sym] / total for sym in scores}

        # Determine position changes first, then execute sells before buys
        changes: List[tuple[str, int]] = []
        for sym, weight in weights.items():
            price = data[sym]["Close"]
            portfolio_value = engine.portfolio.value(data)
            target_qty = int((portfolio_value * weight) / price)
            owned = engine.portfolio.positions.get(sym, 0)
            diff = target_qty - owned
            if diff:
                changes.append((sym, diff))

        for sym, diff in changes:
            if diff < 0:
                engine.sell(sym, -diff)

        for sym, diff in changes:
            if diff > 0:
                engine.buy(sym, diff)


__all__ = ["AlphaWeightStrategy"]
