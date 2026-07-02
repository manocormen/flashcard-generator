"""Test local card sharing."""

from flashcard_generator.card import BasicCard, GeneratedCards
from flashcard_generator.share import CardShare


def test_card_share() -> None:
    """Test the card share methods."""
    card_share = CardShare()
    cards = GeneratedCards(cards=[BasicCard(front="front", back="back")])

    assert card_share.get() is None

    card_share.start(cards)

    assert card_share.get() == cards

    card_share.stop()

    assert card_share.get() is None
