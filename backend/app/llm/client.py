from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.llm.models import LLMRequest, ProviderError
from app.llm.providers import GenericHTTPProvider, OpenAIProvider
from app.validators.types import RoleType


class LLMClient:
    def __init__(self, provider) -> None:
        self.provider = provider

    def model_for_role(self, role: RoleType) -> str:
        settings = get_settings()
        if role == RoleType.INTENT:
            return settings.llm_model_intent
        if role == RoleType.RISK:
            return settings.llm_model_risk
        if role == RoleType.ASSUMPTION:
            return settings.llm_model_assumption
        return settings.llm_model_interview

    def generate(
        self,
        role: RoleType,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.1,
        max_tokens: int = 1200,
    ) -> str:
        settings = get_settings()
        request = LLMRequest(
            model=self.model_for_role(role),
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout_seconds=settings.llm_timeout_seconds,
        )
        try:
            return self.provider.generate(request).raw_text
        except ProviderError as exc:
            if exc.transient:
                # Provider-level retry once on transient network/server issues.
                return self.provider.generate(request).raw_text
            raise


@lru_cache
def get_llm_client() -> LLMClient:
    settings = get_settings()
    if settings.llm_provider == "openai":
        provider = OpenAIProvider(api_key=settings.llm_api_key, base_url=settings.llm_base_url or "https://api.openai.com/v1")
    elif settings.llm_provider == "generic_http":
        provider = GenericHTTPProvider(base_url=settings.llm_base_url, api_key=settings.llm_api_key)
    else:
        raise RuntimeError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")
    return LLMClient(provider)

