"""Flashcard-generation pipeline orchestration."""

import logging
import shutil
import tempfile
from dataclasses import dataclass
from enum import IntEnum, auto
from pathlib import Path
from pprint import pformat
from typing import TYPE_CHECKING

from flashcard_generator.chunk import chunk_docs
from flashcard_generator.clean import clean_docs, clean_text
from flashcard_generator.embed import embed_docs
from flashcard_generator.export import ExportedCards, export_cards
from flashcard_generator.extract import extract_docs
from flashcard_generator.generate import generate_cards
from flashcard_generator.prompt import build_prompt
from flashcard_generator.retrieve import retrieve_docs

if TYPE_CHECKING:
    from collections.abc import Generator

    from flashcard_generator.card import GeneratedCards

IMAGES_TMP_DIR_PREFIX = "flashcard-generator-images-"
MIN_SIMILARITY = 0.65

LOGGER = logging.getLogger(__name__)


class PipelineStep(IntEnum):
    """Pipeline steps in execution order."""

    FILES_UPLOADED = auto()
    CONTENT_EXTRACTED = auto()
    TEXT_CLEANED = auto()
    PROMPT_BUILT = auto()
    CARDS_GENERATED = auto()
    CARDS_EXPORTED = auto()


@dataclass
class PipelineResult:
    """Contain the generated cards and their exports."""

    cards: GeneratedCards
    export: ExportedCards


type PipelineEvent = PipelineStep | PipelineResult


def run_pipeline(
    paths: list[Path],
    model: str,
    topic: str = "",
) -> Generator[PipelineEvent]:
    """Run the flashcard-generation pipeline."""
    yield PipelineStep.FILES_UPLOADED

    with tempfile.TemporaryDirectory(prefix=IMAGES_TMP_DIR_PREFIX) as tmp_dir:
        images_root = Path(tmp_dir)

        extraction = extract_docs(paths, images_root)
        LOGGER.info(
            "Extracted %s document(s); skipped %s file(s).",
            len(extraction.docs),
            len(extraction.rejected_paths),
        )
        LOGGER.debug("Extraction result:\n%s", pformat(extraction, width=120))
        yield PipelineStep.CONTENT_EXTRACTED

        cleaned_docs = clean_docs(extraction.docs)
        topic = clean_text(topic)
        LOGGER.info("Cleaned %s document(s).", len(cleaned_docs))
        LOGGER.debug("Cleaned document(s):\n%s", pformat(cleaned_docs, width=120))
        yield PipelineStep.TEXT_CLEANED

        if topic:
            chunked_docs = chunk_docs(cleaned_docs)
            LOGGER.info(
                "Chunked %s document(s) into %s chunks.",
                len(chunked_docs),
                sum(len(doc.chunks) for doc in chunked_docs),
            )
            LOGGER.debug("Chunked document(s):\n%s", pformat(chunked_docs, width=120))

            embedding_result = embed_docs(chunked_docs, topic)
            LOGGER.info(
                "Embedded topic and %s document(s) (%s chunks) into %sD vectors.",
                len(embedding_result.docs),
                sum(len(doc.chunks) for doc in embedding_result.docs),
                len(embedding_result.topic_vector),
            )

            retrieved_docs = retrieve_docs(embedding_result, MIN_SIMILARITY)
            LOGGER.info(
                "Retrieved %s document(s) (%s chunks) per %s similarity threshold.",
                len(retrieved_docs),
                sum(len(doc.chunks) for doc in retrieved_docs),
                MIN_SIMILARITY,
            )

        prompt = build_prompt(cleaned_docs)
        LOGGER.info("Prompt built.")
        LOGGER.debug("Prompt built:\n%s", pformat(prompt, width=120))
        yield PipelineStep.PROMPT_BUILT

        cards = generate_cards(prompt, model)
    LOGGER.info("Generated %s card(s).", len(cards.cards))
    LOGGER.debug("Generated card(s):\n%s", cards.model_dump_json(indent=2))
    yield PipelineStep.CARDS_GENERATED

    output_dir = Path(tempfile.mkdtemp(prefix="flashcard-generator-"))
    try:
        export = export_cards(cards, output_dir)
    except Exception:
        shutil.rmtree(output_dir, ignore_errors=True)  # Don't mask original error
        raise
    LOGGER.info("Exported card file(s): %s.", output_dir)
    LOGGER.debug("Exported card file(s):\n%s", pformat(export, width=120))
    yield PipelineStep.CARDS_EXPORTED

    yield PipelineResult(cards=cards, export=export)
