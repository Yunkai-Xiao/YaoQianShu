#!/usr/bin/env python
"""
scripts/fetch_data.py
---------------------
Bulk-download daily OHLCV data from Yahoo Finance and save it to your local
DataStore directory in Parquet format.

Usage
-----
$ python scripts/fetch_data.py             # default symbols + dates
$ python scripts/fetch_data.py --symbols AMZN TSLA --start 2015-01-01
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import List

from src.data import DataStore, download_history

###############################################################################
# CLI argument parsing
###############################################################################

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fetch historical price data")
    p.add_argument(
        "--root",
        default="./market_data",
        help="Destination folder for Parquet files (default: %(default)s)",
    )
    p.add_argument(
        "--symbols",
        nargs="+",
        default=["AAPL", "MSFT", "SPY"],
        help="Ticker symbols to download",
    )
    p.add_argument(
        "--start",
        default="2000-01-01",
        help="First date (YYYY-MM-DD)",
    )
    p.add_argument(
        "--end",
        default=None,
        help="Last date (inclusive). Omit for 'today'",
    )
    return p.parse_args()


###############################################################################
# Main routine
###############################################################################

def main():
    args = parse_args()

    logging.basicConfig(
        level="INFO", format="%(levelname)-8s %(message)s"
    )
    log = logging.getLogger("fetch_data")

    store = DataStore(Path(args.root).expanduser(), cache_size=None)
    log.info("Saving data to %s", store.root)

    failures: List[str] = []

    for sym in args.symbols:
        try:
            df = download_history(
                sym,
                start=args.start,
                end=args.end,
                store=store,
                interval="1h"
            )
            log.info("✔ %s (%d rows)", sym, len(df))
        except Exception as exc:
            log.error("✖ %s – %s", sym, exc)
            failures.append(sym)

    if failures:
        log.warning("Download finished with errors: %s", ", ".join(failures))
    else:
        log.info("All done!")

if __name__ == "__main__":
    main()
