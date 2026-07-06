import fitz  # PyMuPDF
from PIL import Image
import io
from app.services.parsers.base import DocumentParser, ExtractionResult, ExtractedPage
from app.services.ocr import get_ocr_service
from app.utils.logging import get_logger

logger = get_logger(__name__)

class PDFParser(DocumentParser):
    """
    Parses PDFs. Automatically falls back to OCR if the native text extraction
    yields very little or no content.
    """
    
    def __init__(self, min_chars_per_page_for_ocr: int = 20):
        self.min_chars = min_chars_per_page_for_ocr
        self.ocr_service = get_ocr_service()

    def parse(self, content: bytes, filename: str) -> ExtractionResult:
        try:
            doc: fitz.Document = fitz.open(stream=content, filetype="pdf")
        except Exception as exc:
            raise ValueError(f"Cannot open PDF '{filename}': {exc}") from exc

        pages: list[ExtractedPage] = []
        parts: list[str] = []
        cursor = 0
        total_pages: int = len(doc)
        
        ocr_was_used = False
        engines_used = set()
        
        for page_index in range(total_pages):
            page: fitz.Page = doc[page_index]
            page_text: str = page.get_text("markdown").strip()
            
            # If native text is too little, we attempt OCR
            if len(page_text) < self.min_chars:
                logger.debug("Page %d of '%s' has little/no text, attempting OCR", page_index + 1, filename)
                try:
                    # Render page to image
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x resolution for better OCR
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    
                    ocr_text, engine_name = self.ocr_service.extract_text(img)
                    
                    if ocr_text.strip():
                        page_text = ocr_text.strip()
                        ocr_was_used = True
                        engines_used.add(engine_name)
                except Exception as e:
                    logger.warning("OCR failed on page %d of '%s': %s", page_index + 1, filename, e)

            if not page_text:
                continue

            start = cursor
            end = start + len(page_text)

            pages.append(ExtractedPage(
                page_number=page_index + 1,
                text=page_text,
                char_start=start,
                char_end=end,
            ))
            parts.append(page_text)
            cursor = end + 2

        doc.close()

        if not pages:
            raise ValueError(f"PDF '{filename}' contains no extractable text even after OCR.")

        full_text = "\n\n".join(p.text for p in pages)

        engine_str = ",".join(engines_used) if engines_used else None
        extraction_method = "ocr" if ocr_was_used else "native"

        return ExtractionResult(
            pages=pages,
            full_text=full_text,
            page_count=total_pages,
            char_count=len(full_text),
            file_type="pdf",
            parser_used="PyMuPDF",
            ocr_used=ocr_was_used,
            ocr_engine=engine_str,
            extraction_method=extraction_method
        )
