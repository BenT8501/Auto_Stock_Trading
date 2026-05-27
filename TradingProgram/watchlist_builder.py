from __future__ import annotations

import argparse
from datetime import date

from src.config import load_config
from src.trading.watchlist_builder import build_watchlist


def main() -> None:
    parser = argparse.ArgumentParser(description="Build next-session setup watchlist from close-based data.")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--date", default=None, help="Watch date in YYYY-MM-DD. Defaults to today.")
    parser.add_argument("--market", default="ALL", choices=["ALL", "KR", "US"])
    args = parser.parse_args()

    config = load_config(args.config)
    run_date = date.fromisoformat(args.date) if args.date else None
    result = build_watchlist(config, run_date=run_date, market=args.market)

    print(f"trend_candidates: {len(result['trend_candidates'])}")
    print(f"setup_candidates: {len(result['setup_candidates'])}")
    print(f"watchlist: {len(result['watchlist'])}")
    print(f"output_dir: {config.get('watchlist', {}).get('output_dir', 'data/watchlist')}")


if __name__ == "__main__":
    main()
