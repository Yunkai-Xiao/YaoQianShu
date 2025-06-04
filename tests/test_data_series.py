from __future__ import annotations

import pandas as pd
from src.data import DataSeries


def test_series_indicator_registration():
    df = pd.DataFrame(
        {
            "Close": [1, 2, 3],
            "Volume": [10, 20, 30],
        },
        index=pd.date_range("2020-01-01", periods=3, freq="D"),
    )
    series = DataSeries(df)
    series.register_indicator("vol2", lambda d: d["Volume"] * 2)
    enhanced = series.enhance()
    assert "vol2" in enhanced.columns
    assert enhanced["vol2"].iloc[0] == 20

    series.unregister_indicator("vol2")
    enhanced2 = series.enhance()
    assert "vol2" not in enhanced2.columns
