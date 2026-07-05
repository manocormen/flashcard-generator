"""Track the currently shared cards."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flashcard_generator.card import GeneratedCards


@dataclass
class CardShare:
    """Currently shared cards."""

    _cards: GeneratedCards | None = None

    def start(self, cards: GeneratedCards) -> None:
        """Start sharing the cards."""
        self._cards = cards

    def stop(self) -> None:
        """Stop sharing the cards."""
        self._cards = None

    def get(self) -> GeneratedCards | None:
        """Get the shared cards."""
        return self._cards
