from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import time
from zoneinfo import ZoneInfo

from src.config import load_config
from src.external_data_collector import collect_external_universe_ohlcv
from src.market_schedule import RefreshRun, next_refresh_runs


def main() -> None:
    parser = argparse.ArgumentParser(description="Run close-based OHLCV refresh scheduler.")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--once", action="store_true", help="Run one refresh immediately and exit.")
    parser.add_argument("--dry-run", action="store_true", help="Print next refresh times and exit.")
    args = parser.parse_args()

    config = load_config(args.config)
    timezone = ZoneInfo(config.get("schedule", {}).get("timezone", "Asia/Seoul"))

    if args.dry_run:
        _print_next_runs(config, timezone)
        return

    if args.once:
        _run_refresh(config, "ALL")
        return

    print("Close-based data refresh scheduler started.")
    print(f"Config: {Path(args.config).resolve()}")
    _print_next_runs(config, timezone)
    while True:
        runs = next_refresh_runs(config)
        next_run = runs[0]
        sleep_seconds = max(1, int((next_run.run_at - datetime.now(timezone)).total_seconds()))
        time.sleep(sleep_seconds)
        _run_refresh(config, next_run.market)


def _print_next_runs(config: dict, timezone: ZoneInfo) -> None:
    for run in next_refresh_runs(config):
        print(f"Next {run.market} refresh: {run.run_at.astimezone(timezone).strftime('%Y-%m-%d %H:%M:%S %Z')}")


def _run_refresh(config: dict, market: str) -> None:
    started_at = datetime.now(ZoneInfo(config.get("schedule", {}).get("timezone", "Asia/Seoul")))
    print(f"[{started_at.isoformat()}] Refresh start: {market}")
    data = collect_external_universe_ohlcv(config)
    finished_at = datetime.now(started_at.tzinfo)
    print(
        f"[{finished_at.isoformat()}] Refresh done: rows={len(data)}, "
        f"symbols={data['symbol'].nunique() if not data.empty else 0}, "
        f"output={config['data']['universe_ohlcv_file']}"
    )


if __name__ == "__main__":
    main()
