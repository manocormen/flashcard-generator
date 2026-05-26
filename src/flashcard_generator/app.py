"""Gradio upload UI for the flashcard generator."""

from pathlib import Path

import gradio as gr

from flashcard_generator.extract import extract_docs


def process_uploads(gradio_paths: list[str] | None) -> str:
    """Process the uploaded files."""
    if not gradio_paths:
        return "You didn't upload anything."

    filepaths = [Path(gp) for gp in gradio_paths]
    extraction = extract_docs(filepaths)

    unsupported = "\n".join(f"\t- {p.name}" for p in extraction.unsupported_paths)
    snippets = "\n".join(
        f"\t- {d.path.name}: \t\t{d.text[:30].strip()} ... [{len(d.text)} characters]"
        for d in extraction.docs
    )
    warning = (
        "Notes:\n\n"
        "\t- PDF support not implemented yet.\n"
        "\t- Flashcard generation not implemented yet."
    )

    return (
        f"Extracted {len(extraction.docs)} documents:\n\n"
        f"{snippets}\n\n"
        f"Skipped {len(extraction.unsupported_paths)} unsupported files:\n\n"
        f"{unsupported}\n\n"
        f"{warning}"
    )


def create_app() -> gr.Interface:
    """Return an app instance."""
    return gr.Interface(
        fn=process_uploads,
        inputs=gr.Files(
            label="Learning materials: .txt .md .markdown .pdf",
            file_types=[".txt", ".md", ".markdown", ".pdf"],
        ),
        outputs="text",
        title="Flashcard Generator",
        submit_btn="Generate Flashcards",
        clear_btn=None,
        flagging_mode="never",
    )


demo = create_app()


def main() -> None:
    """Launch the app."""
    demo.launch()


if __name__ == "__main__":
    main()
