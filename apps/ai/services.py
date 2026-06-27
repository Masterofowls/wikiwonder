"""Cerebras AI integration via cerebras-cloud-sdk."""
from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)


class CerebrasService:
    """Wrapper around Cerebras Cloud SDK (gpt-oss-120b and compatible models)."""

    def __init__(self):
        self.api_key = settings.CEREBRAS_API_KEY
        self.model = settings.CEREBRAS_MODEL
        self.max_completion_tokens = getattr(settings, "CEREBRAS_MAX_COMPLETION_TOKENS", 8192)
        self.temperature = getattr(settings, "CEREBRAS_TEMPERATURE", 0.2)
        self.top_p = getattr(settings, "CEREBRAS_TOP_P", 1.0)
        self.reasoning_effort = getattr(settings, "CEREBRAS_REASONING_EFFORT", "medium")
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

    def _completion_kwargs(
        self,
        *,
        max_completion_tokens: int | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        reasoning_effort: str | None = None,
        stream: bool = False,
    ) -> dict[str, Any]:
        return {
            "model": self.model,
            "max_completion_tokens": max_completion_tokens or self.max_completion_tokens,
            "temperature": self.temperature if temperature is None else temperature,
            "top_p": self.top_p if top_p is None else top_p,
            "reasoning_effort": reasoning_effort or self.reasoning_effort,
            "stream": stream,
        }

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        max_completion_tokens: int | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        reasoning_effort: str | None = None,
    ) -> str:
        """Non-streaming chat completion."""
        completion = self.client.chat.completions.create(
            messages=messages,
            **self._completion_kwargs(
                max_completion_tokens=max_completion_tokens,
                temperature=temperature,
                top_p=top_p,
                reasoning_effort=reasoning_effort,
                stream=False,
            ),
        )
        return completion.choices[0].message.content or ""

    def chat_stream(
        self,
        messages: list[dict[str, str]],
        *,
        max_completion_tokens: int | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        reasoning_effort: str | None = None,
    ) -> Iterator[str]:
        """Streaming chat completion — yields text deltas."""
        stream = self.client.chat.completions.create(
            messages=messages,
            **self._completion_kwargs(
                max_completion_tokens=max_completion_tokens,
                temperature=temperature,
                top_p=top_p,
                reasoning_effort=reasoning_effort,
                stream=True,
            ),
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            if delta:
                yield delta

    def prompt(
        self,
        user_content: str,
        *,
        system: str | None = None,
        max_completion_tokens: int | None = None,
        temperature: float | None = None,
        reasoning_effort: str | None = None,
    ) -> str:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user_content})
        return self.chat(
            messages,
            max_completion_tokens=max_completion_tokens,
            temperature=temperature,
            reasoning_effort=reasoning_effort,
        )

    def format_to_markdown(self, raw_text: str, title: str = "") -> str:
        """Convert raw text into well-structured markdown wiki content."""
        system = (
            "You are a wiki editor. Convert input text into clean, well-structured Markdown. "
            "Use ## for main sections, ### for subsections. Add a brief intro paragraph. "
            "Use bullet lists, code blocks, and tables where appropriate. "
            "Output ONLY markdown, no explanations."
        )
        prompt = f"Title: {title}\n\nRaw content:\n{raw_text}" if title else raw_text
        return self.prompt(
            prompt,
            system=system,
            max_completion_tokens=min(self.max_completion_tokens, 8192),
            temperature=0.2,
        )

    def suggest_title(self, raw_text: str) -> str:
        system = "Suggest a concise wiki page title. Output ONLY the title, nothing else."
        return self.prompt(
            raw_text[:2000],
            system=system,
            max_completion_tokens=64,
            temperature=0.2,
        ).strip().strip('"')

    def generate_summary(self, markdown_content: str) -> str:
        system = "Write a 1-2 sentence summary for a wiki page preview. Output ONLY the summary."
        return self.prompt(
            markdown_content[:3000],
            system=system,
            max_completion_tokens=200,
            temperature=0.3,
        ).strip()

    def enrich_import(self, raw_text: str, title: str = "") -> dict[str, str]:
        """Format markdown and derive title + summary in one pass where possible."""
        markdown = self.format_to_markdown(raw_text, title=title)
        resolved_title = title or self.suggest_title(raw_text)
        summary = self.generate_summary(markdown)
        return {
            "title": resolved_title,
            "markdown": markdown,
            "summary": summary,
        }

    def summarize_wiki_page(self, title: str, markdown_content: str) -> str:
        system = (
            "You summarize wiki articles for readers. Write 3–5 concise bullet points "
            "covering the main ideas. Use plain language. Output markdown bullets only."
        )
        prompt = f"Title: {title}\n\nArticle:\n{markdown_content[:10000]}"
        return self.prompt(
            prompt,
            system=system,
            max_completion_tokens=600,
            temperature=0.3,
        ).strip()

    def ask_about_wiki_page(self, title: str, markdown_content: str, question: str) -> str:
        system = (
            "You answer questions about a wiki article. Use ONLY information from the article. "
            "If the answer is not in the article, say you cannot find it in this page. "
            "Be concise and helpful. Output markdown."
        )
        prompt = (
            f"Title: {title}\n\nArticle:\n{markdown_content[:10000]}\n\n"
            f"Question: {question.strip()}"
        )
        return self.prompt(
            prompt,
            system=system,
            max_completion_tokens=800,
            temperature=0.25,
        ).strip()


def get_ai_service() -> CerebrasService:
    return CerebrasService()
