from app.config import get_settings
from app.services.embeddings.base import BaseEmbeddingProvider
from app.services.embeddings.gemini import GeminiEmbeddingProvider


def get_embedding_provider() -> BaseEmbeddingProvider:
    """
    Factory function to retrieve the configured embedding provider.
    Future extensions (e.g., OpenAI, Voyage) can be added here
    without modifying the caller's logic.
    """
    settings = get_settings()
    
    # In the future, this could inspect an `EMBEDDING_PROVIDER` setting.
    # For now, Gemini is the only implemented provider.
    return GeminiEmbeddingProvider()
