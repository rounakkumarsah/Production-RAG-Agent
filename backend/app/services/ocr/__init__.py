from app.services.ocr.base import OCRService, OCRProvider
from app.services.ocr.paddle_provider import PaddleOCRProvider
from app.services.ocr.tesseract_provider import TesseractProvider
import logging

logger = logging.getLogger(__name__)

# Initialize providers
primary_provider = PaddleOCRProvider()
fallback_provider = TesseractProvider()

# Single service instance used by parsers
ocr_service = OCRService(
    primary_provider=primary_provider,
    fallback_provider=fallback_provider
)

def get_ocr_service() -> OCRService:
    return ocr_service
