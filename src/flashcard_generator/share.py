"""Support local card sharing."""

import socket
from dataclasses import dataclass
from ipaddress import IPv4Address
from typing import TYPE_CHECKING

import psutil  # type: ignore[import-untyped]
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
    """Return this machine's LAN address heuristically."""
    preferred = _get_route_source_ip()
    if preferred is not None:
        return preferred

    candidates = _get_lan_candidates()
    if not candidates:
        message = "No usable LAN address found."
        raise RuntimeError(message)

    return candidates[0]


def _get_lan_candidates() -> list[str]:
    """Find candidate LAN IPv4 addresses."""
    interfaces = psutil.net_if_addrs()
    interface_stats = psutil.net_if_stats()

    candidates: list[str] = []
    for name, addresses in interfaces.items():
        status = interface_stats.get(name)
        if status is not None and not status.isup:  # Filter explicit "down" only
            continue

        for address in addresses:
            if address.family != socket.AF_INET:  # Only IPv4
                continue
            ip = IPv4Address(address.address)
            if (
                ip.is_loopback
                or ip.is_unspecified
                or ip.is_multicast  # Device group
                or ip.is_reserved
            ):
                continue
            candidates.append(str(ip))

    return candidates


def _get_route_source_ip() -> str | None:
    """Return the local IPv4 address the OS would use to reach 8.8.8.8."""
    # Trick for cross-OS reliability: https://stackoverflow.com/a/166589
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            host: str = sock.getsockname()[0]
            return host
    except OSError:
        return None


def make_qr(url: str) -> QRCode:
    """Return a QR code that encodes the input URL."""
    qr_code: QRCode = qrcode.make(url).get_image()

    return qr_code
