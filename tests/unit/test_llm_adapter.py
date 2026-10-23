import pytest
from unittest.mock import AsyncMock, patch
from pydantic import BaseModel, Field

from backend.app.agents.llm import MultiProviderLLM, extract_json_from_text, LLMResponse


class SampleModel(BaseModel):
    name: str
    score: int = Field(ge=0, le=10)


def test_extract_json_from_text_markdown_code_fence():
    text = "Here is the result:\n```json\n{\"name\": \"Startup\", \"score\": 9}\n```\nHope it helps!"
    extracted = extract_json_from_text(text)
    assert extracted == '{"name": "Startup", "score": 9}'


def test_extract_json_from_text_raw_braces():
    text = "Leading chatter {\"name\": \"Startup\", \"score\": 8} trailing chatter"
    extracted = extract_json_from_text(text)
    assert extracted == '{"name": "Startup", "score": 8}'


def test_extract_json_from_text_plain():
    text = '{"name": "Startup", "score": 7}'
    extracted = extract_json_from_text(text)
    assert extracted == '{"name": "Startup", "score": 7}'


def test_llm_provider_endpoints():
    # 1. OpenRouter
    llm_openrouter = MultiProviderLLM(provider="openrouter", model="anthropic/claude-3.5-sonnet")
    url, headers = llm_openrouter._get_api_url_and_headers()
    assert "openrouter.ai" in url
    assert "Authorization" in headers

    # 2. Ollama (local server)
    llm_ollama = MultiProviderLLM(provider="ollama", model="qwen3:4b")
    url_o, headers_o = llm_ollama._get_api_url_and_headers()
    assert "11434" in url_o
    assert "/v1/chat/completions" in url_o

    # 3. OpenAI
    llm_openai = MultiProviderLLM(provider="openai", model="gpt-4o")
    url_ai, headers_ai = llm_openai._get_api_url_and_headers()
    assert "openai.com" in url_ai


@pytest.mark.asyncio
async def test_llm_generate_structured_success():
    llm = MultiProviderLLM(provider="ollama", model="qwen3:4b")
    
    mock_resp = LLMResponse(
        content='{"name": "Alpha", "score": 9}',
        prompt_tokens=10,
        completion_tokens=10,
        total_tokens=20,
        model="qwen3:4b"
    )

    with patch.object(llm, "generate", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = mock_resp
        result = await llm.generate_structured(
            messages=[{"role": "user", "content": "test"}],
            schema=SampleModel
        )
        assert result.parsed is not None
        assert result.parsed.name == "Alpha"
        assert result.parsed.score == 9


@pytest.mark.asyncio
async def test_llm_generate_structured_with_repair_retry():
    llm = MultiProviderLLM(provider="ollama", model="qwen3:4b")
    
    # First response fails schema (score 99 > 10)
    invalid_resp = LLMResponse(
        content='{"name": "Alpha", "score": 99}',
        prompt_tokens=10,
        completion_tokens=10,
        total_tokens=20,
        model="qwen3:4b"
    )
    # Repaired response succeeds (score 9)
    repaired_resp = LLMResponse(
        content='{"name": "Alpha", "score": 9}',
        prompt_tokens=15,
        completion_tokens=10,
        total_tokens=25,
        model="qwen3:4b"
    )

    with patch.object(llm, "generate", new_callable=AsyncMock) as mock_generate:
        mock_generate.side_effect = [invalid_resp, repaired_resp]
        result = await llm.generate_structured(
            messages=[{"role": "user", "content": "test"}],
            schema=SampleModel,
            max_retries=1
        )
        assert mock_generate.call_count == 2
        assert result.parsed.score == 9
