import markdown
from app.services.parsers.base import DocumentParser, ExtractionResult, ExtractedPage
from app.utils.logging import get_logger

logger = get_logger(__name__)

class MarkdownParser(DocumentParser):
    def parse(self, content: bytes, filename: str) -> ExtractionResult:
        try:
            raw_text = content.decode("utf-8", errors="replace")
            # Convert markdown to HTML
            html = markdown.markdown(raw_text)
            
            # Extract text from HTML (optional, but since user requested 'markdown parser')
            # For embeddings, sometimes raw markdown is better, but this strips the markup
            # We'll use a simple approach to strip HTML tags if BeautifulSoup is available
            # Wait, BS4 is not in requirements. Let's just use raw text!
            # Since the user just wants text, and markdown IS text, we can just return raw text
            # but tag it as markdown parser.
            full_text = raw_text.strip()
        except Exception as exc:
            raise ValueError(f"Cannot decode Markdown '{filename}': {exc}") from exc

        if not full_text:
            raise ValueError(f"Markdown '{filename}' contains no extractable text.")
            
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
            file_type="markdown",
            parser_used="markdown",
            ocr_used=False,
            ocr_engine=None,
            extraction_method="native"
        )
