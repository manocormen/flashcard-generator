"""Gradio upload UI for the flashcard generator."""

import time
from collections.abc import Generator  # noqa: TC003
from pathlib import Path

import gradio as gr

from flashcard_generator.clean import clean_docs
from flashcard_generator.extract import (
    Doc,
    ExtractionResult,
    RejectionReason,
    extract_docs,
)

type ViewState = tuple[gr.Column, gr.Column, gr.Column, str, str]

CSS = """
#app-title {
    text-align: center;
}
"""

STEPS = ("Files uploaded", "Text extracted", "Text cleaned")

STEPS_DELAY = 1  # TEMP: to see the steps cascade in the UI


def render_progress(steps_completed: int) -> str:
    """Render pipeline progress as Markdown."""
    lines = ["### Processing...", ""]

    for index, stage in enumerate(STEPS):
        checkbox = "[x]" if index < steps_completed else "[ ]"

        lines.append(f"- {checkbox} {stage}")

    return "\n".join(lines)


def format_summary(extraction: ExtractionResult, cleaned_docs: list[Doc]) -> str:
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
    warning = "Notes:\n\n\t- Flashcard generation not implemented yet."

    return (
        f"Extracted and cleaned {len(cleaned_docs)} document(s):\n\n"
        f"{snippets}\n\n"
        f"Skipped {len(extraction.rejected_paths)} file(s):\n\n"
        f"{rejected}\n\n"
        f"{warning}"
    )


def show_progress_view(progress: str) -> ViewState:
    """Show the progress view when the pipeline starts."""
    # TEMP: gr.skip() avoids this bug: github.com/gradio-app/gradio/issues/13494
    return (
        gr.Column(visible=False),
        gr.Column(visible=True),
        gr.skip(),
        progress,
        gr.skip(),
    )


def update_progress_view(progress: str) -> ViewState:
    """Update the progress view to reflect the current pipeline step."""
    # TEMP: gr.skip() avoids this bug: github.com/gradio-app/gradio/issues/13494
    return (
        gr.skip(),
        gr.skip(),
        gr.skip(),
        progress,
        gr.skip(),
    )


def show_summary_view(summary: str) -> ViewState:
    """Show the summary view with the pipeline results."""
    # TEMP: gr.skip() avoids this bug: github.com/gradio-app/gradio/issues/13494
    return (
        gr.Column(visible=False),
        gr.Column(visible=False),
        gr.Column(visible=True),
        gr.skip(),
        summary,
    )


def run_flow(gradio_paths: list[str] | None) -> Generator[ViewState]:
    """Run the Gradio flashcard generation flow."""
    if not gradio_paths:
        yield show_summary_view("You didn't upload anything.")
        return

    # Gradio passes paths to cached upload copies, not raw user-provided paths
    filepaths = [Path(gp) for gp in gradio_paths]

    yield show_progress_view(render_progress(steps_completed=1))

    time.sleep(STEPS_DELAY)
    extraction = extract_docs(filepaths)
    yield update_progress_view(render_progress(steps_completed=2))

    time.sleep(STEPS_DELAY)
    cleaned_docs = clean_docs(extraction.docs)
    yield update_progress_view(render_progress(steps_completed=3))

    time.sleep(STEPS_DELAY)
    summary = format_summary(extraction, cleaned_docs)
    yield show_summary_view(summary)


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
            button = gr.Button(value="Generate Flashcards", variant="primary")

        with gr.Column(visible=False) as progress_view:
            progress_status = gr.Markdown()

        with gr.Column(visible=False) as summary_view:
            summary = gr.Textbox(label="Summary")

        button.click(
            fn=run_flow,
            inputs=files,
            outputs=[
                upload_view,
                progress_view,
                summary_view,
                progress_status,
                summary,
            ],
        )

    return app


demo = create_app()


def main() -> None:
    """Launch the app."""
    demo.launch(css=CSS)


if __name__ == "__main__":
    main()
