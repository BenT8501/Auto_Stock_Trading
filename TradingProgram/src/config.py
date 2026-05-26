from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file) or {}

    _validate_config(config)
    return config


def _validate_config(config: dict[str, Any]) -> None:
    required_sections = ["project", "data", "strategy", "execution", "risk", "costs", "broker"]
    missing = [section for section in required_sections if section not in config]
    if missing:
        raise ValueError(f"Missing config sections: {', '.join(missing)}")

    if config["project"].get("mode") not in {"backtest", "paper"}:
        raise ValueError("project.mode must be 'backtest' or 'paper'")

    if config["broker"].get("live_trading_enabled", False):
        raise ValueError("Live trading is not supported in this Phase 1 implementation")

    risk = config["risk"]
    if not 0 < float(risk["position_size_pct"]) <= 1:
        raise ValueError("risk.position_size_pct must be in (0, 1]")
