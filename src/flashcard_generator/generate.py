"""Generated flashcards by prompting the model."""

from typing import TYPE_CHECKING

import ollama

from flashcard_generator.card import (
    generated_cards_json_schema,
    parse_generated_cards_json,
)

if TYPE_CHECKING:
    from flashcard_generator.card import GeneratedCards
    from flashcard_generator.prompt import Prompt

DEFAULT_MODEL: str = "gemma4:latest"  # Sane general-purpose default, to get started


def generate_cards(prompt: Prompt, model: str = DEFAULT_MODEL) -> GeneratedCards:
    """Generate flashcards by prompting the model."""
    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": prompt.system},
            {"role": "user", "content": prompt.user},
        ],
        format=generated_cards_json_schema(),
        # Low temperatures are recommended for structured outputs:
        # https://docs.ollama.com/capabilities/structured-outputs#tips-for-reliable-structured-outputs
        options={"temperature": 0},
    )

    cards_json = response.message.content
    if cards_json is None:
        message = "Ollama response didn't include card JSON data."
        raise ValueError(message)

    return parse_generated_cards_json(cards_json)


def list_model_names() -> list[str]:
    """Return the names of the Ollama models available locally."""
    models = ollama.list().models
    model_names = [m.model for m in models if m.model is not None]

    return sorted(model_names)
