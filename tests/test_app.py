"""Tests for the Gradio app."""

from typing import TYPE_CHECKING

import gradio as gr

from flashcard_generator import app as app_module

if TYPE_CHECKING:
    import pytest


def test_create_app() -> None:
    """Test that create_app() returns a valid Gradio instance."""
    app = app_module.create_app()

    assert type(app) is gr.Blocks


def test_run_flow_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that errors during the Gradio flow are logged and shown."""
    message = "Error during document extraction."

    def raise_error(_paths: object) -> None:
        raise RuntimeError(message)

    logs: list[str] = []
    warnings: list[str] = []

    monkeypatch.setattr(app_module, "extract_docs", raise_error)
    monkeypatch.setattr(app_module, "STEPS_DELAY_SECONDS", 0)
    monkeypatch.setattr(app_module.LOGGER, "exception", logs.append)
    monkeypatch.setattr(gr, "Warning", warnings.append)

    list(app_module.run_flow(["example.md"]))  # run_flow yields: list helps consume it

    assert len(logs) == 1
    assert len(warnings) == 1
    assert "RuntimeError" in warnings[0]
    assert message in warnings[0]
