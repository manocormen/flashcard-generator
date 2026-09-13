"""Test local card sharing."""

from socket import AF_INET
from types import SimpleNamespace
from typing import TYPE_CHECKING

from flashcard_generator.card import BasicCard, GeneratedCards
from flashcard_generator.share import CardShare, get_lan_ip

if TYPE_CHECKING:
    import pytest


def test_card_share() -> None:
    """Test the card share methods."""
    card_share = CardShare()
    cards = GeneratedCards(cards=[BasicCard(front="front", back="back")])

    assert card_share.get() is None

    card_share.start(cards)

    assert card_share.get() == cards

    card_share.stop()

    assert card_share.get() is None


def test_get_lan_ip_without_route(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a LAN address is found even when the route trick fails."""
    lan_ip = "192.168.0.10"

    def fake_addrs() -> dict[str, list[SimpleNamespace]]:
        return {
            "lo": [SimpleNamespace(family=AF_INET, address="127.0.0.1")],
            "eth0": [SimpleNamespace(family=AF_INET, address=lan_ip)],
        }

    def fake_stats() -> dict[str, SimpleNamespace]:
        return {
            "lo": SimpleNamespace(isup=True),
            "eth0": SimpleNamespace(isup=True),
        }

    def raise_socket_error(_family: int, _type: int) -> None:
        message = "No outgoing route."
        raise OSError(message)

    monkeypatch.setattr("flashcard_generator.share.psutil.net_if_addrs", fake_addrs)
    monkeypatch.setattr("flashcard_generator.share.psutil.net_if_stats", fake_stats)
    monkeypatch.setattr("flashcard_generator.share.socket.socket", raise_socket_error)

    assert get_lan_ip() == lan_ip
