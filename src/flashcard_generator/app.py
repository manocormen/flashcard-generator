"""Gradio upload UI for the flashcard generator."""

import logging
import time
from collections.abc import Generator  # noqa: TC003
from pathlib import Path
from textwrap import indent
from typing import TYPE_CHECKING

import gradio as gr

from flashcard_generator.clean import clean_docs
from flashcard_generator.extract import (
    Doc,
    ExtractionResult,
    RejectionReason,
    extract_docs,
)
from flashcard_generator.generate import generate_cards
from flashcard_generator.prompt import Prompt, build_prompt

if TYPE_CHECKING:
    from flashcard_generator.card import GeneratedCards

type ViewState = tuple[gr.Column, gr.Column, gr.Column, str, str]

LOGGER = logging.getLogger(__name__)

CSS = """
#app-title {
    text-align: center;
}
"""

STEPS = (
    "Files uploaded",
    "Text extracted",
    "Text cleaned",
    "Prompt built",
    "Cards generated",
)

STEPS_DELAY_SECONDS = 1  # To see the steps cascade in the UI


def render_progress(steps_completed: int) -> str:
    """Render pipeline progress as Markdown."""
    lines = ["### Processing...", ""]

    for index, stage in enumerate(STEPS):
        checkbox = "[x]" if index < steps_completed else "[ ]"

        lines.append(f"- {checkbox} {stage}")

    return "\n".join(lines)


def format_summary(
    extraction: ExtractionResult,
    cleaned_docs: list[Doc],
    prompt: Prompt,
    cards: GeneratedCards,
) -> str:
    """Format the temporary pipeline summary."""
    reason2label: dict[RejectionReason, str] = {
        RejectionReason.UNSUPPORTED_EXTENSION: "Unsupported file type",
        RejectionReason.NOT_UTF8_ENCODED: "Not UTF-8 encoded",
        RejectionReason.READ_FAILED: "Could not read file",
    }
    snippets = "\n".join(
        f"\t- {d.path.name}: \t\t{d.text[:16].strip()} ... [{len(d.text)} characters]"
        for d in cleaned_docs
    )
    rejected = "\n".join(
        f"\t- {r.path.name} \t\t{reason2label[r.reason]}"
        for r in extraction.rejected_paths
    )
    prompt_snippet = ""
    if cleaned_docs:
        prompt_snippet = (
            f"Built prompt:\n\n"
            f"\t{'-' * 40} START OF PROMPT SNIPPET {'-' * 40}\n"
            f"{indent(prompt.system[:158], '\t')}...\n"
            f"\t{'-' * 40}   END OF PROMPT SNIPPET   {'-' * 40}"
        )
    rendered_cards = "\n\n".join(
        [f"Card {i}:\n{c.front}\n{c.back}" for i, c in enumerate(cards.cards, start=1)],
    )

    return (
        f"Extracted and cleaned {len(cleaned_docs)} document(s):\n\n"
        f"{snippets}\n\n"
        f"Skipped {len(extraction.rejected_paths)} file(s):\n\n"
        f"{rejected}\n\n"
        f"{prompt_snippet}\n\n"
        f"Generated cards:\n\n{rendered_cards}"
    )


def show_upload_view() -> ViewState:
    """Show the file upload view."""
    return (
        gr.Column(visible=True),
        gr.Column(visible=False),
        gr.Column(visible=False),
        "",
        "",
    )


def show_progress_view(progress: str) -> ViewState:
    """Show the progress view with a pipeline progress indicator."""
    # gr.skip() avoids this bug: github.com/gradio-app/gradio/issues/13494
    return (
        gr.Column(visible=False),
        gr.Column(visible=True),
        gr.skip(),
        progress,
        gr.skip(),
    )


def show_summary_view(summary: str) -> ViewState:
    """Show the summary view with the pipeline results."""
    return (
        gr.Column(visible=False),
        gr.Column(visible=False),
        gr.Column(visible=True),
        "",
        summary,
    )


def run_flow(gradio_paths: list[str]) -> Generator[ViewState]:
    """Run the Gradio flashcard generation flow."""
    # Gradio passes paths to cached upload copies, not raw user-provided paths
    filepaths = [Path(gp) for gp in gradio_paths]

    try:
        yield show_progress_view(render_progress(steps_completed=1))

        time.sleep(STEPS_DELAY_SECONDS)
        extraction = extract_docs(filepaths)
        yield show_progress_view(render_progress(steps_completed=2))

        time.sleep(STEPS_DELAY_SECONDS)
        cleaned_docs = clean_docs(extraction.docs)
        yield show_progress_view(render_progress(steps_completed=3))

        time.sleep(STEPS_DELAY_SECONDS)
        prompt = build_prompt(cleaned_docs)
        yield show_progress_view(render_progress(steps_completed=4))

        time.sleep(STEPS_DELAY_SECONDS)
        cards = generate_cards(prompt)
        yield show_progress_view(render_progress(steps_completed=5))

        time.sleep(STEPS_DELAY_SECONDS)
        summary = format_summary(extraction, cleaned_docs, prompt, cards)
        yield show_summary_view(summary)

    except Exception as e:
        LOGGER.exception("There was an unexpected error while running the Gradio flow.")
        gr.Warning(
            f"Something went wrong while processing your files.<br>"
            f"Error: {type(e).__name__}: {e}<br>"
            f"Please try again.",
        )
        yield show_upload_view()


def create_app() -> gr.Blocks:
    """Return an app instance."""
    app = gr.Blocks(title="Flashcard Generator")
    with app:
        gr.Markdown("# Flashcard Generator", elem_id="app-title")

        with gr.Column(visible=True) as upload_view:
            files = gr.Files(
                label="Learning materials: .txt .md .markdown .pdf",
                file_types=[".txt", ".md", ".markdown", ".pdf"],
            )
            generate_button = gr.Button(
                value="Generate Flashcards",
                variant="primary",
                interactive=False,
            )

        with gr.Column(visible=False) as progress_view:
            progress_status = gr.Markdown()

        with gr.Column(visible=False) as summary_view:
            summary = gr.Textbox(label="Summary")
            start_over_button = gr.ClearButton(
                value="Start Over",
                components=[files, progress_status, summary],
            )

        files.change(
            fn=lambda files: gr.Button(interactive=bool(files)),
            inputs=files,
            outputs=generate_button,
        )

        outputs = [upload_view, progress_view, summary_view, progress_status, summary]
        generate_button.click(fn=run_flow, inputs=files, outputs=outputs)
        start_over_button.click(fn=show_upload_view, outputs=outputs)

    return app


demo = create_app()


def main() -> None:
    """Launch the app."""
    demo.launch(css=CSS)


if __name__ == "__main__":
    main()
