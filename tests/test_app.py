"""Tests for the Gradio app."""

from types import SimpleNamespace

import gradio as gr
import pytest
from PIL import Image

from flashcard_generator import app as app_module
from flashcard_generator.card import BasicCard, GeneratedCards
from flashcard_generator.generate import DEFAULT_MODEL


def test_run_generation_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that errors during card generation are logged and shown."""
    message = "Error during document extraction."

    def raise_error(_paths: object, _model: str) -> None:
        raise RuntimeError(message)

    logs: list[str] = []
    warnings: list[str] = []

    monkeypatch.setattr(app_module, "run_pipeline", raise_error)
    monkeypatch.setattr(app_module.LOGGER, "exception", logs.append)
    monkeypatch.setattr(gr, "Warning", warnings.append)

    # Since run_generation() yields, list() helps collect its outputs
    list(app_module.run_generation(["example.md"], "dummy_model"))

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

    dropdown = app_module.update_model_choices()

    assert dropdown.value == expected_value


def test_card_sharing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the card-sharing lifecycle."""
    cards = GeneratedCards(cards=[BasicCard(front="front", back="back")])
    request = gr.Request(url={"port": 7860})
    lan_ip = "192.168.0.1"
    qr_urls = []
    qr_code = Image.new("1", (1, 1))
    expected_url = "http://192.168.0.1:7860/gradio_api/api/cards"

    def fake_get_lan_ip() -> str:
        return lan_ip

    def fake_make(url: str) -> SimpleNamespace:
        qr_urls.append(url)
        return SimpleNamespace(get_image=lambda: qr_code)

    monkeypatch.setattr("flashcard_generator.app.get_lan_ip", fake_get_lan_ip)
    monkeypatch.setattr("flashcard_generator.share.qrcode.make", fake_make)

    assert app_module.get_shared_cards() is None

    share_update = app_module.start_sharing(cards, request)

    assert app_module.get_shared_cards() == cards.model_dump()
    assert qr_urls == [expected_url]
    assert expected_url in share_update[app_module.share_instructions]
    assert share_update[app_module.share_qr_image] is qr_code

    app_module.stop_sharing()

    assert app_module.get_shared_cards() is None
