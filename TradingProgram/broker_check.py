from __future__ import annotations

import argparse

from src.broker.kis import KisBroker
from src.config import load_config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--asset", default="domestic", choices=["domestic", "us"])
    parser.add_argument("--symbol", default="005930")
    parser.add_argument("--exchange", default="NAS")
    parser.add_argument("--balance", action="store_true")
    args = parser.parse_args()

    config = load_config(args.config)
    broker = KisBroker.from_config(config)

    if args.asset == "us":
        price = broker.get_overseas_price(args.symbol, args.exchange)
        print("US price response:")
        print(price)
    else:
        price = broker.get_domestic_price(args.symbol)
        print("Domestic price response:")
        print(price)

    if args.balance:
        balance = broker.get_overseas_balance() if args.asset == "us" else broker.get_domestic_balance()
        print("Balance response:")
        print(balance)


if __name__ == "__main__":
    main()
