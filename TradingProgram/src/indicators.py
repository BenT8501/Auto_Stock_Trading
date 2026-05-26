from __future__ import annotations

import pandas as pd


def add_indicators(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    result = df.copy()
    ma_config = config["strategy"]["moving_average"]
    volume_config = config["strategy"]["volume"]
    candle_config = config["strategy"]["candle"]

    short_window = int(ma_config["short_window"])
    long_window = int(ma_config["long_window"])
    slope_period = int(ma_config["slope_period"])
    volume_window = int(volume_config["window"])
    body_window = int(candle_config["body_avg_window"])

    grouped = result.groupby("symbol", group_keys=False)
    result["ma_short"] = grouped["close"].transform(lambda s: s.rolling(short_window, min_periods=1).mean())
    result["ma_long"] = grouped["close"].transform(lambda s: s.rolling(long_window, min_periods=1).mean())
    result["ma_short_slope"] = grouped["ma_short"].transform(lambda s: s.diff(slope_period))
    result["volume_ma"] = grouped["volume"].transform(lambda s: s.rolling(volume_window, min_periods=1).mean())

    body = (result["close"] - result["open"]).abs()
    result["body"] = body
    result["body_avg"] = body.groupby(result["symbol"]).transform(lambda s: s.rolling(body_window, min_periods=1).mean())
    return result
