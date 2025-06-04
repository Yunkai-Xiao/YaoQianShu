from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class Report:
    final_value: float
    total_return: float
    annual_return: float
    sharpe_ratio: float
    max_drawdown: float


def analyze(results: pd.DataFrame, risk_free_rate: float = 0.0) -> Report:
    """Calculate basic performance statistics for an Engine run."""
    value = results["value"]
    returns = value.pct_change().fillna(0.0)

    total = value.iloc[-1] / value.iloc[0] - 1
    annual = (1 + total) ** (252 / len(value)) - 1

    excess = returns - risk_free_rate / 252
    sharpe = (excess.mean() / (excess.std() + 1e-12)) * (252 ** 0.5)

    equity = (1 + returns).cumprod()
    drawdown = (equity - equity.cummax()) / equity.cummax()
    max_dd = drawdown.min()

    return Report(
        final_value=float(value.iloc[-1]),
        total_return=float(total),
        annual_return=float(annual),
        sharpe_ratio=float(sharpe),
        max_drawdown=float(max_dd),
    )


__all__ = ["Report", "analyze"]
