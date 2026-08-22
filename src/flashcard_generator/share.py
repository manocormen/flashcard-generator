"""Support local card sharing."""

import socket
from dataclasses import dataclass
from typing import TYPE_CHECKING

import qrcode  # type: ignore[import-untyped]
from PIL import Image

if TYPE_CHECKING:
    from flashcard_generator.card import GeneratedCards

type QRCode = Image.Image


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


def get_lan_ip() -> str:
    """Return this machine's LAN IP."""
    try:
        # Trick for cross-OS reliability: https://stackoverflow.com/a/166589
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            host: str = sock.getsockname()[0]
            return host
    except OSError:
        return "127.0.0.1"


def make_qr(url: str) -> QRCode:
    """Return a QR code that encodes the input URL."""
    qr_code: QRCode = qrcode.make(url).get_image()

    return qr_code
