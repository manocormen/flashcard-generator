"""Package Tests."""

import importlib


def test_package_import() -> None:
    """Test that the app package can be imported."""
    assert importlib.import_module("flashcard_generator")
