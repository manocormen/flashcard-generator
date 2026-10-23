"""Test document chunking."""

from pathlib import Path

from flashcard_generator.chunk import chunk_docs
from flashcard_generator.extract import Doc


def test_chunk_docs_splits() -> None:
    """Test that docs are split and keep their headings."""
    text = "# Flashcards\n\n## Quality\n\n" + "Good flashcards are atomic. " * 100
    doc = Doc(path=Path("example.md"), text=text)

    chunked_docs = chunk_docs([doc])

    chunks = chunked_docs[0].chunks
    assert len(chunks) > 1
    assert chunks[1].headings == {"h1": "Flashcards", "h2": "Quality"}


def test_chunk_docs_images() -> None:
    """Test that chunk images and order are preserved."""
    images_dir = Path("images/doc-000")
    text = (
        "![](images/doc-000/image2.png)\n"
        "![](images/doc-000/image1.png)\n"
        "![](images/doc-000/image2.png)\n"
    )
    doc = Doc(path=Path("example.pdf"), text=text, images_dir=images_dir)

    chunked_docs = chunk_docs([doc])

    assert chunked_docs[0].chunks[0].images == [
        images_dir / "image2.png",
        images_dir / "image1.png",
        images_dir / "image2.png",
    ]
