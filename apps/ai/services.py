"""Cerebras AI integration for content formatting and enrichment."""
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


class CerebrasService:
    """Wrapper around Cerebras Cloud SDK."""

    def __init__(self):
        self.api_key = settings.CEREBRAS_API_KEY
        self.model = settings.CEREBRAS_MODEL
        self._client = None

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    @property
    def client(self):
        if not self.is_configured:
            raise ValueError("CEREBRAS_API_KEY is not configured")
        if self._client is None:
            from cerebras.cloud.sdk import Cerebras
            self._client = Cerebras(api_key=self.api_key)
        return self._client

    def chat(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.2,
        reasoning_effort: str = "medium",
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        completion = self.client.chat.completions.create(
            messages=messages,
            model=self.model,
            max_completion_tokens=max_tokens,
            temperature=temperature,
            top_p=1,
            stream=False,
            reasoning_effort=reasoning_effort,
        )
        return completion.choices[0].message.content or ""

    def format_to_markdown(self, raw_text: str, title: str = "") -> str:
        """Convert raw text into well-structured markdown wiki content."""
        system = (
            "You are a wiki editor. Convert input text into clean, well-structured Markdown. "
            "Use ## for main sections, ### for subsections. Add a brief intro paragraph. "
            "Use bullet lists, code blocks, and tables where appropriate. "
            "Output ONLY markdown, no explanations."
        )
        prompt = f"Title: {title}\n\nRaw content:\n{raw_text}" if title else raw_text
        return self.chat(prompt, system=system, max_tokens=8192)

    def suggest_title(self, raw_text: str) -> str:
        system = "Suggest a concise wiki page title. Output ONLY the title, nothing else."
        return self.chat(raw_text[:2000], system=system, max_tokens=64).strip().strip('"')

    def generate_summary(self, markdown_content: str) -> str:
        system = "Write a 1-2 sentence summary for a wiki page preview. Output ONLY the summary."
        return self.chat(markdown_content[:3000], system=system, max_tokens=200)


def get_ai_service() -> CerebrasService:
    return CerebrasService()
