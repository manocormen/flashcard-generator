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
        revision="914f7f89142e33e77833254d9c9b90c3cef7303b",
        config_kwargs={"audio_config": None},  # Load only text and image capabilities
    )


def _embed_topic(topic: str, model: SentenceTransformer) -> list[float]:
    """Encode the topic into a query embedding."""
    vector = model.encode_query(topic, normalize_embeddings=True)

    return [float(value) for value in vector]


def _embed_doc(doc: ChunkedDoc, model: SentenceTransformer) -> EmbeddedDoc:
    """Embed document's chunks."""
    prepared_chunks = [_prepare_input(chunk, doc.doc.path.name) for chunk in doc.chunks]
    vectors = model.encode_document(prepared_chunks, normalize_embeddings=True)

    embedded_chunks = [
        EmbeddedChunk(chunk=chunk, vector=[float(value) for value in vector])
        for chunk, vector in zip(doc.chunks, vectors, strict=True)
    ]

    return EmbeddedDoc(doc=doc.doc, chunks=embedded_chunks)


def _prepare_input(chunk: Chunk, filename: str) -> MultimodalInput:
    """Prepare chunk text and images for embedding."""
    text = chunk.text

    context = " > ".join(chunk.headings.values()) or filename
    text = f"{context}\n\n{text}"

    for path in chunk.images:
        image_reference = f"![](images/{path.parent.name}/{path.name})"
        text = text.replace(image_reference, "<|image|>")

    return {"text": text, "image": [str(path) for path in chunk.images]}
