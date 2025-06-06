#!/usr/bin/env python
"""Example script to run a moving average crossover backtest."""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src import DataPortal, DataStore, Engine, MovingAverageCrossStrategy
from src.analysis import analyze


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run moving average cross strategy")
    p.add_argument("--root", default="./market_data", help="Data folder")
    p.add_argument("--symbol", default="SPY", help="Symbol to trade")
    p.add_argument("--short", type=int, default=20, help="Short moving average")
    p.add_argument("--long", type=int, default=50, help="Long moving average")
    p.add_argument("--cash", type=float, default=1_000_000.0, help="Starting cash")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    store = DataStore(Path(args.root).expanduser())
    portal = DataPortal(store, [args.symbol])
    strat = MovingAverageCrossStrategy(args.symbol, args.short, args.long)
    engine = Engine(portal, strat, starting_cash=args.cash)
    results = engine.run()
    report = analyze(results)
    print(report)

if __name__ == "__main__":
    main()
