"""Test document embedding."""

from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING

from flashcard_generator import embed as embed_module
from flashcard_generator.chunk import Chunk, ChunkedDoc
from flashcard_generator.extract import Doc

if TYPE_CHECKING:
    import pytest


def test_embed_docs(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test embedding inputs and returned vectors."""
    image = Path("images/doc-000/image.png")
    text = "Good flashcards are atomic.\n\n![](images/doc-000/image.png)"
    doc = Doc(path=Path("example.pdf"), text=text, images_dir=image.parent)
    chunk = Chunk(text=text, headings={"h1": "Flashcards"}, index=0, images=[image])
    args = []

    def fake_encode_query(text: object, **kwargs: object) -> list[float]:
        args.append(("query", text, kwargs))
        return [1.0, 0.0, 0.0]

    def fake_encode_document(chunk: object, **kwargs: object) -> list[float]:
        args.append(("document", chunk, kwargs))
        return [0.0, 1.0, 0.0]

    def fake_load_model() -> SimpleNamespace:
        return SimpleNamespace(
            encode_query=fake_encode_query,
            encode_document=fake_encode_document,
        )

    monkeypatch.setattr(embed_module, "_load_model", fake_load_model)

    result = embed_module.embed_docs([ChunkedDoc(doc=doc, chunks=[chunk])], "Quality")

    assert args == [
        ("query", "Quality", {"normalize_embeddings": True}),
        (
            "document",
            {
                "text": "Flashcards\n\nGood flashcards are atomic.\n\n<|image|>",
                "image": [str(image)],
            },
            {"normalize_embeddings": True},
        ),
    ]
    assert result.topic_vector == [1.0, 0.0, 0.0]
    assert result.docs[0].chunks[0].vector == [0.0, 1.0, 0.0]
