from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict

import pandas as pd


class Strategy(ABC):
    """Base class for trading strategies."""

    @abstractmethod
    def on_bar(
        self,
        engine: "Engine",
        timestamp: pd.Timestamp,
        data: Dict[str, pd.Series],
    ) -> None:
        """Handle a new bar of market data."""
        raise NotImplementedError
