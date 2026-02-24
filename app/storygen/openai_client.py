import os
from typing import Any

from langfuse.openai import openai as langfuse_openai
from openai import BadRequestError


class OpenAIClient:
    """Minimal client interface for story generation."""

    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        langfuse_public_key: str | None = None,
        langfuse_secret_key: str | None = None,
        langfuse_host: str | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.langfuse_public_key = langfuse_public_key or ""
        self.langfuse_secret_key = langfuse_secret_key or ""
        self.langfuse_host = langfuse_host or ""

    def generate_text(
        self,
        prompt: str,
        *,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Call the OpenAI Responses API and return the text output."""

        client = self._build_openai_client()
        params: dict[str, Any] = {"model": self.model, "input": prompt}
        temperature_applied: bool | None = None

        if temperature is not None:
            params["temperature"] = temperature
            temperature_applied = True
        if max_output_tokens is not None:
            params["max_output_tokens"] = max_output_tokens
        if self._is_gpt5_family(self.model):
            params.setdefault("reasoning", {"effort": "minimal"})

        response, temperature_applied = self._call_with_temperature_fallback(client, params, temperature)
        text, output_types = self._parse_response(response)
        if text:
            return {"text": text, "temperature_applied": temperature_applied}

        if self._should_retry_reasoning_only(output_types):
            retry_params = dict(params)
            retry_params["reasoning"] = {"effort": "minimal"}
            retry_params["max_output_tokens"] = self._retry_token_budget(max_output_tokens)
            response, temperature_applied = self._call_with_temperature_fallback(client, retry_params, temperature)
            text, output_types = self._parse_response(response)
            if text:
                return {"text": text, "temperature_applied": temperature_applied}

        reason = self._incomplete_reason(response)
        summary = self._summarize_response(response, output_types)
        if reason == "max_output_tokens":
            raise RuntimeError(
                "OpenAI ran out of max_output_tokens before producing text. "
                f"Increase the max tokens setting. Response summary: {summary}"
            )
        raise RuntimeError(f"OpenAI returned no text for this prompt. Response summary: {summary}")

    @staticmethod
    def _call_with_temperature_fallback(
        client: Any, params: dict[str, Any], temperature: float | None
    ) -> tuple[Any, bool | None]:
        """Call the API; retry without temperature if the model rejects it."""

        try:
            return client.responses.create(**params), temperature is not None
        except BadRequestError as exc:
            message = str(exc)
            if temperature is not None and "temperature" in message and "Unsupported parameter" in message:
                clean_params = dict(params)
                clean_params.pop("temperature", None)
                return client.responses.create(**clean_params), False
            raise

    @staticmethod
    def _parse_response(response: Any) -> tuple[str, list[str]]:
        """Return (text, output_types) from a Responses API response."""

        if isinstance(response, str):
            return response.strip(), []

        response_dict = OpenAIClient._as_dict(response)
        output_text = (getattr(response, "output_text", None) or "").strip()
        if not output_text and response_dict:
            output_text = str(response_dict.get("output_text", "") or "").strip()
        if output_text:
            return output_text, []

        outputs = (response_dict.get("output") if response_dict else None) or getattr(response, "output", []) or []
        output_types: list[str] = []

        for item in outputs:
            text, item_type = OpenAIClient._extract_text_from_item(item)
            if item_type:
                output_types.append(item_type)
            if text:
                return text, output_types

        return "", output_types

    @staticmethod
    def _extract_text_from_item(item: Any) -> tuple[str, str | None]:
        """Extract text from a single output item, if present."""

        if isinstance(item, dict):
            item_type = item.get("type")
            if item_type in {"output_text", "text"}:
                text_value = item.get("text")
                if isinstance(text_value, str) and text_value.strip():
                    return text_value.strip(), item_type
            if item_type == "message":
                for content in item.get("content", []) or []:
                    if isinstance(content, dict) and content.get("type") in {"output_text", "text"}:
                        text_value = content.get("text")
                        if isinstance(text_value, str) and text_value.strip():
                            return text_value.strip(), item_type
            return "", item_type

        item_type = getattr(item, "type", None)
        if item_type in {"output_text", "text"}:
            text_value = getattr(item, "text", None)
            if isinstance(text_value, str) and text_value.strip():
                return text_value.strip(), item_type
        if item_type == "message":
            for content in getattr(item, "content", []) or []:
                content_type = getattr(content, "type", None)
                if content_type in {"output_text", "text"}:
                    text_value = getattr(content, "text", None)
                    if isinstance(text_value, str) and text_value.strip():
                        return text_value.strip(), item_type
        return "", item_type

    @staticmethod
    def _summarize_response(response: Any, output_types: list[str]) -> str:
        """Provide a compact summary for debugging when no text is returned."""

        response_dict = OpenAIClient._as_dict(response)
        status = response_dict.get("status") if response_dict else getattr(response, "status", None)
        output_len = len((response_dict.get("output") if response_dict else None) or getattr(response, "output", []) or [])
        output_text = (getattr(response, "output_text", None) or "").strip()
        return (
            f"type={type(response).__name__}; output_items={output_len}; "
            f"output_types={output_types}; output_text_len={len(output_text)}; status={status}"
        )

    @staticmethod
    def _as_dict(response: Any) -> dict[str, Any] | None:
        """Convert response to dict when possible."""

        if isinstance(response, dict):
            return response
        serializer = getattr(response, "model_dump", None)
        if serializer:
            try:
                value = serializer()
                if isinstance(value, dict):
                    return value
            except Exception:
                return None
        return None

    @staticmethod
    def _incomplete_reason(response: Any) -> str | None:
        """Return incomplete reason if present."""

        response_dict = OpenAIClient._as_dict(response)
        incomplete = response_dict.get("incomplete_details") if response_dict else getattr(response, "incomplete_details", None)
        if isinstance(incomplete, dict):
            return incomplete.get("reason")
        if incomplete is not None:
            return getattr(incomplete, "reason", None)
        return None

    @staticmethod
    def _should_retry_reasoning_only(output_types: list[str]) -> bool:
        """Return True when the response only contains reasoning output."""

        return bool(output_types) and set(output_types) == {"reasoning"}

    @staticmethod
    def _retry_token_budget(current: int | None) -> int:
        """Return a safer token budget for retrying responses."""

        if current is None:
            return 1600
        return max(current, 1600)

    @staticmethod
    def _is_gpt5_family(model: str) -> bool:
        """Return True if the model is in the GPT-5 family."""

        return model.startswith("gpt-5")

    def _build_openai_client(self) -> Any:
        """Return a Langfuse-instrumented OpenAI client."""

        if not self.langfuse_public_key or not self.langfuse_secret_key:
            raise RuntimeError("Langfuse keys are required (LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY).")

        self._apply_langfuse_env()
        return langfuse_openai.OpenAI(api_key=self.api_key)

    def _apply_langfuse_env(self) -> None:
        """Expose Langfuse settings as environment vars for the wrapper."""

        os.environ["LANGFUSE_PUBLIC_KEY"] = self.langfuse_public_key
        os.environ["LANGFUSE_SECRET_KEY"] = self.langfuse_secret_key
        if self.langfuse_host:
            os.environ["LANGFUSE_HOST"] = self.langfuse_host
