"""Collection of trading strategies."""
from .moving_average import MovingAverageCrossStrategy
from .macd import MACDStrategy

__all__ = [
    "MovingAverageCrossStrategy",
    "MACDStrategy",
]
