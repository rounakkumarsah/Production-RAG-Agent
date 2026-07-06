import io
from docx import Document as DocxDocument
from app.services.parsers.base import DocumentParser, ExtractionResult, ExtractedPage
from app.utils.logging import get_logger

logger = get_logger(__name__)

class DocxParser(DocumentParser):
    def parse(self, content: bytes, filename: str) -> ExtractionResult:
        try:
            doc = DocxDocument(io.BytesIO(content))
        except Exception as exc:
            raise ValueError(f"Cannot open DOCX '{filename}': {exc}") from exc
            
        full_text = "\n".join(paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip())
        
        if not full_text:
            raise ValueError(f"DOCX '{filename}' contains no extractable text.")
            
        # Treat whole doc as a single page for chunking purposes
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
            file_type="docx",
            parser_used="python-docx",
            ocr_used=False,
            ocr_engine=None,
            extraction_method="native"
        )
