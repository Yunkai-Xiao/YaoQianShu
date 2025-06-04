from abc import ABC, abstractmethod
from bisect import bisect_left, insort
from collections import deque
from datetime import datetime


# ──────────── Indicator Base Class ──────────── #
class Indicator(ABC):
    @abstractmethod
    def name(self):
        """
        Returns the unique name of the indicator (e.g., "KDJ_9_3_3" or "SMA_50").
        This name is used as a key in each StockDataPoint.indicators dict.
        """
        pass

    @abstractmethod
    def lookback_period(self):
        """
        How many data points (including current) are needed to calculate this indicator.
        E.g., for a 9‐period KDJ, this should return 9.
        """
        pass

    @abstractmethod
    def calculate(self, window):
        """
        Calculate the indicator based on the provided list of StockDataPoint's.
        The length of 'window' will be exactly self.lookback_period() (once enough data exists).
        Should return the indicator’s value (a float, dict, tuple, etc.), or None if not enough data.
        """
        pass


# ──────────── Stock Data Point ──────────── #
class StockDataPoint:
    __slots__ = ("open", "high", "low", "close", "indicators")

    def __init__(self, open_price, high_price, low_price, close_price):
        self.open = open_price
        self.high = high_price
        self.low = low_price
        self.close = close_price

        # Each data point holds a dict mapping indicator_name -> indicator_value
        self.indicators = {}

    def add_indicator(self, name, value):
        """
        Store (or overwrite) an indicator value at this timestamp.
        """
        self.indicators[name] = value

    def get_indicator(self, name):
        """
        Return the previously calculated indicator value, or None if missing.
        """
        return self.indicators.get(name)

    def __repr__(self):
        return (
            f"StockDataPoint(O={self.open:.2f}, H={self.high:.2f}, "
            f"L={self.low:.2f}, C={self.close:.2f}, "
            f"inds={self.indicators})"
        )


# ──────────── Stock Time Series ──────────── #
class StockTimeSeries:
    def __init__(self, interval="1min"):
        """
        interval: A string describing the granularity (e.g., "1min", "5min", "1hour", "1day").
        Internally, we store:
          self._timestamps: List of datetime
          self._data:       Dict mapping datetime -> StockDataPoint
        so that timestamps are always kept sorted.
        """
        self.interval = interval
        self._timestamps = []    # list of datetime, kept sorted
        self._data = {}          # maps datetime -> StockDataPoint
        self._indicators = []    # list of registered Indicator instances

    def insert(self, timestamp, open_price, high_price, low_price, close_price):
        """
        Insert a new stock data point. If the timestamp already exists, it will be overwritten.
        Timestamps are kept in ascending order internally.
        """
        if timestamp in self._data:
            # Overwrite existing data point
            self._data[timestamp] = StockDataPoint(open_price, high_price, low_price, close_price)
        else:
            # Insert into sorted timestamp list
            insort(self._timestamps, timestamp)
            self._data[timestamp] = StockDataPoint(open_price, high_price, low_price, close_price)

    def get_data(self, timestamp):
        """
        Return the StockDataPoint at exactly this timestamp, or None if not found.
        """
        return self._data.get(timestamp)

    def get_data_in_range(self, start_time, end_time):
        """
        Return a list of (timestamp, StockDataPoint) for all timestamps in [start_time, end_time], inclusive.
        """
        start_idx = bisect_left(self._timestamps, start_time)
        end_idx = bisect_left(self._timestamps, end_time) + 1
        results = []
        for ts in self._timestamps[start_idx:end_idx]:
            results.append((ts, self._data[ts]))
        return results

    def register_indicator(self, indicator):
        """
        Register a new indicator. If an indicator with the same name is already registered, raises ValueError.
        """
        if any(ind.name() == indicator.name() for ind in self._indicators):
            raise ValueError(f"Indicator '{indicator.name()}' is already registered.")
        self._indicators.append(indicator)

    def unregister_indicator(self, indicator_name):
        """
        Unregister an indicator by name. Also remove its values from ALL data points in history.
        """
        self._indicators = [ind for ind in self._indicators if ind.name() != indicator_name]
        for dp in self._data.values():
            if indicator_name in dp.indicators:
                dp.indicators.pop(indicator_name)

    def calculate_all_indicators(self):
        """
        Walk through every timestamp in chronological order.
        For each registered indicator, gather exactly lookback_period() last points (if available)
        and call indicator.calculate(window). If insufficient history, store None.
        """
        # Pre‐compute each indicator’s lookback so we don't call the method repeatedly inside the loop
        ind_lookbacks = {ind.name(): max(1, ind.lookback_period()) for ind in self._indicators}

        for idx, ts in enumerate(self._timestamps):
            dp = self._data[ts]
            for ind in self._indicators:
                lb = ind_lookbacks[ind.name()]
                if idx + 1 < lb:
                    # Not enough data yet to compute this indicator
                    dp.add_indicator(ind.name(), None)
                else:
                    # Grab exactly lb points: from index (idx - lb + 1) to idx inclusive
                    window_timestamps = self._timestamps[idx - lb + 1 : idx + 1]
                    window = [self._data[wts] for wts in window_timestamps]
                    value = ind.calculate(window)
                    dp.add_indicator(ind.name(), value)

    def backtest(self, strategy_function):
        """
        Backtest a strategy over the entire history. Assumes calculate_all_indicators()
        has already been called to populate every StockDataPoint.indicators.
        The strategy_function takes (timestamp, StockDataPoint) and returns a string action (e.g., "BUY", "SELL", "HOLD").
        """
        if not self._indicators:
            print("Warning: No indicators registered. Strategy_function may rely on them anyway.")
        for ts in self._timestamps:
            dp = self._data[ts]
            action = strategy_function(ts, dp)
            print(f"[{ts.isoformat()}] Action: {action}, Indicators: {dp.indicators}")

    def __repr__(self):
        indicator_names = [ind.name() for ind in self._indicators]
        return (
            f"StockTimeSeries(interval='{self.interval}', points={len(self._timestamps)}, "
            f"indicators={indicator_names})"
        )
