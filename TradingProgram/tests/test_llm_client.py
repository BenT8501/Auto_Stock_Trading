from __future__ import annotations

from src.agent.llm_client import MockLLMClient, OllamaGemmaLLMClient, create_llm_client


def test_create_llm_client_uses_ollama_provider() -> None:
    client = create_llm_client({"chat": {"provider": "ollama", "model": "gemma4"}})

    assert isinstance(client, OllamaGemmaLLMClient)


def test_create_llm_client_defaults_to_mock() -> None:
    client = create_llm_client({"chat": {"provider": "mock"}})

    assert isinstance(client, MockLLMClient)


def test_ollama_choose_tool_parses_json(monkeypatch) -> None:
    class Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"message": {"content": '{"tool":"get_setup_candidates","args":{}}'}}

    def fake_post(*_args, **_kwargs):
        return Response()

    monkeypatch.setattr("src.agent.llm_client.requests.post", fake_post)
    client = OllamaGemmaLLMClient(model="gemma4")

    result = client.choose_tool("셋업 후보 보여줘", ["get_setup_candidates", "search_by_conditions"])

    assert result == {"tool": "get_setup_candidates", "args": {}}
