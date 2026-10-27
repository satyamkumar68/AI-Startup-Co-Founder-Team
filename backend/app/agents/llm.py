import os
import json
import re
import logging
from typing import Type, TypeVar, Optional, Dict, Any, List, Tuple
import httpx
from pydantic import BaseModel, ValidationError

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMResponse:
    """Wrapper for LLM responses containing text, parsed object, and usage statistics."""
    def __init__(
        self,
        content: str,
        parsed: Optional[Any] = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        model: str = "",
        cost_usd: float = 0.0,
        low_confidence: bool = False,
        schema_repairs: int = 0,
        fallback_count: int = 0
    ):
        self.content = content
        self.parsed = parsed
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens
        self.model = model
        self.cost_usd = cost_usd
        self.low_confidence = low_confidence
        self.schema_repairs = schema_repairs
        self.fallback_count = fallback_count


def extract_json_from_text(text: str) -> str:
    """Extract JSON string from potential markdown code fences or raw text."""
    text = text.strip()
    
    # Check for markdown code fences: ```json ... ``` or ``` ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # Try finding the outermost JSON object { ... } or array [ ... ]
    start_brace = text.find("{")
    end_brace = text.rfind("}")
    if start_brace != -1 and end_brace != -1 and end_brace > start_brace:
        return text[start_brace:end_brace + 1].strip()
        
    start_bracket = text.find("[")
    end_bracket = text.rfind("]")
    if start_bracket != -1 and end_bracket != -1 and end_bracket > start_bracket:
        return text[start_bracket:end_bracket + 1].strip()

    return text


