"""
Adaptive Semantic Chunker using Markdown Structure.

This chunker detects Markdown headers (e.g., `# Heading`, `## Subheading`) 
to establish semantic boundaries and hierarchy.

Algorithm:
  1. Scan text sequentially to identify semantic blocks bounded by headers.
  2. Track the most recent H1/H2 (section/heading) context.
  3. Greedily group blocks until adding another would exceed MAX_CHUNK_SIZE,
     or stop if a new major semantic boundary is hit.
  4. If a single block is larger than MAX_CHUNK_SIZE, fall back to recursive
     character splitting.
"""

import re
from dataclasses import dataclass, field

from app.utils.logging import get_logger

logger = get_logger(__name__)

# Fallback separators for large unformatted blocks
_FALLBACK_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

@dataclass
class TextChunk:
    """A single chunk produced by the splitter."""

    text: str
    chunk_index: int          # 0-based position in the chunk list
    char_start: int           # approximate start offset in the source text
    char_end: int             # approximate end offset
    page_number: int = 1      # page attribution (populated by caller)
    heading: str | None = None # The closest preceding header
    section: str | None = None # The closest preceding top-level header

# ── Fallback recursive chunker ────────────────────────────────────────────────

def _merge_splits(
    splits: list[str],
    separator: str,
    chunk_size: int,
    chunk_overlap: int,
) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    sep_len = len(separator)

    for split in splits:
        split_len = len(split)
        added_len = split_len + (sep_len if current else 0)

        if current_len + added_len > chunk_size and current:
            chunk_text = separator.join(current).strip()
            if chunk_text:
                chunks.append(chunk_text)
            while current and current_len > chunk_overlap:
                removed = current.pop(0)
                current_len -= len(removed) + sep_len
            if not current:
                current_len = 0

        current.append(split)
        current_len += split_len + (sep_len if len(current) > 1 else 0)

    if current:
        chunk_text = separator.join(current).strip()
        if chunk_text:
            chunks.append(chunk_text)

    return chunks


def _split_recursive(
    text: str,
    separators: list[str],
    chunk_size: int,
    chunk_overlap: int,
) -> list[str]:
    if not text.strip():
        return []
    if len(text) <= chunk_size:
        return [text.strip()]

    separator = separators[0]
    remaining_separators = separators[1:]

    if separator:
        raw_splits = text.split(separator)
    else:
        return [
            text[i : i + chunk_size]
            for i in range(0, len(text), chunk_size - chunk_overlap)
            if text[i : i + chunk_size].strip()
        ]

    good_splits: list[str] = []
    for fragment in raw_splits:
        if not fragment.strip():
            continue
        if len(fragment) > chunk_size and remaining_separators:
            good_splits.extend(
                _split_recursive(fragment, remaining_separators, chunk_size, chunk_overlap)
            )
        else:
            good_splits.append(fragment)

    return _merge_splits(good_splits, separator, chunk_size, chunk_overlap)


# ── Semantic structure chunker ────────────────────────────────────────────────

def _extract_header(line: str) -> tuple[int, str] | None:
    """Detect if a line is a markdown header, return (level, text)."""
    match = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
    if match:
        return len(match.group(1)), match.group(2).strip()
    return None


@dataclass
class SemanticBlock:
    text: str
    section: str | None
    heading: str | None


def _parse_semantic_blocks(text: str) -> list[SemanticBlock]:
    """Parse text into blocks grouped by their current heading context."""
    lines = text.split('\n')
    blocks: list[SemanticBlock] = []
    
    current_section = None
    current_heading = None
    current_lines = []

    def flush_block():
        if current_lines:
            block_text = "\n".join(current_lines).strip()
            if block_text:
                blocks.append(SemanticBlock(
                    text=block_text,
                    section=current_section,
                    heading=current_heading,
                ))
            current_lines.clear()

    for line in lines:
        header_info = _extract_header(line)
        if header_info:
            level, header_text = header_info
            
            # Flush existing block before starting a new context
            flush_block()
            
            if level == 1:
                current_section = header_text
                current_heading = header_text
            else:
                current_heading = header_text
            
            current_lines.append(line)
        else:
            current_lines.append(line)

    flush_block()
    return blocks


def _adaptive_chunk(
    text: str,
    min_chunk_size: int,
    max_chunk_size: int,
    chunk_overlap: int,
) -> list[SemanticBlock]:
    """Merge semantic blocks into chunks adhering to min/max sizes."""
    raw_blocks = _parse_semantic_blocks(text)
    final_chunks: list[SemanticBlock] = []
    
    current_text = ""
    current_section = None
    current_heading = None

    def flush_current():
        nonlocal current_text, current_section, current_heading
        if current_text.strip():
            final_chunks.append(SemanticBlock(
                text=current_text.strip(),
                section=current_section,
                heading=current_heading
            ))
        current_text = ""
        current_section = None
        current_heading = None

    for block in raw_blocks:
        # If this single block is huge, we must fallback split it
        if len(block.text) > max_chunk_size:
            flush_current()
            fallback_splits = _split_recursive(
                block.text, _FALLBACK_SEPARATORS, max_chunk_size, chunk_overlap
            )
            for split in fallback_splits:
                final_chunks.append(SemanticBlock(
                    text=split,
                    section=block.section,
                    heading=block.heading
                ))
            continue

        # If adding this block exceeds max size, flush current first
        if current_text and len(current_text) + len(block.text) + 2 > max_chunk_size:
            flush_current()
        
        # Start a new chunk or append to existing
        if not current_text:
            current_text = block.text
            current_section = block.section
            current_heading = block.heading
        else:
            current_text += "\n\n" + block.text
            # We keep the heading/section of the *start* of the chunk
            # but if it was None, we adopt the new one
            if not current_section: current_section = block.section
            if not current_heading: current_heading = block.heading

        # If current chunk has reached a healthy size, flush it
        if len(current_text) >= min_chunk_size:
            flush_current()

    flush_current()
    return final_chunks


# ── Public API ────────────────────────────────────────────────────────────────

def build_chunks(
    text: str,
    min_chunk_size: int = 500,
    max_chunk_size: int = 2000,
    chunk_overlap: int = 200,
    page_resolver=None,        # callable(char_offset) -> page_number
) -> list[TextChunk]:
    """
    Parse text into adaptive semantic chunks, preserving structural metadata.
    """
    if chunk_overlap >= max_chunk_size:
        raise ValueError("chunk_overlap must be smaller than max_chunk_size.")

    semantic_chunks = _adaptive_chunk(text, min_chunk_size, max_chunk_size, chunk_overlap)
    
    result: list[TextChunk] = []
    search_start = 0

    for idx, schunk in enumerate(semantic_chunks):
        raw = schunk.text
        # Locate chunk inside original text to derive char offsets
        pos = text.find(raw[:50], search_start)
        if pos == -1:
            pos = search_start

        char_start = pos
        char_end = char_start + len(raw)
        search_start = max(0, char_end - chunk_overlap)

        page_number = page_resolver(char_start) if page_resolver else 1

        result.append(TextChunk(
            text=raw,
            chunk_index=idx,
            char_start=char_start,
            char_end=char_end,
            page_number=page_number,
            heading=schunk.heading,
            section=schunk.section,
        ))

    logger.debug(
        "build_chunks → %d chunks (min=%d max=%d overlap=%d)",
        len(result),
        min_chunk_size,
        max_chunk_size,
        chunk_overlap,
    )
    return result
