"""Gradio upload UI for the flashcard generator."""

from pathlib import Path

import gradio as gr


def report_uploads(filepaths: list[str] | None) -> str:
    """Return a temporary message listing the uploaded files."""
    if not filepaths:
        return "You didn't upload anything."

    filenames = [Path(fp).name for fp in filepaths]
    bullets = "\n".join(f"\t- {fn}" for fn in filenames)
    warning = "Flashcard generation not implemented yet."

    return f"You uploaded {len(filenames)} files:\n\n{bullets}\n\n{warning}"


def create_app() -> gr.Interface:
    """Return an app instance."""
    return gr.Interface(
        fn=report_uploads,
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


def main() -> None:
    """Launch the app."""
    create_app().launch()


if __name__ == "__main__":
    main()
