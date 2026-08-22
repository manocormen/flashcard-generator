"""Flashcard model for structured outputs."""

from typing import TYPE_CHECKING, Annotated

from pydantic import BaseModel, StringConstraints

if TYPE_CHECKING:
    from pydantic.json_schema import JsonSchemaValue

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


def build_cards_json_schema() -> JsonSchemaValue:
    """Build the JSON card schema for enforcing structured outputs."""
    return GeneratedCards.model_json_schema()


def parse_cards_json(raw_json: str) -> GeneratedCards:
    """Validate and parse the generated cards against the card model."""
    return GeneratedCards.model_validate_json(raw_json)
