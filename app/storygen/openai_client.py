from typing import Any
from openai import OpenAI


class OpenAIClient:
    """Minimal client interface for story generation."""

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def generate_text(self, prompt: str) -> dict[str, Any]:
        """Call the OpenAI Responses API and return the text output.

        This is intentionally minimal: one call in, text out.
        """

        client = OpenAI(api_key=self.api_key)
        response = client.responses.create(model=self.model, input=prompt)

        output_text = (response.output_text or "").strip()
        if not output_text:
            raise RuntimeError("OpenAI returned no text for this prompt.")

        return {"text": output_text}
