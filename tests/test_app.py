"""Tests for the Gradio app."""

import gradio as gr
import pytest

from flashcard_generator import app as app_module
from flashcard_generator.card import BasicCard, GeneratedCards
from flashcard_generator.generate import DEFAULT_MODEL


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

    # Since run_flow() yields, list() helps collect its outputs
    list(app_module.run_flow(["example.md"], "dummy_model"))

    assert len(logs) == 1
    assert len(warnings) == 1
    assert "RuntimeError" in warnings[0]
    assert message in warnings[0]


@pytest.mark.parametrize(
    ("model_names", "expected_value"),
    [
        (["model1", DEFAULT_MODEL], DEFAULT_MODEL),
        (["model1", "model2"], "model1"),  # If default is absent, select first model
    ],
)
def test_update_model_choices(
    monkeypatch: pytest.MonkeyPatch,
    model_names: list[str],
    expected_value: str,
) -> None:
    """Test that the right model is selected among the choices."""

    def fake_list_model_names() -> list[str]:
        return model_names

    monkeypatch.setattr(app_module, "list_model_names", fake_list_model_names)

    update = app_module.update_model_choices()

    assert update["value"] == expected_value


def test_card_sharing() -> None:
    """Test the card-sharing lifecycle."""
    cards = GeneratedCards(cards=[BasicCard(front="front", back="back")])
    request = gr.Request(url={"port": 7860})

    assert app_module.get_shared_cards() is None

    app_module.start_sharing(cards, request)

    assert app_module.get_shared_cards() == cards.model_dump()

    app_module.stop_sharing()

    assert app_module.get_shared_cards() is None
