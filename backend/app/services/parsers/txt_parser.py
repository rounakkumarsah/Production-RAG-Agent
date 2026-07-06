from app.services.parsers.base import DocumentParser, ExtractionResult, ExtractedPage
from app.utils.logging import get_logger

logger = get_logger(__name__)

class TxtParser(DocumentParser):
    def parse(self, content: bytes, filename: str) -> ExtractionResult:
        try:
            full_text = content.decode("utf-8", errors="replace").strip()
        except Exception as exc:
            raise ValueError(f"Cannot decode TXT '{filename}': {exc}") from exc

        full_text = full_text.strip()
        if not full_text:
            raise ValueError(f"TXT '{filename}' contains no extractable text.")
            
        page = ExtractedPage(
            page_number=1,
            text=full_text,
            char_start=0,
            char_end=len(full_text)
        )
        
        return ExtractionResult(
            pages=[page],
            full_text=full_text,
            page_count=1,
            char_count=len(full_text),
            file_type="txt",
            parser_used="utf8",
            ocr_used=False,
            ocr_engine=None,
            extraction_method="native"
        )
