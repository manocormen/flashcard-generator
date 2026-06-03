"""Gradio upload UI for the flashcard generator."""

from pathlib import Path

import gradio as gr

from flashcard_generator.clean import clean_docs
from flashcard_generator.extract import RejectionReason, extract_docs

CSS = """
#app-title {
    text-align: center;
}
"""


def process_uploads(gradio_paths: list[str] | None) -> str:
    """Process the uploaded files."""
    if not gradio_paths:
        return "You didn't upload anything."

    # Gradio passes paths to cached upload copies, not raw user-provided paths
    filepaths = [Path(gp) for gp in gradio_paths]
    extraction = extract_docs(filepaths)
    cleaned_docs = clean_docs(extraction.docs)

    # Return temporary status output while the pipeline is incomplete
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


def create_app() -> gr.Blocks:
    """Return an app instance."""
    app = gr.Blocks(title="Flashcard Generator")
    with app:
        gr.Markdown("# Flashcard Generator", elem_id="app-title")
        files = gr.Files(
            label="Learning materials: .txt .md .markdown .pdf",
            file_types=[".txt", ".md", ".markdown", ".pdf"],
        )
        button = gr.Button(value="Generate Flashcards", variant="primary")
        output = gr.Textbox(label="Summary")

        button.click(fn=process_uploads, inputs=files, outputs=output)

    return app


demo = create_app()


def main() -> None:
    """Launch the app."""
    demo.launch(css=CSS)


if __name__ == "__main__":
    main()
