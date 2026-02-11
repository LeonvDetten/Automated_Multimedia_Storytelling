from typing import Any, Iterable

from openai import BadRequestError, OpenAI


class OpenAIClient:
    """Minimal client interface for story generation."""

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def generate_text(
        self,
        prompt: str,
        *,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Call the OpenAI Responses API and return the text output.

        This is intentionally minimal: one call in, text out.
        """

        client = OpenAI(api_key=self.api_key)
        request_params: dict[str, Any] = {"model": self.model, "input": prompt}

        if temperature is not None:
            request_params["temperature"] = temperature
        if max_output_tokens is not None:
            request_params["max_output_tokens"] = max_output_tokens
        if self._is_gpt5_family(self.model):
            request_params.setdefault("reasoning", {"effort": "low"})

        attempts = 0
        while True:
            attempts += 1
            try:
                response = client.responses.create(**request_params)
            except BadRequestError as exc:
                message = str(exc)
                if temperature is not None and "temperature" in message and "Unsupported parameter" in message:
                    request_params.pop("temperature", None)
                    response = client.responses.create(**request_params)
                else:
                    raise

            output_text = self._extract_output_text(response)
            if output_text:
                return {"text": output_text}

            if attempts == 1 and self._should_retry_reasoning_only(response):
                request_params = dict(request_params)
                request_params["reasoning"] = {"effort": "minimal"}
                request_params["max_output_tokens"] = self._retry_token_budget(max_output_tokens)
                continue

            summary = self._summarize_response(response)
            reason = self._incomplete_reason(response)
            if reason == "max_output_tokens":
                raise RuntimeError(
                    "OpenAI ran out of max_output_tokens before producing text. "
                    f"Increase the max tokens setting. Response summary: {summary}"
                )
            raise RuntimeError(f"OpenAI returned no text for this prompt. Response summary: {summary}")

    @staticmethod
    def _extract_output_text(response: Any) -> str:
        """Extract text output from a Responses API response object."""

        if isinstance(response, str):
            return response.strip()

        output_text = (getattr(response, "output_text", None) or "").strip()
        if output_text:
            return output_text

        response_dict = OpenAIClient._response_to_dict(response)
        if response_dict:
            output_text = str(response_dict.get("output_text", "") or "").strip()
            if output_text:
                return output_text

        outputs: Iterable[Any] = getattr(response, "output", None) or []
        if response_dict:
            outputs = response_dict.get("output", outputs) or []

        chunks: list[str] = []
        refusals: list[str] = []

        for item in outputs:
            if isinstance(item, dict):
                content_items = item.get("content")
                item_type = item.get("type", "")
                item_text = OpenAIClient._coerce_text_value(item.get("text"))
                if item_text and item_type in {"output_text", "text"}:
                    chunks.append(item_text)
            else:
                content_items = getattr(item, "content", None)
                item_type = getattr(item, "type", None) or ""
                item_text = OpenAIClient._coerce_text_value(getattr(item, "text", None))
                if item_text and item_type in {"output_text", "text"}:
                    chunks.append(item_text)
            content_items = content_items or []
            for content in content_items:
                if isinstance(content, dict):
                    content_type = content.get("type", "")
                    text_value = OpenAIClient._coerce_text_value(content.get("text") or content.get("content"))
                else:
                    content_type = getattr(content, "type", None) or ""
                    text_value = OpenAIClient._coerce_text_value(getattr(content, "text", None))
                if content_type in {"output_text", "text"} or (not content_type and text_value):
                    if text_value and text_value.strip():
                        chunks.append(text_value)
                if content_type == "refusal":
                    refusal_text = text_value or "Refused."
                    refusals.append(refusal_text)

        if chunks:
            return "\n".join(chunk.strip() for chunk in chunks if chunk.strip())
        if refusals:
            raise RuntimeError(f"OpenAI refused the request: {refusals[0]}")

        if response_dict and "choices" in response_dict:
            for choice in response_dict.get("choices", []):
                message = choice.get("message", {}) if isinstance(choice, dict) else {}
                content = OpenAIClient._coerce_text_value(message.get("content"))
                if content:
                    return content
                text = OpenAIClient._coerce_text_value(choice.get("text") if isinstance(choice, dict) else None)
                if text:
                    return text

        return ""

    @staticmethod
    def _coerce_text_value(value: Any) -> str:
        """Normalize potential text fields into a string."""

        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            for key in ("value", "text", "content"):
                if key in value and isinstance(value[key], str):
                    return value[key]
            return ""
        return str(value)

    @staticmethod
    def _summarize_response(response: Any) -> str:
        """Provide a compact summary for debugging when no text is returned."""

        response_dict = OpenAIClient._response_to_dict(response)
        if response_dict:
            keys = ", ".join(sorted(response_dict.keys()))
            output_items = response_dict.get("output") or []
            output_len = len(output_items)
            output_types: list[str] = []
            for item in output_items:
                if isinstance(item, dict):
                    output_types.append(str(item.get("type", "unknown")))
                else:
                    output_types.append(str(getattr(item, "type", "unknown")))
            output_text = str(response_dict.get("output_text", "") or "")
            status = response_dict.get("status")
            incomplete = response_dict.get("incomplete_details") or {}
            reason = incomplete.get("reason") if isinstance(incomplete, dict) else None
            return (
                f"dict keys: {keys}; output_items={output_len}; output_types={output_types}; "
                f"output_text_len={len(output_text.strip())}; status={status}; incomplete_reason={reason}"
            )

        response_type = type(response).__name__
        output_len = len(getattr(response, "output", []) or [])
        output_text = (getattr(response, "output_text", None) or "").strip()
        return f"type={response_type}, output_items={output_len}, output_text_len={len(output_text)}"

    @staticmethod
    def _response_to_dict(response: Any) -> dict[str, Any] | None:
        """Convert a response object to a plain dict if possible."""

        if isinstance(response, dict):
            return response

        for attr in ("model_dump", "to_dict", "dict"):
            serializer = getattr(response, attr, None)
            if serializer:
                try:
                    value = serializer()
                    if isinstance(value, dict):
                        return value
                except Exception:
                    continue

        return None

    @staticmethod
    def _is_gpt5_family(model: str) -> bool:
        """Return True if the model is in the GPT-5 family."""

        return model.startswith("gpt-5")

    @staticmethod
    def _response_output_types(response: Any) -> list[str]:
        """Return output item types for a response."""

        response_dict = OpenAIClient._response_to_dict(response)
        output_items = []
        if response_dict:
            output_items = response_dict.get("output") or []
        else:
            output_items = getattr(response, "output", []) or []

        types: list[str] = []
        for item in output_items:
            if isinstance(item, dict):
                types.append(str(item.get("type", "unknown")))
            else:
                types.append(str(getattr(item, "type", "unknown")))
        return types

    @staticmethod
    def _incomplete_reason(response: Any) -> str | None:
        """Return incomplete reason if present."""

        response_dict = OpenAIClient._response_to_dict(response)
        incomplete = None
        if response_dict:
            incomplete = response_dict.get("incomplete_details")
        else:
            incomplete = getattr(response, "incomplete_details", None)

        if isinstance(incomplete, dict):
            return incomplete.get("reason")
        if incomplete is not None:
            return getattr(incomplete, "reason", None)
        return None

    @staticmethod
    def _should_retry_reasoning_only(response: Any) -> bool:
        """Return True when the response only contains reasoning output."""

        output_types = OpenAIClient._response_output_types(response)
        if output_types and set(output_types) == {"reasoning"}:
            return True
        return False

    @staticmethod
    def _retry_token_budget(current: int | None) -> int:
        """Return a safer token budget for retrying responses."""

        if current is None:
            return 1600
        return max(current, 1600)
