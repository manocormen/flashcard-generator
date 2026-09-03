"""Test flashcard-generation pipeline orchestration."""

from typing import TYPE_CHECKING

from flashcard_generator import pipeline as pipeline_module
from flashcard_generator.card import GeneratedCards
from flashcard_generator.extract import Doc, ExtractionResult
from flashcard_generator.pipeline import PipelineStep

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    import pytest

    from flashcard_generator.prompt import Prompt


def test_pipeline_preserves_images_until_generation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Test that extracted images exist through generation, then are deleted."""
    path = tmp_path / "example.pdf"
    extracted_images: list[Path] = []

    def fake_extract_docs(
        paths: Iterable[Path],
        images_root: Path,
    ) -> ExtractionResult:
        images_dir = images_root / "doc-000"
        images_dir.mkdir()
        image_path = images_dir / "image.png"
        image_path.touch()
        extracted_images.append(image_path)

        paths = tuple(paths)

        return ExtractionResult(
            docs=[Doc(path=paths[0], text="content", images_dir=images_dir)],
            rejected_paths=[],
        )

    def fake_generate_cards(prompt: Prompt, model: str) -> GeneratedCards:
        assert model == "model"
        assert prompt.images == extracted_images
        assert prompt.images[0].is_file()

        return GeneratedCards(cards=[])

    monkeypatch.setattr(pipeline_module, "extract_docs", fake_extract_docs)
    monkeypatch.setattr(pipeline_module, "generate_cards", fake_generate_cards)

    events = pipeline_module.run_pipeline([path], "model")
    try:
        for expected_step in (
            PipelineStep.FILES_UPLOADED,
            PipelineStep.TEXT_EXTRACTED,
            PipelineStep.TEXT_CLEANED,
            PipelineStep.PROMPT_BUILT,
            PipelineStep.CARDS_GENERATED,
        ):
            assert next(events) == expected_step

        assert len(extracted_images) == 1
        assert not extracted_images[0].exists()
    finally:
        events.close()  # Stop the pipeline after generation and cleanup on failure
