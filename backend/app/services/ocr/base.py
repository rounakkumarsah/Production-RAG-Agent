import abc
from PIL import Image

class OCRProvider(abc.ABC):
    """
    Abstract base class for OCR Engines.
    """
    @abc.abstractmethod
    def name(self) -> str:
        """Return the name of the OCR engine."""
        pass

    @abc.abstractmethod
    def extract_text(self, image: Image.Image) -> str:
        """
        Extract text from a PIL Image.
        Returns the extracted text as a string.
        """
        pass

class OCRService:
    """
    Service facade for OCR providers.
    Uses PaddleOCR by default, falls back to Tesseract.
    """
    def __init__(self, primary_provider: OCRProvider, fallback_provider: OCRProvider | None = None):
        self.primary = primary_provider
        self.fallback = fallback_provider

    def extract_text(self, image: Image.Image) -> tuple[str, str]:
        """
        Extract text and return a tuple: (extracted_text, engine_used).
        """
        try:
            return self.primary.extract_text(image), self.primary.name()
        except Exception as e:
            if self.fallback:
                # Log warning in production, but here we just fallback
                return self.fallback.extract_text(image), self.fallback.name()
            raise e
