"""Tests for document extraction."""

from typing import TYPE_CHECKING

import pymupdf
import pytest

from flashcard_generator.extract import Doc, RejectedPath, RejectionReason, extract_docs

if TYPE_CHECKING:
    from pathlib import Path


# French pangram with lots of non-ASCII characters for testing UTF-8 decoding.
PANGRAM = (
    "Dès Noël, où un zéphyr haï me vêt de glaçons würmiens, je "
    "dîne d'exquis rôtis de bœuf au kir, à l'aÿ d'âge mûr, &cætera."
)


@pytest.mark.parametrize("extension", [".txt", ".md", ".markdown", ".MD"])
def test_extract_docs_from_supported_text_file(tmp_path: Path, extension: str) -> None:
    """Test extracting docs from a single text file with a supported extension."""
    path = tmp_path / f"example{extension}"
    path.write_text(PANGRAM, encoding="utf-8")

    extraction = extract_docs([path])

    assert extraction.docs == [Doc(path=path, text=PANGRAM)]
    assert extraction.rejected_paths == []


@pytest.mark.parametrize("extension", [".pdf", ".PDF"])
def test_extract_docs_from_text_pdf_file(tmp_path: Path, extension: str) -> None:
    """Test extracting a doc from a text-based PDF file."""
    pdf_path = tmp_path / f"example{extension}"
    text = "Only review what you need, when you need it!"

    pdf = pymupdf.open()  # type: ignore[no-untyped-call]
    pdf.new_page().insert_text(point=(64, 64), text=text)
    pdf.save(str(pdf_path))  # type: ignore[no-untyped-call]
    pdf.close()  # type: ignore[no-untyped-call]

    extraction = extract_docs([pdf_path])

    assert extraction.rejected_paths == []
    assert len(extraction.docs) == 1

    doc = extraction.docs[0]
    assert doc.path == pdf_path
    assert text in doc.text


@pytest.mark.parametrize("extension", ["", ".unsupported"])
def test_extract_docs_from_unsupported_file(tmp_path: Path, extension: str) -> None:
    """Test rejecting a file without a supported extension."""
    unsupported_path = tmp_path / f"example{extension}"
    unsupported_path.touch()

    extraction = extract_docs([unsupported_path])

    assert extraction.docs == []
    assert extraction.rejected_paths == [
        RejectedPath(
            path=unsupported_path,
            reason=RejectionReason.UNSUPPORTED_EXTENSION,
        ),
    ]


def test_extract_docs_from_mixed_files(tmp_path: Path) -> None:
    """Test extracting docs from a mix of supported and unsupported file extensions."""
    supported_path1 = tmp_path / "example.txt"
    supported_path2 = tmp_path / "example.md"
    unsupported_path = tmp_path / "example.unsupported"

    text1 = f"{PANGRAM} 1"
    text2 = f"{PANGRAM} 2"

    supported_path1.write_text(text1, encoding="utf-8")
    supported_path2.write_text(text2, encoding="utf-8")
    unsupported_path.touch()

    extraction = extract_docs([supported_path1, unsupported_path, supported_path2])

    assert extraction.docs == [
        Doc(path=supported_path1, text=text1),
        Doc(path=supported_path2, text=text2),
    ]
    assert extraction.rejected_paths == [
        RejectedPath(
            path=unsupported_path,
            reason=RejectionReason.UNSUPPORTED_EXTENSION,
        ),
    ]


def test_extract_docs_from_non_utf8_file(tmp_path: Path) -> None:
    """Test rejecting a supported file that isn't UTF-8 encoded."""
    non_utf8_path = tmp_path / "example.txt"
    non_utf8_path.write_text(PANGRAM, encoding="cp1252")

    extraction = extract_docs([non_utf8_path])

    assert extraction.docs == []
    assert extraction.rejected_paths == [
        RejectedPath(path=non_utf8_path, reason=RejectionReason.NOT_UTF8_ENCODED),
    ]


def test_extract_docs_from_non_existent_file(tmp_path: Path) -> None:
    """Test trying to extract docs from a non-existing file."""
    fileless_path = tmp_path / "example.txt"

    extraction = extract_docs([fileless_path])

    assert extraction.docs == []
    assert extraction.rejected_paths == [
        RejectedPath(path=fileless_path, reason=RejectionReason.READ_FAILED),
    ]
