"""Flashcard model for structured outputs."""

from typing import Annotated

from pydantic import BaseModel, StringConstraints

type NonEmptyStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
]


class BasicCard(BaseModel):
    """Anki Basic note type."""

    front: NonEmptyStr
    back: NonEmptyStr


class GeneratedCards(BaseModel):
    """Collection of generated flashcards."""

    cards: list[BasicCard]
