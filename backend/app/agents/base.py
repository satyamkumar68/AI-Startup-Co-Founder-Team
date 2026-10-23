import os
import time
import logging
from typing import Type, TypeVar, Optional, Dict, Any, List, Tuple
from pydantic import BaseModel

from backend.app.agents.llm import MultiProviderLLM, LLMResponse
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class BaseAgent:
    """Base class for all startup co-founder agents."""

    def __init__(
        self,
        name: str,
        prompt_file: str,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        fallback_models: Optional[List[str]] = None,
        on_switch_callback: Optional[Any] = None
    ):
        self.name = name
        self.prompt_file = prompt_file
        self.provider = provider or settings.LLM_PROVIDER
        self.model = model or settings.MODEL_DEFAULT
        self.llm = MultiProviderLLM(
            provider=self.provider,
            model=self.model,
            fallback_models=fallback_models,
            on_switch_callback=on_switch_callback
        )
        self.system_prompt = self._load_prompt()

    def _load_prompt(self) -> str:
        """Load Markdown prompt template from /prompts/ directory."""
        # Check standard paths
        possible_paths = [
            os.path.join(os.path.dirname(__file__), "../../../prompts", self.prompt_file),
            os.path.join(os.getcwd(), "prompts", self.prompt_file),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()

        logger.warning(f"Prompt file {self.prompt_file} not found; using fallback.")
        return f"You are the {self.name} for the startup co-founder team."

    async def execute_structured(
        self,
        user_content: str,
        schema: Type[T],
        additional_messages: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.2
    ) -> Tuple[T, Dict[str, Any]]:
        """Execute LLM call and return validated Pydantic model + execution metadata."""
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        if additional_messages:
            messages.extend(additional_messages)
        messages.append({"role": "user", "content": user_content})

        start_time = time.time()
        response: LLMResponse = await self.llm.generate_structured(
            messages=messages,
            schema=schema,
            temperature=temperature
        )
        latency_ms = int((time.time() - start_time) * 1000)

        meta = {
            "agent": self.name,
            "model": response.model,
            "provider": self.provider,
            "tokens": response.total_tokens,
            "prompt_tokens": response.prompt_tokens,
            "completion_tokens": response.completion_tokens,
            "cost_usd": response.cost_usd,
            "latency_ms": latency_ms,
            "low_confidence": response.low_confidence
        }

        return response.parsed, meta
