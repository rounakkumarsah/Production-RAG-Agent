import mimetypes
from app.services.parsers.base import DocumentParser
from app.services.parsers.pdf_parser import PDFParser
from app.services.parsers.docx_parser import DocxParser
from app.services.parsers.pptx_parser import PptxParser
from app.services.parsers.xlsx_parser import XlsxParser
from app.services.parsers.csv_parser import CsvParser
from app.services.parsers.txt_parser import TxtParser
from app.services.parsers.markdown_parser import MarkdownParser
from app.services.parsers.image_parser import ImageParser
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Initialize singletons
_parsers = {
    "pdf": PDFParser(),
    "docx": DocxParser(),
    "pptx": PptxParser(),
    "xlsx": XlsxParser(),
    "csv": CsvParser(),
    "txt": TxtParser(),
    "markdown": MarkdownParser(),
    "image": ImageParser(),
}

def get_parser_for_file(filename: str, mime_type: str = "") -> DocumentParser:
    """
    Returns the appropriate DocumentParser based on filename and mime_type.
    """
    ext = filename.lower().split('.')[-1] if '.' in filename else ""
    
    if not mime_type:
        mime_type = mimetypes.guess_type(filename)[0] or ""

    # 1. Check by extension first
    if ext == "pdf":
        return _parsers["pdf"]
    elif ext == "docx":
        return _parsers["docx"]
    elif ext == "pptx":
        return _parsers["pptx"]
    elif ext == "xlsx":
        return _parsers["xlsx"]
    elif ext == "csv":
        return _parsers["csv"]
    elif ext in ("md", "markdown"):
        return _parsers["markdown"]
    elif ext in ("txt", "log", "json"):  # fallback for text files
        return _parsers["txt"]
    elif ext in ("png", "jpg", "jpeg", "tiff", "bmp", "webp"):
        return _parsers["image"]

    # 2. Check by MIME type
    if "pdf" in mime_type:
        return _parsers["pdf"]
    elif "wordprocessingml.document" in mime_type:
        return _parsers["docx"]
    elif "presentationml.presentation" in mime_type:
        return _parsers["pptx"]
    elif "spreadsheetml.sheet" in mime_type:
        return _parsers["xlsx"]
    elif "csv" in mime_type:
        return _parsers["csv"]
    elif "markdown" in mime_type:
        return _parsers["markdown"]
    elif mime_type.startswith("text/"):
        return _parsers["txt"]
    elif mime_type.startswith("image/"):
        return _parsers["image"]

    # Default fallback
    logger.warning("Unrecognized file type for '%s' (mime: %s). Falling back to TXT parser.", filename, mime_type)
    return _parsers["txt"]
