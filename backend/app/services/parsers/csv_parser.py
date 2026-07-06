import io
import pandas as pd
from app.services.parsers.base import DocumentParser, ExtractionResult, ExtractedPage
from app.utils.logging import get_logger

logger = get_logger(__name__)

class CsvParser(DocumentParser):
    def parse(self, content: bytes, filename: str) -> ExtractionResult:
        try:
            # Read CSV and convert to string representation
            df = pd.read_csv(io.BytesIO(content))
            full_text = df.to_string(index=False)
        except Exception as exc:
            raise ValueError(f"Cannot open CSV '{filename}': {exc}") from exc

        if not full_text or full_text.strip() == "Empty DataFrame\nColumns: []\nIndex: []":
            raise ValueError(f"CSV '{filename}' contains no extractable text.")
            
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
            file_type="csv",
            parser_used="pandas",
            ocr_used=False,
            ocr_engine=None,
            extraction_method="native"
        )
