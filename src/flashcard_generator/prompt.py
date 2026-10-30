"""Build prompts for generating flashcards."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from flashcard_generator.chunk import Chunk, ChunkedDoc
    from flashcard_generator.extract import Doc

SYSTEM_PROMPT = """
## Role

You're an expert flashcard maker. You create high-quality flashcards from learning
materials provided by the user. You strictly follow the principles of flashcard making
and output flashcards in a specific format, both described below.

## Principles

A good flashcard should be:

- atomic: cover one concept per card.
- selective: focus on the most important concepts.
- concise: front and back should be worded succinctly.
- grounded: directly stem from the learning materials.

And the deck as a whole should ensure good coverage: cover all important concepts,
including those conveyed by images.

## Format

You output flashcards in a JSON format that corresponds to the Anki Basic note type:
each item represents a card with two keys: `front` and `back`.
"""

TOPIC_INSTRUCTIONS = """
## Scope

Limit the deck to the concepts relevant to the provided topic.
"""

USER_PROMPT_PREFIX = """
## Learning Materials

The JSON flashcards should be strictly based on the following learning materials,
including any attached images.
"""


@dataclass(kw_only=True)
class Prompt:
    """Prompt for querying an LLM."""

    system: str
    user: str
    images: list[Path] = field(default_factory=list)


def build_prompt(docs: Iterable[Doc]) -> Prompt:
    """Build a prompt using the given docs."""
    docs = tuple(docs)  # To be able to consume it twice below

    return Prompt(
        system=SYSTEM_PROMPT.strip(),
        user=f"{USER_PROMPT_PREFIX.strip()}\n\n{_render_docs(docs)}",
        images=_gather_images(docs),
    )


def build_topic_prompt(docs: Iterable[ChunkedDoc], topic: str) -> Prompt:
    """Build a prompt using the given chunked docs and topic."""
    docs = tuple(docs)

    user_prompt = (
        f"## Topic\n\n{topic}\n\n{USER_PROMPT_PREFIX.strip()}\n\n"
        f"Note that these are excerpts: they may omit intervening "
        f"material and shouldn't be treated as continuous text.\n\n"
        f"{_render_chunked_docs(docs)}"
    )

    return Prompt(
        system=f"{SYSTEM_PROMPT.strip()}\n\n{TOPIC_INSTRUCTIONS.strip()}",
        user=user_prompt,
        images=_gather_chunk_images(docs),
    )


def _render_docs(docs: Iterable[Doc]) -> str:
    """Render the learning materials for the prompt."""
    return "\n\n".join(
        _render_doc(index, doc) for index, doc in enumerate(docs, start=1)
    )


def _render_doc(index: int, doc: Doc) -> str:
    """Render a single document for the prompt."""
    return (
        f'<document index="{index}" filename="{doc.path.name}">\n'
        f"{doc.text}\n</document>"
    )


def _render_chunked_docs(docs: Iterable[ChunkedDoc]) -> str:
    """Render all the chunked docs for the prompt."""
    return "\n\n".join(
        _render_chunked_doc(index, doc) for index, doc in enumerate(docs, start=1)
    )


def _render_chunked_doc(index: int, doc: ChunkedDoc) -> str:
    """Render a single chunked document for the prompt."""
    rendered_chunks = "\n\n".join(_render_chunk(chunk) for chunk in doc.chunks)

    return (
        f'<document index="{index}" filename="{doc.doc.path.name}">\n'
        f"{rendered_chunks}\n</document>"
    )


def _render_chunk(chunk: Chunk) -> str:
    """Render a single chunk for the prompt."""
    text = chunk.text

    breadcrumb = " > ".join(chunk.headings.values())
    if breadcrumb:
        text = f"{breadcrumb}\n\n{text}"

    return f'<excerpt index="{chunk.index + 1}">\n{text}\n</excerpt>'


def _gather_images(docs: Iterable[Doc]) -> list[Path]:
    """Return image paths in document and filename order."""
    image_paths = []

    for doc in docs:
        if doc.images_dir is not None:
            image_paths.extend(sorted(doc.images_dir.iterdir()))

    return image_paths


def _gather_chunk_images(docs: Iterable[ChunkedDoc]) -> list[Path]:
    """Return image paths in all chunked documents."""
    return [image for doc in docs for chunk in doc.chunks for image in chunk.images]
