"""Collection of trading strategies."""

from .moving_average import MovingAverageCrossStrategy
from .macd import MACDStrategy
from .friend_strategy import FriendStrategy
from .support_ft_strategy import SupportFTStrategy
from .kdj import KDJStrategy
from .alpha101 import Alpha101Strategy
from .alpha_weight import AlphaWeightStrategy
from .pullback_strategy import PullbackStrategy

__all__ = [
    "MovingAverageCrossStrategy",
    "MACDStrategy",
    "FriendStrategy",
    "SupportFTStrategy",
    "KDJStrategy",
    "Alpha101Strategy",
    "AlphaWeightStrategy",
    "PullbackStrategy",
]
