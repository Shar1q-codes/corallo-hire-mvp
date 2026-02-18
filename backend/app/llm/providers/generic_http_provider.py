from __future__ import annotations

import httpx

from app.llm.models import LLMRequest, LLMResponse, ProviderError


class GenericHTTPProvider:
    def __init__(self, *, base_url: str, api_key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def generate(self, request: LLMRequest) -> LLMResponse:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": request.model,
            "messages": request.messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        try:
            with httpx.Client(timeout=request.timeout_seconds) as client:
                response = client.post(self.base_url, headers=headers, json=payload)
            if response.status_code >= 500:
                raise ProviderError("Provider server error.", transient=True)
            if response.status_code >= 400:
                raise ProviderError(f"Provider request failed with status {response.status_code}.")
            data = response.json()
            raw_text = data.get("text") or data.get("output_text") or data.get("content")
            if not isinstance(raw_text, str):
                raise ProviderError("Provider response missing text field.")
            return LLMResponse(raw_text=raw_text, provider_meta={"provider": "generic_http"})
        except httpx.TimeoutException as exc:
            raise ProviderError("Provider timeout.", transient=True) from exc
        except httpx.TransportError as exc:
            raise ProviderError("Provider network error.", transient=True) from exc

