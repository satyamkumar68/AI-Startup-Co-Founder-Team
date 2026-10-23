import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pydantic import BaseModel, Field
import httpx

from backend.app.agents.llm import MultiProviderLLM, LLMResponse


class DemoSchema(BaseModel):
    title: str
    confidence: float = Field(ge=0.0, le=1.0)


def test_default_fallbacks():
    llm_ollama = MultiProviderLLM(provider="ollama", model="qwen3:4b")
    assert len(llm_ollama.fallback_models) >= 2
    assert any("qwen2.5-coder" in m for m in llm_ollama.fallback_models)

    llm_or = MultiProviderLLM(provider="openrouter", model="meta-llama/llama-3.3-70b-instruct:free")
    assert len(llm_or.fallback_models) >= 2
    assert any("gemini" in m for m in llm_or.fallback_models)


@pytest.mark.asyncio
async def test_switch_to_next_model_callback():
    switched_records = []

    def on_switch(previous_model: str, new_model: str, reason: str):
        switched_records.append((previous_model, new_model, reason))

    llm = MultiProviderLLM(
        provider="ollama",
        model="qwen3:4b",
        fallback_models=["openrouter/google/gemini-2.0-flash-exp:free", "ollama:qwen2.5-coder:1.5b"],
        on_switch_callback=on_switch
    )

    success = await llm._switch_to_next_model("Client 400 bad request")
    assert success is True
    assert llm.provider == "openrouter"
    assert llm.model == "google/gemini-2.0-flash-exp:free"
    assert len(switched_records) == 1
    assert switched_records[0][0] == "ollama:qwen3:4b"
    assert switched_records[0][1] == "openrouter:google/gemini-2.0-flash-exp:free"
    assert "400" in switched_records[0][2]


@pytest.mark.asyncio
async def test_generate_auto_failover_on_http_error():
    switched = []

    def on_switch(previous_model, new_model, reason):
        switched.append((previous_model, new_model))

    llm = MultiProviderLLM(
        provider="openrouter",
        model="invalid-broken-model",
        fallback_models=["openrouter/google/gemini-2.0-flash-exp:free"],
        on_switch_callback=on_switch
    )

    mock_client = AsyncMock()
    req_dummy = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
    # First post fails with 400 Bad Request
    resp_400 = httpx.Response(status_code=400, json={"error": {"message": "Invalid model"}}, request=req_dummy)
    # Second post succeeds with 200 OK
    resp_200 = httpx.Response(
        status_code=200,
        json={
            "choices": [{"message": {"content": "Hello from fallback!"}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 5, "total_tokens": 10}
        },
        request=req_dummy
    )

    mock_client.post.side_effect = [
        httpx.HTTPStatusError("400 Bad Request", request=req_dummy, response=resp_400),
        resp_200
    ]

    with patch("httpx.AsyncClient") as MockClientCls:
        MockClientCls.return_value.__aenter__.return_value = mock_client
        res = await llm.generate([{"role": "user", "content": "ping"}])
        assert res.content == "Hello from fallback!"
        assert len(switched) == 1
        assert switched[0][1] == "openrouter:google/gemini-2.0-flash-exp:free"
