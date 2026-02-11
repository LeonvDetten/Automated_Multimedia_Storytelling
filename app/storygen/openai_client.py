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
        if not output_text:
            raise RuntimeError("OpenAI returned no text for this prompt.")

        return {"text": output_text}

    @staticmethod
    def _extract_output_text(response: Any) -> str:
        """Extract text output from a Responses API response object."""

        if isinstance(response, str):
            return response.strip()

        output_text = (getattr(response, "output_text", None) or "").strip()
        if output_text:
            return output_text

        outputs: Iterable[Any] = getattr(response, "output", None) or []
        chunks: list[str] = []
        refusals: list[str] = []

        for item in outputs:
            content_items = getattr(item, "content", None) if not isinstance(item, dict) else item.get("content")
            content_items = content_items or []
            for content in content_items:
                if isinstance(content, dict):
                    content_type = content.get("type", "")
                    text_value = content.get("text", "") or content.get("content", "")
                else:
                    content_type = getattr(content, "type", None) or ""
                    text_value = getattr(content, "text", None) or ""
                if content_type == "output_text":
                    if text_value and str(text_value).strip():
                        chunks.append(str(text_value))
                if content_type == "refusal":
                    refusal_text = text_value or "Refused."
                    refusals.append(str(refusal_text))

        if chunks:
            return "\n".join(chunk.strip() for chunk in chunks if chunk.strip())
        if refusals:
            raise RuntimeError(f"OpenAI refused the request: {refusals[0]}")

        return ""
