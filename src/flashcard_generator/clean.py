"""Clean text artefacts from extracted documents."""

import re
from dataclasses import replace
from typing import TYPE_CHECKING

import ftfy

if TYPE_CHECKING:
    from collections.abc import Iterable

    from flashcard_generator.extract import Doc


def clean_docs(docs: Iterable[Doc]) -> list[Doc]:
    """Clean the text of each document."""
    return [_clean_doc(doc) for doc in docs]


def _clean_doc(doc: Doc) -> Doc:
    """Clean image references and Unicode text glitches."""
    text = doc.text

    if doc.images_dir is not None:
        text = re.sub(
            r"!\[\]\([^\n)]*/(doc-\d+/)",
            r"![](images/\1",  # Removes random prefix, for deterministic prompt
            text,
        )

    return replace(doc, text=ftfy.fix_text(text))
