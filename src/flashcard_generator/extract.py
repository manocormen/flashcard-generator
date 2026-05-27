"""Extract text from uploaded files."""

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

SUPPORTED_EXTENSIONS = {".txt", ".md", ".markdown"}


class RejectionReason(StrEnum):
    """Reason for path rejection."""

    UNSUPPORTED_EXTENSION = "unsupported_extension"
    NOT_UTF8_ENCODED = "not_utf8_encoded"


@dataclass(kw_only=True)
class Doc:
    """Extracted text document."""

    path: Path
    text: str


@dataclass(kw_only=True)
class RejectedPath:
    """Path that couldn't be extracted."""

    path: Path
    reason: RejectionReason


@dataclass(kw_only=True)
class ExtractionResult:
    """Documents successfully extracted and paths rejected."""

    docs: list[Doc]
    rejected_paths: list[RejectedPath]


def extract_docs(paths: Iterable[Path]) -> ExtractionResult:
    """Extract documents from paths."""
    docs, rejected_paths = [], []

    for path in paths:
        if not _is_extension_supported(path):
            rp = RejectedPath(path=path, reason=RejectionReason.UNSUPPORTED_EXTENSION)
            rejected_paths.append(rp)
            continue

        try:
            docs.append(_extract_doc(path))
        except UnicodeDecodeError:
            rp = RejectedPath(path=path, reason=RejectionReason.NOT_UTF8_ENCODED)
            rejected_paths.append(rp)

    return ExtractionResult(docs=docs, rejected_paths=rejected_paths)


def _extract_doc(path: Path) -> Doc:
    """Extract document from a supported path."""
    text = path.read_text(encoding="utf-8")
    return Doc(path=path, text=text)


def _is_extension_supported(path: Path) -> bool:
    """Return whether the path has a supported extension."""
    return path.suffix.lower() in SUPPORTED_EXTENSIONS
