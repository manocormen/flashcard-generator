"""Embed document chunks for retrieval."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from sentence_transformers import SentenceTransformer
    from sentence_transformers.base.modality_types import MultimodalInput

    from flashcard_generator.chunk import Chunk, ChunkedDoc
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


def embed_docs(docs: Iterable[ChunkedDoc], topic: str) -> EmbeddingResult:
    """Embed documents and topic."""
    model = _load_model()

    return EmbeddingResult(
        topic_vector=_embed_topic(topic, model),
        docs=[_embed_doc(doc, model) for doc in docs],
    )


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


def _embed_doc(doc: ChunkedDoc, model: SentenceTransformer) -> EmbeddedDoc:
    """Embed each chunk of a document."""
    chunks = [_embed_chunk(chunk, model) for chunk in doc.chunks]

    return EmbeddedDoc(doc=doc.doc, chunks=chunks)


def _embed_chunk(chunk: Chunk, model: SentenceTransformer) -> EmbeddedChunk:
    """Encode the chunk text and images into a document embedding."""
    input_chunk = _prepare_input(chunk)

    vector = model.encode_document(input_chunk, normalize_embeddings=True)

    return EmbeddedChunk(chunk=chunk, vector=[float(value) for value in vector])


def _prepare_input(chunk: Chunk) -> MultimodalInput:
    """Prepare chunk text and images for embedding."""
    text = chunk.text

    breadcrumb = " > ".join(chunk.headings.values())
    if breadcrumb:
        text = f"{breadcrumb}\n\n{text}"

    for path in chunk.images:
        image_reference = f"![](images/{path.parent.name}/{path.name})"
        text = text.replace(image_reference, "<|image|>")

    return {"text": text, "image": [str(path) for path in chunk.images]}
