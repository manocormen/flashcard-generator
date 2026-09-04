"""Tests for prompt building."""

from pathlib import Path

from flashcard_generator.extract import Doc
from flashcard_generator.prompt import build_prompt


def test_system_prompt_elements() -> None:
    """Test that the system subprompt contains the expected core elements."""
    prompt = build_prompt([])

    system = prompt.system.lower()

    assert "role" in system
    assert "flashcard" in system
    assert "quality" in system
    assert "learning materials" in system
    assert "principles" in system
    assert "atomic" in system
    assert "selective" in system
    assert "grounded" in system
    assert "image" in system
    assert "format" in system
    assert "json" in system
    assert "front" in system
    assert "back" in system


def test_user_prompt_elements() -> None:
    """Test that the user subprompt contains the expected core elements."""
    path = Path("example.md")
    text = "Memorize anything efficiently with AnkiDroid!"

    prompt = build_prompt([Doc(path=path, text=text)])

    user = prompt.user

    assert "<document" in user
    assert 'index="1"' in user
    assert 'filename="example.md"' in user
    assert text in user
    assert "image" in user
    assert "</document>" in user
    assert prompt.images == []


def test_user_prompt_elements_order() -> None:
    """Test that the user subprompt documents are ordered correctly."""
    doc1 = Doc(path=Path("example1.md"), text="content1")
    doc2 = Doc(path=Path("example2.md"), text="content2")

    prompt = build_prompt([doc1, doc2])

    user = prompt.user

    assert user.index('index="1"') < user.index('index="2"')
    assert user.index("example1.md") < user.index("example2.md")
    assert user.index("content1") < user.index("content2")


def test_prompt_images_order(tmp_path: Path) -> None:
    """Test that prompt images are ordered by document, then filename."""
    images_dir1 = tmp_path / "images2"
    images_dir2 = tmp_path / "images1"
    images_dir1.mkdir()
    images_dir2.mkdir()

    image11 = images_dir1 / "image1.png"
    image12 = images_dir1 / "image2.png"
    image21 = images_dir2 / "image1.png"
    image12.touch()
    image11.touch()
    image21.touch()

    docs = (
        Doc(path=Path("example1.pdf"), text="content1", images_dir=images_dir1),
        Doc(path=Path("example2.pdf"), text="content2", images_dir=images_dir2),
    )

    prompt = build_prompt(iter(docs))

    assert all(doc.text in prompt.user for doc in docs)
    assert prompt.images == [image11, image12, image21]
