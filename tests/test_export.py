"""Test exporting generated cards."""

import csv
import json
from typing import TYPE_CHECKING

import pytest

from flashcard_generator.card import BasicCard, GeneratedCards
from flashcard_generator.export import CSV_FILENAME, JSON_FILENAME, export_cards

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def generated_cards() -> GeneratedCards:
    """Return a generated cards instance with two cards."""
    return GeneratedCards(
        cards=[
            BasicCard(front="front1", back="back1"),
            BasicCard(front="front2", back="back2"),
        ],
    )


def test_export_cards_paths(generated_cards: GeneratedCards, tmp_path: Path) -> None:
    """Test that exported cards' paths are as expected."""
    exported_cards = export_cards(generated_cards, tmp_path)

    assert exported_cards.json_path == tmp_path / JSON_FILENAME
    assert exported_cards.csv_path == tmp_path / CSV_FILENAME


def test_export_cards_json_content(
    generated_cards: GeneratedCards,
    tmp_path: Path,
) -> None:
    """Test that exported cards' JSON content is as expected."""
    exported_cards = export_cards(generated_cards, tmp_path)

    json_cards = json.loads(exported_cards.json_path.read_text(encoding="utf-8"))

    assert json_cards == generated_cards.model_dump()


def test_export_cards_csv_content(
    generated_cards: GeneratedCards,
    tmp_path: Path,
) -> None:
    """Test that exported cards' CSV content is as expected."""
    exported_cards = export_cards(generated_cards, tmp_path)

    with exported_cards.csv_path.open(encoding="utf-8", newline="") as f:
        csv_cards = list(csv.reader(f))

    assert csv_cards == [
        ["front", "back"],
        ["front1", "back1"],
        ["front2", "back2"],
    ]


def test_export_cards_csv_special_chars(tmp_path: Path) -> None:
    """Test that special characters are correctly exported as CSV."""
    generated_cards = GeneratedCards(
        cards=[
            BasicCard(front="hello, there", back="hello, there"),
            BasicCard(front='hello "there"', back='hello "there"'),
            BasicCard(front="hello\nthere", back="hello\nthere"),
        ],
    )

    exported_cards = export_cards(generated_cards, tmp_path)

    with exported_cards.csv_path.open(encoding="utf-8", newline="") as f:
        csv_cards = list(csv.reader(f))

    assert csv_cards == [
        ["front", "back"],
        ["hello, there", "hello, there"],
        ['hello "there"', 'hello "there"'],
        ["hello\nthere", "hello\nthere"],
    ]


def test_export_empty_cards_list(tmp_path: Path) -> None:
    """Test that no cards still produces valid export files."""
    generated_cards = GeneratedCards(cards=[])

    exported_cards = export_cards(generated_cards, tmp_path)

    json_cards = json.loads(exported_cards.json_path.read_text(encoding="utf-8"))

    with exported_cards.csv_path.open(encoding="utf-8", newline="") as f:
        csv_cards = list(csv.reader(f))

    assert json_cards["cards"] == []
    assert csv_cards == [["front", "back"]]
