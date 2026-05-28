from __future__ import annotations

import argparse
from datetime import date, datetime
import time
from zoneinfo import ZoneInfo

from src.broker.kis import KisBroker
from src.config import load_config
from src.trading.notifier import CompositeNotifier
from src.trading.realtime_scanner import load_watchlist, scan_watchlist_once, update_realtime_status


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan setup watchlist for intraday trigger signals.")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--date", default=None, help="Watchlist date in YYYY-MM-DD. Defaults to latest file.")
    parser.add_argument("--market", default="ALL", choices=["ALL", "KR", "US"])
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config = load_config(args.config)
    watch_date = date.fromisoformat(args.date) if args.date else None

    if args.dry_run:
        watchlist = load_watchlist(config, watch_date=watch_date, market=args.market)
        print(f"watchlist: {len(watchlist)}")
        if not watchlist.empty:
            print(watchlist[["trade_date", "setup_date", "symbol", "name", "market", "trigger_price", "gap_limit_price"]].to_string(index=False))
        return

    broker = KisBroker.from_config(config)
    notifier = CompositeNotifier.from_config(config)
    realtime = config.get("realtime", {})
    price_scan_interval_seconds = int(realtime.get("price_scan_interval_seconds", 10))
    status_refresh_interval_minutes = int(realtime.get("status_refresh_interval_minutes", 10))

    if args.once:
        _run_cycle(config, broker, notifier, watch_date, args.market)
        return

    print(
        "Realtime scanner started. "
        f"market={args.market}, price_scan_interval_seconds={price_scan_interval_seconds}, "
        f"status_refresh_interval_minutes={status_refresh_interval_minutes}"
    )
    last_status_refresh = 0.0
    while True:
        _run_cycle(config, broker, notifier, watch_date, args.market)
        now = time.time()
        if now - last_status_refresh >= status_refresh_interval_minutes * 60:
            watchlist = load_watchlist(config, watch_date=watch_date, market=args.market)
            update_realtime_status(config, watchlist, watch_date=watch_date)
            last_status_refresh = now
        time.sleep(price_scan_interval_seconds)


def _run_cycle(config: dict, broker: KisBroker, notifier: CompositeNotifier, watch_date: date | None, market: str) -> None:
    timezone = ZoneInfo(config.get("schedule", {}).get("timezone", "Asia/Seoul"))
    started_at = datetime.now(timezone)
    print(f"[{started_at.isoformat()}] realtime scanner cycle start: market={market}")
    triggered = scan_watchlist_once(config, broker, watch_date=watch_date, market=market)
    print(f"[{datetime.now(timezone).isoformat()}] realtime scanner cycle done: triggered={len(triggered)}")
    for _, row in triggered.iterrows():
        notifier.notify(
            "[trigger_signal]\n"
            f"{row['market']} {row['symbol']} {row.get('name', '')}\n"
            f"current={row['current_price']} trigger={row['trigger_price']} open={row['open_price']} "
            f"limit={row.get('limit_price', '')}"
        )


if __name__ == "__main__":
    main()
