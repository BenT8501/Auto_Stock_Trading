from __future__ import annotations

import argparse

from src.broker.kis import KisBroker
from src.config import load_config
from src.data_collector import collect_kis_universe_ohlcv


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--output", default="data/processed/kis_universe_ohlcv.csv")
    parser.add_argument("--limit-per-market", type=int, default=None)
    args = parser.parse_args()

    config = load_config(args.config)
    broker = KisBroker.from_config(config)
    result = collect_kis_universe_ohlcv(
        config,
        broker,
        output_path=args.output,
        limit_per_market=args.limit_per_market,
    )
    print(f"Saved rows: {len(result.data)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
