"""Tests for document cleaning."""

from pathlib import Path

from flashcard_generator.clean import clean_docs
from flashcard_generator.extract import Doc

# French pangram with lots of non-ASCII characters to verify cleaning preserves them.
PANGRAM = (
    "Dès Noël, où un zéphyr haï me vêt de glaçons würmiens, je "
    "dîne d'exquis rôtis de bœuf au kir, à l'aÿ d'âge mûr, &cætera."
)


def test_clean_docs_fixes_text_glitch() -> None:
    """Test that cleaning fixes a realistic extracted-text glitch."""
    # I verified that a correct-looking PDF may extract "café" as the mojibake below.
    # This shows that upload/extract isn't enough: a separate cleaning step is needed.
    broken_text = "I like using AnkiDroid at the cafÃ©!"
    fixed_text = "I like using AnkiDroid at the café!"
    path = Path("example.pdf")

    cleaned_docs = clean_docs([Doc(path=path, text=broken_text)])

    assert cleaned_docs == [Doc(path=path, text=fixed_text)]


def test_clean_docs_preserves_non_ascii_text() -> None:
    """Test that cleaning preserves already-correct non-ASCII characters."""
    path = Path("example.md")

    cleaned_docs = clean_docs([Doc(path=path, text=PANGRAM)])

    assert cleaned_docs == [Doc(path=path, text=PANGRAM)]