class MultiProviderLLM:
    """Unified LLM adapter supporting OpenRouter, Ollama, OpenAI, Gemini, and Anthropic.
    
    Supports structured JSON extraction, repair retry on validation failure (ADR-005),
    and per-agent model routing.
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 120.0,
        fallback_models: Optional[List[str]] = None,
        on_switch_callback: Optional[Any] = None
    ):
        raw_model = (model or settings.MODEL_DEFAULT).strip()
        raw_provider = (provider or "").strip().lower()

        # Auto-detect provider if model prefix is supplied (e.g. 'ollama:qwen3:4b' or 'openrouter/...')
        if raw_model.startswith("ollama:") or raw_model.startswith("ollama/"):
            self.provider = "ollama"
            self.model = raw_model.split(":", 1)[-1].split("/", 1)[-1]
        elif raw_model.startswith("openrouter/"):
            self.provider = "openrouter"
            self.model = raw_model.replace("openrouter/", "", 1)
        elif ":" in raw_model and "/" not in raw_model:
            self.provider = "ollama"
            self.model = raw_model
        elif raw_provider:
            self.provider = raw_provider
            self.model = raw_model
        elif settings.LLM_PROVIDER:
            self.provider = settings.LLM_PROVIDER.lower()
            self.model = raw_model
        else:
            self.provider = "openrouter"
        if self.provider == "ollama" and timeout == 120.0:
            self.timeout = 600.0
        else:
            self.timeout = timeout

        self.fallback_models = list(fallback_models) if fallback_models else self._default_fallbacks()
        self.on_switch_callback = on_switch_callback
        self.fallback_count: int = 0

    def _default_fallbacks(self) -> List[str]:
        """Provide automatic fallback models if primary model fails."""
        if self.provider == "ollama":
            fallbacks = ["ollama:qwen2.5-coder:1.5b", "ollama:qwen3:4b"]
            if settings.OPENROUTER_API_KEY and len(settings.OPENROUTER_API_KEY.strip()) > 10:
                fallbacks.extend([
                    "openrouter/meta-llama/llama-3.3-70b-instruct:free",
                    "openrouter/google/gemini-2.0-flash-exp:free"
                ])
            return fallbacks
        else:
            fallbacks = [
                "openrouter/google/gemini-2.0-flash-exp:free",
                "openrouter/meta-llama/llama-3.3-70b-instruct:free"
            ]
            fallbacks.append("ollama:qwen2.5-coder:1.5b")
            return fallbacks

    async def _switch_to_next_model(self, error_reason: str) -> bool:
        """Automatically switch to the next fallback model in the chain."""
        import asyncio
        if not self.fallback_models:
            return False

        # Filter out current model
        candidates = [m for m in self.fallback_models if m != self.model and f"{self.provider}:{self.model}" != m]

        # If API key is rejected (401 / Unauthorized), bypass remaining models of the same provider
        err_lower = str(error_reason).lower()
        if any(term in err_lower for term in ["401", "unauthorized", "user not found"]):
            if self.provider == "openrouter":
                candidates = [m for m in candidates if not (m.startswith("openrouter/") or "openrouter" in m)]
                if not candidates:
                    candidates = ["ollama:qwen2.5-coder:1.5b"]

        if not candidates:
            if self.provider != "ollama":
                candidates = ["ollama:qwen2.5-coder:1.5b"]
            else:
                return False

        next_model_id = candidates[0]
        self.fallback_models = candidates[1:]

        old_desc = f"{self.provider}:{self.model}"
        raw_model = next_model_id.strip()

        if raw_model.startswith("ollama:") or raw_model.startswith("ollama/"):
            self.provider = "ollama"
            self.model = raw_model.split(":", 1)[-1].split("/", 1)[-1]
        elif raw_model.startswith("openrouter/"):
            self.provider = "openrouter"
            self.model = raw_model.replace("openrouter/", "", 1)
        elif ":" in raw_model and "/" not in raw_model:
            self.provider = "ollama"
            self.model = raw_model
        else:
            self.provider = "openrouter"
            self.model = raw_model

        if self.provider == "ollama":
            self.timeout = 300.0

        self.fallback_count += 1
        new_desc = f"{self.provider}:{self.model}"
        logger.warning(f"AUTOMATIC FAILOVER: Switching from '{old_desc}' to '{new_desc}' due to: {error_reason}")

        if self.on_switch_callback:
            try:
                res = self.on_switch_callback(previous_model=old_desc, new_model=new_desc, reason=error_reason)
                if asyncio.iscoroutine(res):
                    await res
            except Exception as e:
                logger.warning(f"Error in on_switch_callback: {e}")

        return True

    def _get_api_url_and_headers(self) -> Tuple[str, Dict[str, str]]:
        """Resolve API endpoint and authentication headers based on provider."""
        try:
            from dotenv import load_dotenv
            load_dotenv(override=False)
        except Exception:
            pass

        if self.provider == "openrouter":
            url = "https://openrouter.ai/api/v1/chat/completions"
            api_key = (
                os.getenv("OPENROUTER_API_KEY")
                or settings.OPENROUTER_API_KEY
                or os.getenv("LLM_API_KEY")
                or settings.LLM_API_KEY
                or ""
            ).strip()

            auth_val = f"Bearer {api_key}" if api_key else "Bearer dev-key"
            headers = {
                "Authorization": auth_val,
                "HTTP-Referer": "https://github.com/satyam/ai-startup-co-founder",
                "X-Title": "AI Startup Co-Founder Team",
                "Content-Type": "application/json"
            }
            return url, headers

        elif self.provider == "ollama":
            # Ollama provides standard OpenAI-compatible completions endpoint
            base_url = (os.getenv("OLLAMA_BASE_URL") or settings.OLLAMA_BASE_URL).rstrip("/")
            url = f"{base_url}/v1/chat/completions"
            headers = {
                "Content-Type": "application/json"
            }
            return url, headers

        elif self.provider == "openai":
            url = "https://api.openai.com/v1/chat/completions"
            api_key = (
                os.getenv("OPENAI_API_KEY")
                or settings.OPENAI_API_KEY
                or os.getenv("LLM_API_KEY")
                or settings.LLM_API_KEY
                or ""
            ).strip()

            auth_val = f"Bearer {api_key}" if api_key else "Bearer dev-key"
            headers = {
                "Authorization": auth_val,
                "Content-Type": "application/json"
            }
            return url, headers

        elif self.provider == "gemini":
            # OpenAI-compatible endpoint for Google Gemini
            url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
            api_key = (
                os.getenv("GEMINI_API_KEY")
                or settings.GEMINI_API_KEY
                or os.getenv("LLM_API_KEY")
                or settings.LLM_API_KEY
                or ""
            ).strip()

            auth_val = f"Bearer {api_key}" if api_key else "Bearer dev-key"
            headers = {
                "Authorization": auth_val,
                "Content-Type": "application/json"
            }
            return url, headers

        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def _estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate run cost in USD based on model family."""
        if self.provider == "ollama":
            return 0.0  # Local Ollama is completely free!
        
        # Approximate blended costs per 1K tokens
        model_lower = self.model.lower()
        if "gpt-4o" in model_lower or "claude-3.5-sonnet" in model_lower:
            prompt_rate = 0.003 / 1000
            completion_rate = 0.015 / 1000
        elif "flash" in model_lower or "mini" in model_lower or "llama" in model_lower:
            prompt_rate = 0.0001 / 1000
            completion_rate = 0.0004 / 1000
        else:
            prompt_rate = 0.001 / 1000
            completion_rate = 0.003 / 1000

        return (prompt_tokens * prompt_rate) + (completion_tokens * completion_rate)

    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        response_format_json: bool = False,
    ) -> LLMResponse:
        """Execute raw text completion request against configured provider."""
        url, headers = self._get_api_url_and_headers()
        
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3 if self.provider == "ollama" else temperature,
        }

        if self.provider == "ollama":
            payload["frequency_penalty"] = 0.2
            payload["presence_penalty"] = 0.1

        if response_format_json and self.provider in ["openrouter", "openai", "ollama"]:
            payload["response_format"] = {"type": "json_object"}

        timeout_cfg = httpx.Timeout(
            connect=20.0,
            read=self.timeout,
            write=60.0,
            pool=30.0
        )

        async with httpx.AsyncClient(timeout=timeout_cfg) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPError as err:
                err_detail = ""
                if hasattr(err, "response") and err.response is not None:
                    try:
                        err_detail = f" - Response: {err.response.text}"
                    except Exception:
                        pass
                logger.error(f"LLM request error ({self.provider} - {self.model}): {err}{err_detail}")

                switched = await self._switch_to_next_model(f"{err}{err_detail}")
                if switched:
                    return await self.generate(messages, temperature, response_format_json)
                raise

        choice = data.get("choices", [{}])[0]
        content = choice.get("message", {}).get("content", "")
        
        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)
        cost_usd = self._estimate_cost(prompt_tokens, completion_tokens)

        return LLMResponse(
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            model=self.model,
            cost_usd=cost_usd
        )

    async def generate_structured(
        self,
        messages: List[Dict[str, str]],
        schema: Type[T],
        temperature: float = 0.2,
        max_retries: int = 1
    ) -> LLMResponse:
        """Generate and validate structured JSON output against a Pydantic schema.
        
        If parsing fails, triggers 1 repair retry prompt as per ADR-005 / AGENTS.md.
        If still failing, triggers automatic failover to alternative model.
        """
        # 1. Initial generation
        response = await self.generate(messages, temperature=temperature, response_format_json=True)
        raw_text = response.content

        initial_error_msg = ""
        try:
            cleaned_json_str = extract_json_from_text(raw_text)
            parsed_data = json.loads(cleaned_json_str)
            validated_obj = schema.model_validate(parsed_data)
            response.parsed = validated_obj
            response.schema_repairs = 0
            response.fallback_count = self.fallback_count
            return response
        except (json.JSONDecodeError, ValidationError) as initial_err:
            initial_error_msg = str(initial_err)
            logger.warning(f"Initial schema validation failed: {initial_err}. Triggering repair prompt...")

        # 3. Repair retry (ADR-005: 1 repair attempt with error feedback)
        if max_retries > 0:
            repair_prompt = (
                f"Your previous output failed validation against the required JSON schema.\n"
                f"Validation error:\n{initial_error_msg}\n\n"
                f"Previous output:\n{raw_text}\n\n"
                f"Schema requirement (JSON Schema):\n{json.dumps(schema.model_json_schema(), indent=2)}\n\n"
                f"Please fix all errors and return ONLY a valid, raw JSON object matching the schema."
            )
            repair_messages = list(messages) + [
                {"role": "assistant", "content": raw_text},
                {"role": "user", "content": repair_prompt}
            ]

            repair_response = await self.generate(repair_messages, temperature=0.1, response_format_json=True)
            repair_text = repair_response.content

            # Accumulate token metrics
            repair_response.prompt_tokens += response.prompt_tokens
            repair_response.completion_tokens += response.completion_tokens
            repair_response.total_tokens += response.total_tokens
            repair_response.cost_usd += response.cost_usd

            try:
                cleaned_repair_json = extract_json_from_text(repair_text)
                parsed_repair_data = json.loads(cleaned_repair_json)
                validated_obj = schema.model_validate(parsed_repair_data)
                repair_response.parsed = validated_obj
                repair_response.schema_repairs = 1
                repair_response.fallback_count = self.fallback_count
                return repair_response
            except Exception as repair_err:
                logger.error(f"Repair retry also failed validation: {repair_err}")

                # Automatically failover to next model in chain
                switched = await self._switch_to_next_model(f"Schema validation failed: {repair_err}")
                if switched:
                    return await self.generate_structured(messages, schema, temperature, max_retries)

                repair_response.low_confidence = True
                repair_response.fallback_count = self.fallback_count
                raise ValueError(f"Failed to generate structured JSON output matching schema {schema.__name__}: {repair_err}")

        response.low_confidence = True
        response.fallback_count = self.fallback_count
        return response
