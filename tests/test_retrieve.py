"""Test document retrieval."""

from pathlib import Path

import pytest

from flashcard_generator.chunk import Chunk, ChunkedDoc
from flashcard_generator.embed import EmbeddedChunk, EmbeddedDoc, EmbeddingResult
from flashcard_generator.extract import Doc
from flashcard_generator.retrieve import NoMatchesError, retrieve_docs


def test_retrieve_docs_matches() -> None:
    """Test that retrieval keeps chunks above the similarity threshold."""
    chunk1 = Chunk(text="Good flashcards are atomic.", headings={}, index=0)
    chunk2 = Chunk(text="Rocks help study the past.", headings={}, index=1)
    doc = Doc(path=Path("example.md"), text=f"{chunk1.text}\n\n{chunk2.text}")
    embedded_doc = EmbeddedDoc(
        doc=doc,
        chunks=[
            EmbeddedChunk(chunk=chunk1, vector=[0.2, 0.0]),
            EmbeddedChunk(chunk=chunk2, vector=[0.0, 1.0]),  # Orthogonal to topic
        ],
    )
    result = EmbeddingResult(topic_vector=[1.0, 0.0], docs=[embedded_doc])

    retrieved_docs = retrieve_docs(result, threshold=0.5)

    assert retrieved_docs == [ChunkedDoc(doc=doc, chunks=[chunk1])]


def test_retrieve_docs_no_matches() -> None:
    """Test that retrieval raises error when no chunks match."""
    chunk = Chunk(text="Good flashcards are atomic.", headings={}, index=0)
    doc = Doc(path=Path("example.md"), text=chunk.text)
    embedded_doc = EmbeddedDoc(
        doc=doc,
        chunks=[EmbeddedChunk(chunk=chunk, vector=[0.0, 1.0])],
    )
    result = EmbeddingResult(topic_vector=[1.0, 0.0], docs=[embedded_doc])

    with pytest.raises(NoMatchesError, match="No relevant passages found"):
        retrieve_docs(result, threshold=0.5)
