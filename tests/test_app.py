"""Tests for the Gradio app."""

import gradio as gr

from flashcard_generator.app import create_app


def test_create_app() -> None:
    """Test that create_app() returns a valid Gradio instance."""
    app = create_app()

    assert isinstance(app, gr.Interface)
