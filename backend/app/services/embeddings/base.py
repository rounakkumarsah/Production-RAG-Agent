from abc import ABC, abstractmethod
from typing import Any

class BaseEmbeddingProvider(ABC):
    """
    Abstract base class for all embedding providers (Gemini, OpenAI, etc).
    """

    @abstractmethod
    def embed_batch(self, texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
        """
        Embed a batch of texts synchronously.
        This must be run inside `asyncio.to_thread` by the orchestrator.

        Args:
            texts: List of strings to embed.
            task_type: Hint for the provider (if supported).

        Returns:
            A list of float vectors corresponding to the input texts.
            
        Raises:
            Any provider-specific exceptions which the orchestrator is responsible for catching and retrying.
        """
        pass
