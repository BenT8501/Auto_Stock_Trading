from __future__ import annotations

import pandas as pd

from src.agent.llm_client import LLMClientBase, create_llm_client
from src.agent.memory import ChatMemory
from src.agent.tools import AgentTools, SAFE_TOOL_NAMES


BLOCKED_WORDS = ["매수해", "매도해", "주문", "실주문", "계좌", "api key", "토큰"]


class ChatAgent:
    def __init__(self, config: dict, llm_client: LLMClientBase | None = None, memory: ChatMemory | None = None) -> None:
        self.config = config
        self.llm = llm_client or create_llm_client(config)
        self.memory = memory or ChatMemory()
        self.tools = AgentTools(config)

    def answer(self, question: str) -> tuple[str, pd.DataFrame | None]:
        self.memory.add("user", question)
        if self._blocked(question):
            response = "현재 로컬 데이터 기준 답변입니다. Chat Agent는 실주문/실매도/계좌 정보 조회를 수행하지 않습니다."
            self.memory.add("assistant", response)
            return response, None

        registry = self.tools.registry()
        tool_call = self.llm.choose_tool(question, sorted(registry))
        tool_name = str(tool_call.get("tool", "search_by_conditions"))
        if tool_name not in SAFE_TOOL_NAMES or tool_name not in registry:
            tool_name = "search_by_conditions"
            args = {"query": question}
        else:
            args = dict(tool_call.get("args") or {})

        symbol_tools = {"explain_stock_status", "get_stock_latest_metrics", "compare_strategy_conditions", "get_trigger_price"}
        if tool_name in symbol_tools and not args.get("symbol"):
            args["symbol"] = question
        if tool_name == "search_by_conditions" and "filters" not in args and "query" not in args:
            args["query"] = question
        result = registry[tool_name](**args)
        response = self._format_response(question, tool_name, result)
        self.memory.add("assistant", response)
        return response, result if isinstance(result, pd.DataFrame) else None

    def _blocked(self, question: str) -> bool:
        lowered = question.lower()
        if not self.config.get("agent_safety", {}).get("block_real_order_tools", True):
            return False
        return any(word in lowered or word in question for word in BLOCKED_WORDS)

    def _format_response(self, question: str, tool_name: str, result) -> str:
        prefix = "현재 로컬 데이터와 내부 계산 함수 기준입니다. 투자 추천이 아니라 조건 기반 분석입니다."
        if isinstance(result, pd.DataFrame):
            if result.empty:
                return f"{prefix}\n\n조건을 통과한 후보가 없습니다."
            latest_date = result["date"].max() if "date" in result.columns else result.get("setup_date", pd.Series([""])).max()
            return f"{prefix}\n\n사용 도구: {tool_name}\n기준일: {str(latest_date)[:10]}\n조건 통과 후보: {len(result)}개"
        if isinstance(result, dict):
            lines = [f"{key}: {value}" for key, value in result.items()]
            return f"{prefix}\n\n사용 도구: {tool_name}\n" + "\n".join(lines)
        return self.llm.summarize(question, tool_name, result)
