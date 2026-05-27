from __future__ import annotations

import argparse
from datetime import datetime
import time
from zoneinfo import ZoneInfo

from src.broker.kis import KisBroker
from src.config import load_config
from src.trading.order_queue import OrderQueue
from src.trading.realtime_monitor import load_breakout_watchlist, run_breakout_monitor_once


def main() -> None:
    parser = argparse.ArgumentParser(description="Monitor close-based candidates for live breakout.")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--market", default="ALL", choices=["ALL", "KR", "US"])
    parser.add_argument("--once", action="store_true", help="Run one monitor cycle and exit.")
    parser.add_argument("--dry-run", action="store_true", help="Print current watchlist and exit without price calls.")
    args = parser.parse_args()

    config = load_config(args.config)
    monitor_config = config.get("realtime_monitor", {})
    interval_minutes = int(monitor_config.get("interval_minutes", 10))

    if args.dry_run:
        watchlist = load_breakout_watchlist(config, market=args.market)
        print(f"Watchlist candidates: {len(watchlist)}")
        if not watchlist.empty:
            print(watchlist[["date", "symbol", "name", "market", "high", "buy_pattern"]].to_string(index=False))
        return

    broker = KisBroker.from_config(config)
    queue = OrderQueue()

    if args.once:
        _run_cycle(config, broker, queue, args.market)
        return

    print(f"Realtime breakout monitor started. market={args.market}, interval_minutes={interval_minutes}")
    while True:
        _run_cycle(config, broker, queue, args.market)
        time.sleep(interval_minutes * 60)


def _run_cycle(config: dict, broker: KisBroker, queue: OrderQueue, market: str) -> None:
    timezone = ZoneInfo(config.get("schedule", {}).get("timezone", "Asia/Seoul"))
    started_at = datetime.now(timezone)
    print(f"[{started_at.isoformat()}] Breakout monitor cycle start: market={market}")
    orders = run_breakout_monitor_once(config, broker, queue, market=market)
    finished_at = datetime.now(timezone)
    print(f"[{finished_at.isoformat()}] Breakout monitor cycle done: triggered={len(orders)}")


if __name__ == "__main__":
    main()
