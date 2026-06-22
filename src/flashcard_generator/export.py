"""Export the generated cards."""

import csv
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from flashcard_generator.card import GeneratedCards

JSON_FILENAME = "cards.json"
CSV_FILENAME = "cards.csv"


@dataclass(kw_only=True)
class ExportedCards:
    """Card files saved to disk."""

    json_path: Path
    csv_path: Path


def export_cards(cards: GeneratedCards, output_dir: Path) -> ExportedCards:
    """Save the generated cards to disk."""
    json_path = output_dir / JSON_FILENAME
    csv_path = output_dir / CSV_FILENAME

    json_path.write_text(cards.model_dump_json(indent=2), encoding="utf-8")

    # Explicit newline recommended here:
    # https://docs.python.org/3/library/csv.html#csv.writer
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["front", "back"])
        for card in cards.cards:
            writer.writerow([card.front, card.back])

    return ExportedCards(json_path=json_path, csv_path=csv_path)
