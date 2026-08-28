"""Clean text artefacts from extracted documents."""

from dataclasses import replace
from typing import TYPE_CHECKING

import ftfy

if TYPE_CHECKING:
    from collections.abc import Iterable

    from flashcard_generator.extract import Doc


def clean_docs(docs: Iterable[Doc]) -> list[Doc]:
    """Clean the text of each document."""
    return [replace(doc, text=_clean_text(doc.text)) for doc in docs]


def _clean_text(text: str) -> str:
    """Fix common Unicode text glitches."""
    return ftfy.fix_text(text)
