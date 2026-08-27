"""Tests for the flashcard models."""

import json

import pytest
from pydantic import ValidationError

from flashcard_generator.card import (
    build_cards_json_schema,
    parse_cards_json,
)


def test_build_cards_json_schema() -> None:
    """Test that the cards JSON schema has the expected elements."""
    schema = build_cards_json_schema()

    assert schema["type"] == "object"
    assert "cards" in schema["properties"]
    assert "cards" in schema["required"]


def test_parse_cards_json() -> None:
    """Test parsing valid generated card JSON."""
    generated_cards_json = json.dumps({"cards": [{"front": "Hello", "back": "There"}]})

    generated_cards = parse_cards_json(generated_cards_json)

    assert len(generated_cards.cards) == 1
    assert generated_cards.cards[0].front == "Hello"
    assert generated_cards.cards[0].back == "There"


@pytest.mark.parametrize(
    "card",
    [
        {"front": "Hello", "back": "     "},
        {"front": "     ", "back": "There"},
    ],
)
def test_reject_cards_with_blank_side(card: dict[str, str]) -> None:
    """Test that generated JSON cards with blank fields are rejected."""
    generated_cards_json = json.dumps({"cards": [card]})

    with pytest.raises(ValidationError):
        parse_cards_json(generated_cards_json)
