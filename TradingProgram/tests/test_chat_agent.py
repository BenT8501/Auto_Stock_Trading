from __future__ import annotations

from src.agent.chat_agent import ChatAgent


def test_chat_agent_blocks_order_requests() -> None:
    agent = ChatAgent({"agent_safety": {"block_real_order_tools": True}})

    answer, table = agent.answer("삼성전자 매수 주문 넣어줘")

    assert "실주문" in answer
    assert table is None


def test_chat_agent_uses_safe_tool_registry() -> None:
    config = {
        "agent_safety": {"block_real_order_tools": True},
        "watchlist": {"output_dir": "missing"},
        "results": {"output_dir": "missing"},
        "manual_search": {"default_market": "KR", "latest_only": True, "max_results": 10},
        "data": {"universe_ohlcv_file": "missing.csv"},
        "universe": {"kr_file": "missing.csv", "us_file": "missing.csv"},
    }
    agent = ChatAgent(config)

    answer, _table = agent.answer("현재 셋업 후보 보여줘")

    assert "조건 기반 분석" in answer or "조건을 통과" in answer
