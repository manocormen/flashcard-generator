"""Embed document chunks for retrieval."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

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


def _load_model() -> SentenceTransformer:
    """Load embedding model."""
    from sentence_transformers import SentenceTransformer  # noqa: PLC0415 - lazy import

    return SentenceTransformer(
        "google/embeddinggemma-2",
        config_kwargs={"audio_config": None},  # Load only text and image capabilities
    )


def _embed_topic(topic: str, model: SentenceTransformer) -> list[float]:
    """Encode the topic into a query embedding."""
    vector = model.encode_query(topic, normalize_embeddings=True)

    return [float(value) for value in vector]
