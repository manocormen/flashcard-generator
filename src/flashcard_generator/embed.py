"""Embed document chunks for retrieval."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flashcard_generator.chunk import Chunk
    from flashcard_generator.extract import Doc


@dataclass(kw_only=True)
class EmbeddedChunk:
    """Chunk and its embedding vector."""

    chunk: Chunk
    vector: list[float]


@dataclass(kw_only=True)
class EmbeddedDoc:
    """Document and its embedded chunks."""

    doc: Doc
    chunks: list[EmbeddedChunk]


@dataclass(kw_only=True)
class EmbeddingResult:
    """Embedded topic and documents."""

    topic_vector: list[float]
    docs: list[EmbeddedDoc]
