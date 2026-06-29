"""Test card generation."""

import json
from types import SimpleNamespace

import pytest

from flashcard_generator.card import generated_cards_json_schema
from flashcard_generator.generate import generate_cards, list_model_names
from flashcard_generator.prompt import Prompt


def test_generate_cards_args_and_return(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test generating cards with Ollama with structured outputs."""
    prompt = Prompt(system="system", user="user")
    cards_json = json.dumps({"cards": [{"front": "front", "back": "back"}]})

    args = []

    def fake_chat(**kwargs: object) -> SimpleNamespace:
        args.append(kwargs)
        return SimpleNamespace(message=SimpleNamespace(content=cards_json))

    monkeypatch.setattr("flashcard_generator.generate.ollama.chat", fake_chat)

    generated_cards = generate_cards(prompt, model="model")

    assert args == [
        {
            "model": "model",
            "messages": [
                {"role": "system", "content": "system"},
                {"role": "user", "content": "user"},
            ],
            "format": generated_cards_json_schema(),
            "options": {"temperature": 0},
        },
    ]

    assert generated_cards.cards[0].front == "front"
    assert generated_cards.cards[0].back == "back"


def test_missing_cards_json_raises_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that missing Ollama message content raises ValueError."""
    prompt = Prompt(system="system", user="user")

    def return_nested_none(**_kwargs: object) -> SimpleNamespace:
        return SimpleNamespace(message=SimpleNamespace(content=None))

    monkeypatch.setattr("flashcard_generator.generate.ollama.chat", return_nested_none)

    with pytest.raises(
        ValueError,
        match=r"Ollama response didn't include card JSON data.",
    ):
        generate_cards(prompt, model="model")


def test_list_model_names(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that local Ollama model names are correctly returned."""

    def fake_list() -> SimpleNamespace:
        return SimpleNamespace(
            models=[
                SimpleNamespace(model="model2"),
                SimpleNamespace(model=None),
                SimpleNamespace(model="model1"),
            ],
        )

    monkeypatch.setattr("flashcard_generator.generate.ollama.list", fake_list)

    assert list_model_names() == ["model1", "model2"]
