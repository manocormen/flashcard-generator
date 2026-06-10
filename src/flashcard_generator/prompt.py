"""Build prompts for generating flashcards."""

from dataclasses import dataclass


@dataclass(kw_only=True)
class Prompt:
    """Prompt for querying an LLM."""

    system: str
    user: str
