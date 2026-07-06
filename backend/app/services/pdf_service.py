"""
PDF text extraction using PyMuPDF (fitz).

Extracts text page-by-page and tracks character offsets so that downstream
chunking can map each chunk back to its originating page number.
"""

from dataclasses import dataclass, field

import fitz  # PyMuPDF

from app.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ExtractedPage:
    """Text content and position metadata for a single PDF page."""

    page_number: int        # 1-indexed
    text: str
    char_start: int         # offset of this page's text in the full document string
    char_end: int           # exclusive end offset


@dataclass
class ExtractionResult:
    """Result returned by extract_pdf."""

    pages: list[ExtractedPage] = field(default_factory=list)
    full_text: str = ""
    page_count: int = 0
    char_count: int = 0

    def page_for_offset(self, char_offset: int) -> int:
        """Return the 1-indexed page number that contains the given character offset."""
        for page in self.pages:
            if page.char_start <= char_offset < page.char_end:
                return page.page_number
        # Fallback: return last page
        return self.pages[-1].page_number if self.pages else 1


def extract_pdf(content: bytes, filename: str = "<bytes>") -> ExtractionResult:
    """
    Extract all text from a PDF given its raw bytes.

    Strategy:
      - Open document from memory (no temp files)
      - Extract text with 'text' mode (preserves layout)
      - Concatenate pages with a double-newline separator
      - Track per-page char offsets for source attribution

    Args:
        content: Raw PDF bytes.
        filename: Used only for logging.

    Returns:
        ExtractionResult with per-page text and a stitched full_text string.

    Raises:
        ValueError: If the document has no extractable text.
    """
    try:
        doc: fitz.Document = fitz.open(stream=content, filetype="pdf")
    except Exception as exc:
        raise ValueError(f"Cannot open PDF '{filename}': {exc}") from exc

    pages: list[ExtractedPage] = []
    parts: list[str] = []
    cursor = 0

    for page_index in range(len(doc)):
        page: fitz.Page = doc[page_index]
        page_text: str = page.get_text("markdown")  # type: ignore[arg-type]

        # Normalise whitespace but preserve paragraph structure
        page_text = page_text.strip()

        if not page_text:
            logger.debug("Page %d of '%s' has no extractable text — skipping", page_index + 1, filename)
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

        # Account for the "\n\n" separator we'll join with
        cursor = end + 2

    # Capture page_count BEFORE closing the document.
    # Accessing len(doc) after doc.close() raises "document closed".
    total_pages: int = len(doc)
    doc.close()

    if not pages:
        raise ValueError(
            f"PDF '{filename}' contains no extractable text. "
            "It may be a scanned document without OCR."
        )

    full_text = "\n\n".join(p.text for p in pages)

    result = ExtractionResult(
        pages=pages,
        full_text=full_text,
        page_count=total_pages,
        char_count=len(full_text),
    )

    logger.info(
        "Extracted PDF '%s': %d pages, %d chars, %d text-pages",
        filename,
        result.page_count,
        result.char_count,
        len(pages),
    )
    return result
