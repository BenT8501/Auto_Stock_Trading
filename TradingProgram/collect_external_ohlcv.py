from __future__ import annotations

import argparse

from src.config import load_config
from src.external_data_collector import collect_external_universe_ohlcv


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--output", default=None)
    parser.add_argument("--limit-per-market", type=int, default=None)
    args = parser.parse_args()

    config = load_config(args.config)
    data = collect_external_universe_ohlcv(config, output_path=args.output, limit_per_market=args.limit_per_market)
    print(f"Saved rows: {len(data)}")
    print(f"Symbols: {data['symbol'].nunique() if not data.empty else 0}")
    print(f"Output: {args.output or config['data']['universe_ohlcv_file']}")


if __name__ == "__main__":
    main()
