import time
import logging
from typing import Dict, List, Any, Optional
import httpx

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

# Fallback models if external API is unreachable
DEFAULT_FREE_OPENROUTER_MODELS = [
    {
        "id": "openrouter/meta-llama/llama-3.3-70b-instruct:free",
        "name": "Llama 3.3 70B Instruct (Free)",
        "context_length": 131072,
        "provider": "openrouter",
        "is_free": True
    },
    {
        "id": "openrouter/google/gemini-2.0-flash-exp:free",
        "name": "Gemini 2.0 Flash Exp (Free)",
        "context_length": 1048576,
        "provider": "openrouter",
        "is_free": True
    },
    {
        "id": "openrouter/deepseek/deepseek-r1:free",
        "name": "DeepSeek R1 (Free)",
        "context_length": 64000,
        "provider": "openrouter",
        "is_free": True
    },
    {
        "id": "openrouter/qwen/qwen-2.5-coder-32b-instruct:free",
        "name": "Qwen 2.5 Coder 32B (Free)",
        "context_length": 32768,
        "provider": "openrouter",
        "is_free": True
    },
    {
        "id": "openrouter/mistralai/mistral-7b-instruct:free",
        "name": "Mistral 7B Instruct (Free)",
        "context_length": 32768,
        "provider": "openrouter",
        "is_free": True
    }
]

DEFAULT_FLAGSHIP_MODELS = [
    {
        "id": "openrouter/anthropic/claude-3.5-sonnet",
        "name": "Anthropic: Claude 3.5 Sonnet",
        "context_length": 200000,
        "provider": "openrouter",
        "is_free": False
    },
    {
        "id": "openrouter/openai/gpt-4o",
        "name": "OpenAI: GPT-4o",
        "context_length": 128000,
        "provider": "openrouter",
        "is_free": False
    },
    {
        "id": "openrouter/google/gemini-2.0-flash-001",
        "name": "Google: Gemini 2.0 Flash",
        "context_length": 1048576,
        "provider": "openrouter",
        "is_free": False
    }
]


class ModelCatalogService:
    """Service to discover and cache models from OpenRouter and local Ollama."""

    def __init__(self, cache_ttl_seconds: int = 3600):
        self.cache_ttl = cache_ttl_seconds
        self._cached_data: Optional[Dict[str, Any]] = None
        self._last_fetch_time: float = 0.0

    async def get_models(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Return categorized models with 1-hour cache."""
        now = time.time()
        if (
            not force_refresh
            and self._cached_data is not None
            and (now - self._last_fetch_time) < self.cache_ttl
        ):
            return self._cached_data

        free_openrouter = await self._fetch_openrouter_free_models()
        local_ollama = await self._fetch_ollama_models()

        catalog = {
            "free_openrouter": free_openrouter or DEFAULT_FREE_OPENROUTER_MODELS,
            "openrouter_free": free_openrouter or DEFAULT_FREE_OPENROUTER_MODELS,
            "local_ollama": local_ollama,
            "ollama_local": local_ollama,
            "flagship": DEFAULT_FLAGSHIP_MODELS,
            "cached_at": now
        }

        self._cached_data = catalog
        self._last_fetch_time = now
        return catalog

    async def _fetch_openrouter_free_models(self) -> List[Dict[str, Any]]:
        """Query OpenRouter API and filter all free models."""
        url = "https://openrouter.ai/api/v1/models"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    models_raw = data.get("data", [])
                    free_list = []
                    for m in models_raw:
                        m_id = m.get("id", "")
                        pricing = m.get("pricing", {})
                        prompt_price = float(pricing.get("prompt", 0) or 0)
                        completion_price = float(pricing.get("completion", 0) or 0)

                        is_free = (
                            ":free" in m_id
                            or (prompt_price == 0.0 and completion_price == 0.0)
                        )

                        if is_free:
                            free_list.append({
                                "id": f"openrouter/{m_id}",
                                "name": m.get("name", m_id),
                                "context_length": m.get("context_length", 32768),
                                "provider": "openrouter",
                                "is_free": True
                            })

                    if free_list:
                        # Prioritize popular models
                        free_list.sort(key=lambda x: (":free" not in x["id"], x["name"]))
                        return free_list[:25]
        except Exception as e:
            logger.warning(f"Failed to fetch dynamic OpenRouter models: {e}")

        return DEFAULT_FREE_OPENROUTER_MODELS

    async def _fetch_ollama_models(self) -> List[Dict[str, Any]]:
        """Query local Ollama instance for installed models."""
        base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        url = f"{base_url}/api/tags"
        local_list = []
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    for m in data.get("models", []):
                        name = m.get("name", "")
                        local_list.append({
                            "id": f"ollama:{name}",
                            "name": f"Local Ollama: {name}",
                            "size_bytes": m.get("size", 0),
                            "provider": "ollama",
                            "is_free": True
                        })
        except Exception:
            # If Ollama is not running, return empty list gracefully
            pass

        return local_list


model_catalog_service = ModelCatalogService()
