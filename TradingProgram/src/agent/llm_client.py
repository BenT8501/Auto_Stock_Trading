from __future__ import annotations

from abc import ABC, abstractmethod
import json
from typing import Any

import pandas as pd
import requests


class LLMClientBase(ABC):
    @abstractmethod
    def choose_tool(self, question: str, available_tools: list[str]) -> dict:
        raise NotImplementedError

    @abstractmethod
    def summarize(self, question: str, tool_name: str, tool_result) -> str:
        raise NotImplementedError


class MockLLMClient(LLMClientBase):
    def choose_tool(self, question: str, available_tools: list[str]) -> dict:
        text = question.lower()
        if "트리거" in question or "trigger" in text:
            return {"tool": "get_triggered_candidates", "args": {}}
        if "셋업" in question or "setup" in text or "감시" in question:
            return {"tool": "get_setup_candidates", "args": {}}
        if "트리거가" in question or "trigger price" in text or "가격" in question:
            symbol = _extract_symbol(question)
            return {"tool": "get_trigger_price", "args": {"symbol": symbol}}
        if "상태" in question or "설명" in question:
            symbol = _extract_symbol(question)
            return {"tool": "explain_stock_status", "args": {"symbol": symbol}}
        if "지표" in question or "metric" in text:
            symbol = _extract_symbol(question)
            return {"tool": "get_stock_latest_metrics", "args": {"symbol": symbol}}
        if "비교" in question or "완화" in question:
            symbol = _extract_symbol(question)
            return {"tool": "compare_strategy_conditions", "args": {"symbol": symbol, "relaxed": "완화" in question}}
        return {"tool": "search_by_conditions", "args": {"query": question}}

    def summarize(self, question: str, tool_name: str, tool_result) -> str:
        return (
            "현재 로컬 데이터와 내부 계산 함수 기준 결과입니다. "
            "이는 투자 추천이 아니라 조건 기반 분석입니다.\n\n"
            f"질문: {question}\n"
            f"사용 도구: {tool_name}\n"
            f"결과:\n{tool_result}"
        )


class OllamaGemmaLLMClient(LLMClientBase):
    def __init__(
        self,
        *,
        model: str,
        base_url: str = "http://localhost:11434",
        timeout_seconds: int = 60,
        fallback: LLMClientBase | None = None,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.fallback = fallback or MockLLMClient()

    def choose_tool(self, question: str, available_tools: list[str]) -> dict:
        prompt = (
            "너는 로컬 자동매매 리서치 앱의 읽기 전용 tool router다.\n"
            "실주문/실매도/설정 변경/계좌 조회 tool은 절대 선택하지 않는다.\n"
            "아래 tool 중 하나만 골라 JSON만 출력한다.\n"
            f"available_tools={available_tools}\n"
            "JSON schema: {\"tool\":\"tool_name\",\"args\":{...}}\n"
            "검색성 질문이면 search_by_conditions를 선택하고 args에는 query 원문을 넣어라.\n"
            f"question={question}"
        )
        try:
            content = self._chat(prompt, json_format=True)
            parsed = _parse_json_object(content)
            if parsed.get("tool") not in available_tools:
                return self.fallback.choose_tool(question, available_tools)
            return {"tool": parsed.get("tool"), "args": parsed.get("args") or {}}
        except Exception:
            return self.fallback.choose_tool(question, available_tools)

    def summarize(self, question: str, tool_name: str, tool_result) -> str:
        prompt = (
            "너는 로컬 자동매매 리서치 앱의 설명 Agent다.\n"
            "투자 추천을 직접 생성하지 말고 내부 함수 결과만 설명한다.\n"
            "'추천' 대신 '조건 통과 후보'라는 표현을 사용한다.\n"
            "수익 가능성을 단정하지 않는다.\n"
            "항상 현재 로컬 데이터 기준임을 명시한다.\n\n"
            f"질문: {question}\n"
            f"사용 도구: {tool_name}\n"
            f"도구 결과:\n{_compact_result(tool_result)}"
        )
        try:
            return self._chat(prompt, json_format=False)
        except Exception:
            return self.fallback.summarize(question, tool_name, tool_result)

    def _chat(self, prompt: str, *, json_format: bool) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "stream": False,
            "messages": [{"role": "user", "content": prompt}],
        }
        if json_format:
            payload["format"] = "json"
        response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=self.timeout_seconds)
        response.raise_for_status()
        data = response.json()
        return str(data.get("message", {}).get("content", "")).strip()


GemmaLLMClient = OllamaGemmaLLMClient


def create_llm_client(config: dict) -> LLMClientBase:
    chat = config.get("chat", {})
    provider = str(chat.get("provider", "mock")).lower()
    if provider in {"ollama", "gemma", "gemma4"}:
        return OllamaGemmaLLMClient(
            model=str(chat.get("model", "gemma4")),
            base_url=str(chat.get("ollama_base_url", "http://localhost:11434")),
            timeout_seconds=int(chat.get("timeout_seconds", 60)),
        )
    return MockLLMClient()


def _parse_json_object(content: str) -> dict:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start : end + 1])
        raise


def _compact_result(result) -> str:
    if isinstance(result, pd.DataFrame):
        if result.empty:
            return "empty DataFrame"
        return result.head(20).to_string(index=False)
    if isinstance(result, dict):
        return json.dumps(result, ensure_ascii=False, indent=2)
    return str(result)


def _extract_symbol(text: str) -> str:
    for token in text.replace(",", " ").split():
        cleaned = token.strip().upper()
        if cleaned.isdigit() and len(cleaned) <= 6:
            return cleaned.zfill(6)
        if cleaned.isalpha() and 1 <= len(cleaned) <= 6:
            return cleaned
    return ""
