"""Extract text from uploaded files."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

SUPPORTED_EXTENSIONS = {".txt", ".md", ".markdown"}


@dataclass(kw_only=True)
class Doc:
    """Extracted text document."""

    path: Path
    text: str


@dataclass(kw_only=True)
class ExtractionResult:
    """Result of extracting documents from paths."""

    docs: list[Doc]
    unsupported_paths: list[Path]


def extract_docs(paths: Iterable[Path]) -> ExtractionResult:
    """Extract documents from files."""
    docs, unsupported_paths = [], []

    for path in paths:
        if _is_supported(path):
            docs.append(_extract_doc(path))
        else:
            unsupported_paths.append(path)

    return ExtractionResult(docs=docs, unsupported_paths=unsupported_paths)


def _extract_doc(path: Path) -> Doc:
    """Extract document from a supported file."""
    text = path.read_text(encoding="utf-8")
    return Doc(path=path, text=text)


def _is_supported(path: Path) -> bool:
    """Return whether the path has a supported extension."""
    return path.suffix.lower() in SUPPORTED_EXTENSIONS
