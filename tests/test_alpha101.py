from __future__ import annotations

import pandas as pd
import numpy as np

from src.alphas.alpha101 import compute_alpha


def test_alpha001():
    df = pd.DataFrame({"Close": [1.0, 2.0, 4.0, 8.0]})
    result = compute_alpha(df, "alpha001")
    expected = pd.Series([np.nan, 1.0, 1.0, 1.0])
    assert result.equals(expected)


def test_alpha004():
    df = pd.DataFrame({"Low": [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]}, dtype=float)
    result = compute_alpha(df, "alpha004")
    assert result.dropna().equals(pd.Series([-1.0, -1.0], index=[8, 9]))

