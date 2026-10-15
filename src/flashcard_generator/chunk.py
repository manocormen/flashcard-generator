"""Chunk documents for embedding."""

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

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
    images: list[Path] = field(default_factory=list)


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
        Chunk(
            text=fragment.page_content,
            headings=fragment.metadata,
            index=index,
            images=_gather_images(fragment.page_content, doc.images_dir),
        )
        for index, fragment in enumerate(fragments)
    ]

    return ChunkedDoc(doc=doc, chunks=chunks)


def _gather_images(text: str, images_dir: Path | None) -> list[Path]:
    """Return paths of images referenced in text."""
    if images_dir is None:
        return []

    pattern = rf"!\[\]\(images/{images_dir.name}/([^\n)]+)\)"
    image_paths = re.findall(pattern, text)

    return [images_dir / image_path for image_path in image_paths]
