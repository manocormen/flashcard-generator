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
    assert "</document>" in user


def test_user_prompt_elements_order() -> None:
    """Test that the user subprompt documents are ordered correctly."""
    doc1 = Doc(path=Path("example1.md"), text="content1")
    doc2 = Doc(path=Path("example2.md"), text="content2")

    prompt = build_prompt([doc1, doc2])

    user = prompt.user

    assert user.index('index="1"') < user.index('index="2"')
    assert user.index("example1.md") < user.index("example2.md")
    assert user.index("content1") < user.index("content2")
