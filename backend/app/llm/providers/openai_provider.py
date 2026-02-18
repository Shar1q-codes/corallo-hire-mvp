from __future__ import annotations

import httpx

from app.llm.models import LLMRequest, LLMResponse, ProviderError


class OpenAIProvider:
    def __init__(self, *, api_key: str, base_url: str = "https://api.openai.com/v1") -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def generate(self, request: LLMRequest) -> LLMResponse:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": request.model,
            "messages": request.messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        url = f"{self.base_url}/chat/completions"
        try:
            with httpx.Client(timeout=request.timeout_seconds) as client:
                response = client.post(url, headers=headers, json=payload)
            if response.status_code >= 500:
                raise ProviderError("Provider server error.", transient=True)
            if response.status_code >= 400:
                raise ProviderError(f"Provider request failed with status {response.status_code}.")
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            if not isinstance(content, str):
                raise ProviderError("Provider response is missing text content.")
            return LLMResponse(raw_text=content, provider_meta={"id": data.get("id")})
        except httpx.TimeoutException as exc:
            raise ProviderError("Provider timeout.", transient=True) from exc
        except httpx.TransportError as exc:
            raise ProviderError("Provider network error.", transient=True) from exc

