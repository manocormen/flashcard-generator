"""Retrieve relevant embedded passages."""

import logging
from math import hypot, sumprod
from typing import TYPE_CHECKING

from flashcard_generator.chunk import ChunkedDoc

if TYPE_CHECKING:
    from flashcard_generator.embed import EmbeddedDoc, EmbeddingResult

# Found through informal trial and error using evals' PDFs
# TODO: Add a dedicated eval and optimize through grid search
MIN_SIMILARITY = 0.70

LOGGER = logging.getLogger(__name__)


class NoMatchesError(ValueError):
    """No passages matched the topic."""


def retrieve_docs(
    result: EmbeddingResult,
    threshold: float = MIN_SIMILARITY,
) -> list[ChunkedDoc]:
    """Return documents with relevant chunks only."""
    thresholded = [
        _retrieve_doc(embedded_doc, result.topic_vector, threshold)
        for embedded_doc in result.docs
    ]

    relevant = [chunked_doc for chunked_doc in thresholded if chunked_doc.chunks]

    if not relevant:
        message = "No relevant passages found. Try a broader topic or other documents."
        raise NoMatchesError(message)

    return relevant


def _retrieve_doc(
    doc: EmbeddedDoc,
    topic_vector: list[float],
    threshold: float,
) -> ChunkedDoc:
    """Return document with relevant chunks only."""
    selected_chunks = []

    for embedded_chunk in doc.chunks:
        score = _cosine_similarity(topic_vector, embedded_chunk.vector)

        LOGGER.debug(
            "Document %s, chunk %s: cosine similarity %s.",
            doc.doc.path.name,
            embedded_chunk.chunk.index,
            score,
        )

        if score >= threshold:
            selected_chunks.append(embedded_chunk.chunk)

    return ChunkedDoc(doc=doc.doc, chunks=selected_chunks)


def _cosine_similarity(vector1: list[float], vector2: list[float]) -> float:
    """Compute the cosine similarity between the two vectors."""
    return sumprod(vector1, vector2) / (hypot(*vector1) * hypot(*vector2))
