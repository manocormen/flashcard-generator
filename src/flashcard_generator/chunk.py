"""Chunk documents for embedding."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from flashcard_generator.extract import Doc

_HEADING_SPLITTER = MarkdownHeaderTextSplitter(
    headers_to_split_on=[("#" * level, f"#{level}") for level in range(1, 7)],
    strip_headers=False,
)
_TEXT_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=2000,
    chunk_overlap=0,
)


@dataclass(kw_only=True)
class Chunk:
    """Individual document chunk."""

    text: str
    headings: dict[str, str]
    index: int


@dataclass(kw_only=True)
class ChunkedDoc:
    """Full document and its chunks."""

    doc: Doc
    chunks: list[Chunk]


def chunk_docs(docs: Iterable[Doc]) -> list[ChunkedDoc]:
    """Chunk each document for embedding."""
    return [_chunk_doc(doc) for doc in docs]


def _chunk_doc(doc: Doc) -> ChunkedDoc:
    """Chunk a document by headings and length."""
    sections = _HEADING_SPLITTER.split_text(doc.text)
    fragments = _TEXT_SPLITTER.split_documents(sections)

    chunks = [
        Chunk(text=fragment.page_content, headings=fragment.metadata, index=index)
        for index, fragment in enumerate(fragments)
    ]

    return ChunkedDoc(doc=doc, chunks=chunks)
