import io
from PIL import Image
from app.services.parsers.base import DocumentParser, ExtractionResult, ExtractedPage
from app.services.ocr import get_ocr_service
from app.utils.logging import get_logger

logger = get_logger(__name__)

class ImageParser(DocumentParser):
    """
    Parses Image files using OCR.
    """
    
    def __init__(self):
        self.ocr_service = get_ocr_service()

    def parse(self, content: bytes, filename: str) -> ExtractionResult:
        try:
            img = Image.open(io.BytesIO(content))
            # verify image is valid
            img.verify()
            
            # reopening because verify() seeks to end
            img = Image.open(io.BytesIO(content))
        except Exception as exc:
            raise ValueError(f"Cannot open Image '{filename}': {exc}") from exc

        try:
            full_text, engine_name = self.ocr_service.extract_text(img)
            full_text = full_text.strip()
        except Exception as exc:
            raise ValueError(f"OCR failed for Image '{filename}': {exc}") from exc

        if not full_text:
            raise ValueError(f"Image '{filename}' contains no extractable text even after OCR.")
            
        page = ExtractedPage(
            page_number=1,
            text=full_text,
            char_start=0,
            char_end=len(full_text)
        )
        
        # Determine format extension
        fmt = (img.format or "image").lower()
        
        return ExtractionResult(
            pages=[page],
            full_text=full_text,
            page_count=1,
            char_count=len(full_text),
            file_type=fmt,
            parser_used="ImageParser",
            ocr_used=True,
            ocr_engine=engine_name,
            extraction_method="ocr"
        )
