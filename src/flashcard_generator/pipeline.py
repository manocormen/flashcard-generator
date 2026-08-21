"""Flashcard-generation pipeline orchestration."""

import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path
from pprint import pformat
from typing import TYPE_CHECKING

from flashcard_generator.clean import clean_docs
from flashcard_generator.export import ExportedCards, export_cards
from flashcard_generator.extract import extract_docs
from flashcard_generator.generate import generate_cards
from flashcard_generator.prompt import build_prompt

if TYPE_CHECKING:
    from collections.abc import Generator

    from flashcard_generator.card import GeneratedCards

LOGGER = logging.getLogger(__name__)


@dataclass
class PipelineProgress:
    """Report completed pipeline steps."""

    steps_completed: int


@dataclass
class PipelineResult:
    """Contain the generated cards and their exports."""

    cards: GeneratedCards
    export: ExportedCards


type PipelineEvent = PipelineProgress | PipelineResult


def run_pipeline(paths: list[Path], model: str) -> Generator[PipelineEvent]:
    """Run the flashcard-generation pipeline."""
    yield PipelineProgress(steps_completed=1)

    extraction = extract_docs(paths)
    LOGGER.info(
        "Extracted %s document(s); skipped %s file(s).",
        len(extraction.docs),
        len(extraction.rejected_paths),
    )
    LOGGER.debug("Extraction result:\n%s", pformat(extraction, width=120))
    yield PipelineProgress(steps_completed=2)

    cleaned_docs = clean_docs(extraction.docs)
    LOGGER.info("Cleaned %s document(s).", len(cleaned_docs))
    LOGGER.debug("Cleaned document(s):\n%s", pformat(cleaned_docs, width=120))
    yield PipelineProgress(steps_completed=3)

    prompt = build_prompt(cleaned_docs)
    LOGGER.info("Prompt built.")
    LOGGER.debug("Prompt built:\n%s", pformat(prompt, width=120))
    yield PipelineProgress(steps_completed=4)

    cards = generate_cards(prompt, model)
    LOGGER.info("Generated %s card(s).", len(cards.cards))
    LOGGER.debug("Generated card(s):\n%s", cards.model_dump_json(indent=2))
    yield PipelineProgress(steps_completed=5)

    output_dir = Path(tempfile.mkdtemp(prefix="flashcard-generator-"))
    export = export_cards(cards, output_dir)
    LOGGER.info("Exported card file(s): %s.", output_dir)
    LOGGER.debug("Exported card file(s):\n%s", pformat(export, width=120))
    yield PipelineProgress(steps_completed=6)

    yield PipelineResult(cards=cards, export=export)
