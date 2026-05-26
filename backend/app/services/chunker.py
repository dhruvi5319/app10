"""Token-based text chunker using LangChain RecursiveCharacterTextSplitter + tiktoken."""

import logging
from dataclasses import dataclass

import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.services.parser import ParsedDocument

logger = logging.getLogger(__name__)

_ENCODING_NAME = "cl100k_base"


@dataclass
class ChunkResult:
    chunk_index: int
    text: str
    page_number: int | None
    token_count: int


def _tiktoken_len(text: str, encoding_name: str = _ENCODING_NAME) -> int:
    """Return the token count for *text* using the specified tiktoken encoding."""
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))


def _count_tokens(text: str, encoding: tiktoken.Encoding) -> int:
    return len(encoding.encode(text))


def _make_splitter(chunk_size: int, chunk_overlap: int) -> RecursiveCharacterTextSplitter:
    """Build a RecursiveCharacterTextSplitter that measures length in tokens."""
    enc = tiktoken.get_encoding(_ENCODING_NAME)

    def token_len(text: str) -> int:
        return len(enc.encode(text))

    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=token_len,
        separators=["\n\n", "\n", " ", ""],
    )


def chunk_document(
    parsed: ParsedDocument,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[ChunkResult]:
    """
    Chunk a ParsedDocument into token-bounded ChunkResult objects.

    For PDFs: each page is chunked separately, page_number is preserved.
    For TXT/DOCX: full text is chunked, page_number=None for all chunks.
    """
    # Safety: clamp overlap
    if chunk_overlap >= chunk_size:
        logger.warning(
            f"chunk_overlap ({chunk_overlap}) >= chunk_size ({chunk_size}); "
            f"clamping overlap to chunk_size // 4"
        )
        chunk_overlap = chunk_size // 4

    enc = tiktoken.get_encoding(_ENCODING_NAME)
    splitter = _make_splitter(chunk_size, chunk_overlap)
    results: list[ChunkResult] = []
    global_index = 0

    if parsed.page_chunks:
        # PDF: chunk per page, preserve page_number
        for page_number, page_text in parsed.page_chunks:
            if not page_text.strip():
                continue
            splits = splitter.split_text(page_text)
            for split in splits:
                if not split.strip():
                    continue
                token_count = _count_tokens(split, enc)
                if token_count == 0:
                    continue
                results.append(
                    ChunkResult(
                        chunk_index=global_index,
                        text=split,
                        page_number=page_number,
                        token_count=token_count,
                    )
                )
                global_index += 1
    else:
        # TXT/DOCX: chunk full text
        if not parsed.text.strip():
            return []
        splits = splitter.split_text(parsed.text)
        for split in splits:
            if not split.strip():
                continue
            token_count = _count_tokens(split, enc)
            if token_count == 0:
                continue
            results.append(
                ChunkResult(
                    chunk_index=global_index,
                    text=split,
                    page_number=None,
                    token_count=token_count,
                )
            )
            global_index += 1

    logger.debug(f"Chunked into {len(results)} chunks (chunk_size={chunk_size})")
    return results
