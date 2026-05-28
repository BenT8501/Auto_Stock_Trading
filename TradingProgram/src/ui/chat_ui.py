from __future__ import annotations

import pandas as pd


def format_chat_table(frame: pd.DataFrame | None) -> pd.DataFrame:
    if frame is None:
        return pd.DataFrame()
    return frame.copy()


def format_agent_answer(answer: str) -> str:
    return answer.strip()
