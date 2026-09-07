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


def _write_pdf(path: Path, text: str, *, with_image: bool = False) -> None:
    """Write a PDF with text and, optionally, an image."""
    with pymupdf.open() as pdf:  # type: ignore[no-untyped-call]
        page = pdf.new_page()
        page.insert_text(point=(64, 64), text=text)

        if with_image:
            pixmap = pymupdf.Pixmap(  # type: ignore[no-untyped-call]
                pymupdf.csRGB,
                (0, 0, 200, 150),
                False,  # noqa: FBT003
            )
            pixmap.clear_with(128)  # type: ignore[no-untyped-call]
            page.insert_image((64, 97, 264, 247), pixmap=pixmap)

        pdf.save(str(path))


@pytest.mark.parametrize("extension", [".txt", ".md", ".markdown", ".MD"])
def test_extract_docs_from_supported_text_file(tmp_path: Path, extension: str) -> None:
    """Test extracting docs from a single text file with a supported extension."""
    path = tmp_path / f"example{extension}"
    path.write_text(PANGRAM, encoding="utf-8")
    images_root = tmp_path

    extraction = extract_docs([path], images_root)

    assert extraction.docs == [Doc(path=path, text=PANGRAM)]
    assert extraction.rejected_paths == []


@pytest.mark.parametrize("extension", [".pdf", ".PDF"])
def test_extract_docs_from_text_only_pdf_file(tmp_path: Path, extension: str) -> None:
    """Test extracting a doc from a text-only PDF file."""
    pdf_path = tmp_path / f"example{extension}"
    images_root = tmp_path
    text = "Only review what you need, when you need it!"
    _write_pdf(pdf_path, text)

    extraction = extract_docs([pdf_path], images_root)

    assert extraction.rejected_paths == []
    assert len(extraction.docs) == 1

    doc = extraction.docs[0]
    assert doc.path == pdf_path
    assert text in doc.text


def test_extract_docs_from_pdf_with_image(tmp_path: Path) -> None:
    """Test extracting a doc from a PDF with both text and image."""
    pdf_path = tmp_path / "example.pdf"
    images_root = tmp_path
    text = "Only review what you need, when you need it!"
    _write_pdf(pdf_path, text, with_image=True)

    extraction = extract_docs([pdf_path], images_root)

    doc = extraction.docs[0]
    assert text in doc.text
    assert doc.images_dir is not None
    assert len(list(doc.images_dir.iterdir())) == 1


@pytest.mark.parametrize("extension", ["", ".unsupported"])
def test_extract_docs_from_unsupported_file(tmp_path: Path, extension: str) -> None:
    """Test rejecting a file without a supported extension."""
    unsupported_path = tmp_path / f"example{extension}"
    unsupported_path.touch()
    images_root = tmp_path

    extraction = extract_docs([unsupported_path], images_root)

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
    images_root = tmp_path

    text1 = f"{PANGRAM} 1"
    text2 = f"{PANGRAM} 2"

    supported_path1.write_text(text1, encoding="utf-8")
    supported_path2.write_text(text2, encoding="utf-8")
    unsupported_path.touch()

    extraction = extract_docs(
        [supported_path1, unsupported_path, supported_path2],
        images_root,
    )

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
    images_root = tmp_path

    extraction = extract_docs([non_utf8_path], images_root)

    assert extraction.docs == []
    assert extraction.rejected_paths == [
        RejectedPath(path=non_utf8_path, reason=RejectionReason.NOT_UTF8_ENCODED),
    ]


def test_extract_docs_from_non_existent_file(tmp_path: Path) -> None:
    """Test trying to extract docs from a non-existing file."""
    fileless_path = tmp_path / "example.txt"
    images_root = tmp_path

    extraction = extract_docs([fileless_path], images_root)

    assert extraction.docs == []
    assert extraction.rejected_paths == [
        RejectedPath(path=fileless_path, reason=RejectionReason.READ_FAILED),
    ]
