"""Extract text and images from uploaded files."""

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

import pymupdf4llm  # type: ignore[import-untyped]

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

SUPPORTED_TEXT_EXTENSIONS = {".txt", ".md", ".markdown"}
PDF_EXTENSION = ".pdf"


class RejectionReason(StrEnum):
    """Reason for path rejection."""

    UNSUPPORTED_EXTENSION = "unsupported_extension"
    NOT_UTF8_ENCODED = "not_utf8_encoded"
    READ_FAILED = "read_failed"


@dataclass(kw_only=True)
class Doc:
    """Extracted document."""

    path: Path
    text: str
    images_dir: Path | None = None


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


def extract_docs(paths: Iterable[Path], images_root: Path) -> ExtractionResult:
    """Extract documents from paths, placing images under given root."""
    docs, rejected_paths = [], []

    for index, path in enumerate(paths):
        images_dir = images_root / f"doc-{index:03d}"
        outcome = _extract_doc(path, images_dir)
        if isinstance(outcome, Doc):
            docs.append(outcome)
        else:
            rejected_paths.append(outcome)

    return ExtractionResult(docs=docs, rejected_paths=rejected_paths)


def _extract_doc(path: Path, images_dir: Path) -> Doc | RejectedPath:
    """Extract document from path."""
    extension = path.suffix.lower()

    if extension in SUPPORTED_TEXT_EXTENSIONS:
        return _extract_doc_from_text(path)
    if extension == PDF_EXTENSION:
        return _extract_doc_from_pdf(path, images_dir)

    return RejectedPath(path=path, reason=RejectionReason.UNSUPPORTED_EXTENSION)


def _extract_doc_from_text(path: Path) -> Doc | RejectedPath:
    """Extract document from UTF-8 text file."""
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return RejectedPath(path=path, reason=RejectionReason.NOT_UTF8_ENCODED)
    except OSError:
        return RejectedPath(path=path, reason=RejectionReason.READ_FAILED)

    return Doc(path=path, text=text)


def _extract_doc_from_pdf(path: Path, images_dir: Path) -> Doc | RejectedPath:
    """Extract document from PDF file."""
    try:
        images_dir.mkdir()
        text = pymupdf4llm.to_markdown(
            str(path),
            use_ocr=False,
            write_images=True,
            image_path=str(images_dir),
        )
    except OSError, RuntimeError:
        return RejectedPath(path=path, reason=RejectionReason.READ_FAILED)

    return Doc(path=path, text=text, images_dir=images_dir)
