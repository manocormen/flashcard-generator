"""Clean text artefacts from extracted documents."""

from typing import TYPE_CHECKING

import ftfy

from flashcard_generator.extract import Doc

if TYPE_CHECKING:
    from collections.abc import Iterable


def clean_docs(docs: Iterable[Doc]) -> list[Doc]:
    """Clean the text of each document."""
    return [Doc(path=d.path, text=_clean_text(d.text)) for d in docs]


def _clean_text(text: str) -> str:
    """Fix common Unicode text glitches."""
    return ftfy.fix_text(text)
