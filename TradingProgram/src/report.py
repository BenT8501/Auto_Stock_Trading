from __future__ import annotations

from pathlib import Path

import pandas as pd


def save_backtest_outputs(result: dict, metrics: dict, output_dir: str | Path) -> None:
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    result["trades"].to_csv(path / "trades.csv", index=False)
    result["equity_curve"].to_csv(path / "equity_curve.csv", index=False)
    result["skipped_signals"].to_csv(path / "skipped_signals.csv", index=False)
    pd.DataFrame([metrics]).to_csv(path / "metrics.csv", index=False)


def format_metrics(metrics: dict) -> str:
    lines = ["Backtest Metrics"]
    for key, value in metrics.items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines)
