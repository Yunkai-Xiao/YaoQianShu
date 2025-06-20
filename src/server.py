from __future__ import annotations

from pathlib import Path
from typing import Dict, Callable, Optional, Any, List

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from . import (
    DataStore,
    DataPortal,
    Engine,
    analyze,
    download_history,
)
from .strategy import Strategy
import importlib
import inspect
import pkgutil
from .indicators import sma, ema, macd, volume, kdj, atr



app = FastAPI(title="Backtest API")

# ---------------------------------------------------------------------------
# Data store and portal management
# ---------------------------------------------------------------------------
DATA_ROOT = Path("src/market_data")
store = DataStore(DATA_ROOT)

# Cache DataPortal instances keyed by tuple of symbols to preserve indicators
_PORTALS: Dict[tuple, DataPortal] = {}


_INDICATORS: Dict[str, Callable[..., Any]] = {
    "sma": sma,
    "ema": ema,
    "macd": macd,
    "volume": volume,
    "kdj": kdj,
    "atr": atr,
}

_STRATEGIES: Dict[str, Callable[..., Any]] = {}


def refresh_strategies() -> None:
    """Load available strategy classes from ``src.strategies``."""
    global _STRATEGIES
    _STRATEGIES = {}
    pkg = importlib.import_module(".strategies", __package__)
    for _, mod_name, _ in pkgutil.iter_modules(pkg.__path__):
        mod = importlib.import_module(f".strategies.{mod_name}", __package__)
        for name, obj in inspect.getmembers(mod, inspect.isclass):
            if issubclass(obj, Strategy) and obj is not Strategy:
                _STRATEGIES[obj.__name__] = obj


# Populate on start
refresh_strategies()


def _get_portal(symbols: str | List[str]) -> DataPortal:
    """Return or create a DataPortal for *symbols*.

    Symbols may be provided as a single string or a list. Portals are cached
    per unique combination of symbols (order independent)."""
    if isinstance(symbols, str):
        symbols = [symbols]
    key = tuple(sorted(symbols))
    if key not in _PORTALS:
        _PORTALS[key] = DataPortal(store, list(key))
    return _PORTALS[key]


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class IndicatorRequest(BaseModel):
    symbol: str
    name: str
    params: Optional[Dict[str, Any]] = None


class BacktestRequest(BaseModel):
    symbol: Optional[str] = None
    symbols: Optional[List[str]] = None
    strategy: str
    start: Optional[str] = None
    end: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    cash: float = 1_000_000.0


class FetchRequest(BaseModel):
    symbol: str
    start: Optional[str] = "2000-01-01"
    end: Optional[str] = None


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------
@app.get("/data/{symbol}")
def get_data(symbol: str, start: Optional[str] = None, end: Optional[str] = None):
    """Return price data for *symbol* as a list of records."""
    portal = _get_portal(symbol)
    df = portal._series[symbol].enhance()
    if start or end:
        start_ts = pd.to_datetime(start) if start else df.index.min()
        end_ts = pd.to_datetime(end) if end else df.index.max()
        df = df.loc[start_ts:end_ts]
    records = df.reset_index().rename(columns={"index": "timestamp"}).to_dict("records")
    return {"symbol": symbol, "data": records}


@app.post("/indicator")
def add_indicator(req: IndicatorRequest):
    func = _INDICATORS.get(req.name)
    if func is None:
        raise HTTPException(status_code=400, detail="Unknown indicator")
    symbols = req.symbols or ([req.symbol] if req.symbol else [])
    if not symbols:
        raise HTTPException(status_code=400, detail="No symbols provided")
    portal = _get_portal(symbols)

    def wrapper(df: pd.DataFrame, f=func, p=req.params or {}):
        return f(df, **p)

    portal.register_indicator(req.name, wrapper)
    return {"status": "ok"}


@app.post("/backtest")
def run_backtest(req: BacktestRequest):
    refresh_strategies()
    strat_cls = _STRATEGIES.get(req.strategy)
    if strat_cls is None:
        raise HTTPException(status_code=400, detail="Unknown strategy")
    symbols = req.symbols or ([req.symbol] if req.symbol else [])
    if not symbols:
        raise HTTPException(status_code=400, detail="No symbols provided")
    portal = _get_portal(symbols)
    portal.register_indicator("sma", sma)
    portal.register_indicator("atr", atr)
    portal.register_indicator("kdj", kdj)
    params = req.params or {}
    sig = inspect.signature(strat_cls)
    if "symbols" in sig.parameters:
        strategy = strat_cls(symbols, **params)
    else:
        if len(symbols) != 1:
            raise HTTPException(status_code=400, detail="Strategy expects a single symbol")
        strategy = strat_cls(symbols[0], **params)
    engine = Engine(portal, strategy, starting_cash=req.cash)
    start_ts = pd.to_datetime(req.start) if req.start else None
    end_ts = pd.to_datetime(req.end) if req.end else None
    results = engine.run(start=start_ts, end=end_ts)
    report = analyze(results)
    return {
        "report": report.__dict__,
        "history": results.reset_index().to_dict("records"),
        "trades": [t.__dict__ for t in engine.trades],
    }


@app.get("/strategies")
def list_strategies():
    refresh_strategies()
    return {"strategies": list(_STRATEGIES.keys())}


@app.get("/symbols")
def list_symbols():
    symbols = store.list_symbols()
    return {"symbols": symbols}


@app.post("/fetch")
def fetch_data(req: FetchRequest):
    df = download_history(req.symbol, start=req.start, end=req.end, store=store)
    # Invalidate any cached portals containing this symbol
    for key in list(_PORTALS):
        if req.symbol in key:
            _PORTALS.pop(key, None)
    return {"rows": len(df)}
