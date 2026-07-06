import google.generativeai as genai
from typing import Any

from app.config import get_settings
from app.services.embeddings.base import BaseEmbeddingProvider


class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    """
    Synchronous Google Gemini implementation.
    The orchestrator handles batch sizing and asyncio.to_thread wrappers.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        genai.configure(api_key=self.settings.GOOGLE_API_KEY)
        self.model = self.settings.GEMINI_EMBEDDING_MODEL

    def embed_batch(self, texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
        if not texts:
            return []

        result: Any = genai.embed_content(
            model=self.model,
            content=texts,
            task_type=task_type,
        )

        raw = result["embedding"]

        # Handle list vs scalar outputs based on single/multi string requests
        if isinstance(raw[0], float):
            return [raw]
        return [list(v) for v in raw]
