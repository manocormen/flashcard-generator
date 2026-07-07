"""Gradio upload UI for the flashcard generator."""

import logging
import os
import shutil
import socket
import tempfile
import time
from collections.abc import Generator  # noqa: TC003
from pathlib import Path
from pprint import pformat
from typing import Any

import gradio as gr

from flashcard_generator.card import GeneratedCards
from flashcard_generator.clean import clean_docs
from flashcard_generator.export import ExportedCards, export_cards
from flashcard_generator.extract import extract_docs
from flashcard_generator.generate import DEFAULT_MODEL, generate_cards, list_model_names
from flashcard_generator.prompt import build_prompt
from flashcard_generator.share import CardShare

# TODO: Once stabilized, update to a type with named slots, for readability
type ViewState = tuple[
    gr.Column,
    gr.Column,
    gr.Column,
    gr.Column,
    str,
    str,
    GeneratedCards | None,
    ExportedCards | None,
    str,
]
type GradioUpdate = dict[str, Any]

card_share = CardShare()

# Explicit name needed because just dev runs this file as __main__
LOGGER = logging.getLogger("flashcard_generator.app")

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
    "Downloads ready",
)

STEPS_DELAY_SECONDS = 1  # To see the steps cascade in the UI

BIND_ADDRESS = "0.0.0.0"  # noqa: S104
CARDS_ENDPOINT = "/gradio_api/api/cards"


def render_progress(steps_completed: int) -> str:
    """Render pipeline progress as Markdown."""
    lines = ["### Processing...", ""]

    for index, stage in enumerate(STEPS):
        checkbox = "[x]" if index < steps_completed else "[ ]"

        lines.append(f"- {checkbox} {stage}")

    return "\n".join(lines)


def show_upload_view() -> ViewState:
    """Show the file upload view."""
    return (
        gr.Column(visible=True),
        gr.Column(visible=False),
        gr.Column(visible=False),
        gr.Column(visible=False),
        "",
        "",
        None,
        None,
        "",
    )


def show_progress_view(progress: str) -> ViewState:
    """Show the progress view with a pipeline progress indicator."""
    # gr.skip() avoids this bug: github.com/gradio-app/gradio/issues/13494
    return (
        gr.Column(visible=False),
        gr.Column(visible=True),
        gr.skip(),
        gr.skip(),
        progress,
        gr.skip(),
        gr.skip(),
        gr.skip(),
        gr.skip(),
    )


def show_results_view(
    generated_cards: GeneratedCards | None,
    rendered_cards: str | None,
    export: ExportedCards,
) -> ViewState:
    """Show the rendered cards and export options."""
    return (
        gr.Column(visible=False),
        gr.Column(visible=False),
        gr.Column(visible=True),
        gr.skip(),
        "",
        rendered_cards if rendered_cards is not None else "No cards generated.",
        generated_cards,
        export,
        gr.skip(),
    )


def show_share_view(share_url: str) -> ViewState:
    """Show the view for sharing cards locally."""
    return (
        gr.Column(visible=False),
        gr.Column(visible=False),
        gr.Column(visible=False),
        gr.Column(visible=True),
        gr.skip(),
        gr.skip(),
        gr.skip(),
        gr.skip(),
        f"Card sharing endpoint: POST `{share_url}`",
    )


def exit_share_view() -> ViewState:
    """Return to the results view after sharing."""
    return (
        gr.Column(visible=False),
        gr.Column(visible=False),
        gr.Column(visible=True),
        gr.Column(visible=False),
        gr.skip(),
        gr.skip(),
        gr.skip(),
        gr.skip(),
        gr.skip(),
    )


def run_flow(gradio_paths: list[str], model: str) -> Generator[ViewState]:
    """Run the Gradio flashcard generation flow."""
    # Gradio passes paths to cached upload copies, not raw user-provided paths
    filepaths = [Path(gp) for gp in gradio_paths]

    try:
        yield show_progress_view(render_progress(steps_completed=1))

        time.sleep(STEPS_DELAY_SECONDS)
        extraction = extract_docs(filepaths)
        LOGGER.info(
            "Extracted %s document(s); skipped %s file(s).",
            len(extraction.docs),
            len(extraction.rejected_paths),
        )
        LOGGER.debug("Extraction result:\n%s", pformat(extraction, width=120))
        yield show_progress_view(render_progress(steps_completed=2))

        time.sleep(STEPS_DELAY_SECONDS)
        cleaned_docs = clean_docs(extraction.docs)
        LOGGER.info("Cleaned %s document(s).", len(cleaned_docs))
        LOGGER.debug("Cleaned document(s):\n%s", pformat(cleaned_docs, width=120))
        yield show_progress_view(render_progress(steps_completed=3))

        time.sleep(STEPS_DELAY_SECONDS)
        prompt = build_prompt(cleaned_docs)
        LOGGER.info("Prompt built.")
        LOGGER.debug("Prompt built:\n%s", pformat(prompt, width=120))
        yield show_progress_view(render_progress(steps_completed=4))

        time.sleep(STEPS_DELAY_SECONDS)
        cards = generate_cards(prompt, model)
        LOGGER.info("Generated %s card(s).", len(cards.cards))
        LOGGER.debug("Generated card(s):\n%s", cards.model_dump_json(indent=2))
        yield show_progress_view(render_progress(steps_completed=5))

        time.sleep(STEPS_DELAY_SECONDS)
        output_dir = Path(tempfile.mkdtemp(prefix="flashcard-generator-"))
        export = export_cards(cards, output_dir)
        LOGGER.info("Exported card file(s): %s.", output_dir)
        LOGGER.debug("Exported card file(s):\n%s", pformat(export, width=120))
        yield show_progress_view(render_progress(steps_completed=6))

        time.sleep(STEPS_DELAY_SECONDS)
        rendered_cards = render_cards(cards)
        yield show_results_view(cards, rendered_cards, export)

    except Exception as e:
        LOGGER.exception("There was an unexpected error while running the Gradio flow.")
        gr.Warning(
            f"Something went wrong while processing your files.<br>"
            f"Error: {type(e).__name__}: {e}<br>"
            f"Please try again.",
        )
        yield show_upload_view()


def render_cards(cards: GeneratedCards) -> str | None:
    """Return the generated cards cleanly formatted in Markdown."""
    if not cards.cards:
        return None

    rendered_cards = []

    for index, card in enumerate(cards.cards, start=1):
        rendered_card = "\n\n".join(
            [
                f"### Card {index}",
                card.front,
                card.back,
            ],
        )
        rendered_cards.append(rendered_card)

    return "\n\n---\n\n".join(rendered_cards)


def get_filepath(format_: str, export: ExportedCards | None) -> Path | None:
    """Return the filepath for the chosen format."""
    if export is None:
        return None

    match format_:
        case "CSV":
            return export.csv_path
        case "JSON":
            return export.json_path
        case _:
            return None


def cleanup_export(export: ExportedCards | None) -> None:
    """Delete the exported card files."""
    if export is None:
        return

    shutil.rmtree(export.json_path.parent)


def reset_app_state(export: ExportedCards | None) -> ViewState:
    """Delete exported files and return to the upload view."""
    cleanup_export(export)
    card_share.stop()

    return show_upload_view()


def update_model_choices() -> GradioUpdate:
    """Update the model dropdown to reflect the models available locally."""
    choices = list_model_names()

    if not choices:
        return gr.update()

    value = DEFAULT_MODEL if DEFAULT_MODEL in choices else choices[0]

    return gr.update(choices=choices, value=value)


def start_sharing(cards: GeneratedCards | None, request: gr.Request) -> ViewState:
    """Start sharing the generated cards."""
    if cards is not None:
        card_share.start(cards)
        LOGGER.info("Started sharing %s card(s).", len(cards.cards))
        LOGGER.debug("Shared card(s):\n%s", cards.model_dump_json(indent=2))

    return show_share_view(get_share_url(request))


def stop_sharing() -> ViewState:
    """Stop sharing the generated cards."""
    card_share.stop()

    LOGGER.info("Stopped sharing.")

    return exit_share_view()


def get_shared_cards() -> dict[str, Any] | None:
    """Return the currently-shared cards."""
    cards = card_share.get()

    if cards is None:
        return None

    LOGGER.info("Served %s card(s).", len(cards.cards))
    LOGGER.debug("Served card(s):\n%s", cards.model_dump_json(indent=2))

    return cards.model_dump()


def get_lan_ip() -> str:
    """Return this machine's LAN IP."""
    try:
        # Trick for cross-OS reliability: https://stackoverflow.com/a/166589
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            host: str = s.getsockname()[0]
            return host
    except OSError:
        return "127.0.0.1"


def get_share_url(request: gr.Request) -> str:
    """Return the URL exposing the shared cards on LAN."""
    host = get_lan_ip()
    port = request.url.port

    return f"http://{host}:{port}{CARDS_ENDPOINT}"


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
            model_dropdown = gr.Dropdown(
                label="Model",
                choices=[DEFAULT_MODEL],
                value=DEFAULT_MODEL,
                interactive=True,
            )
            generate_button = gr.Button(
                value="Generate Flashcards",
                variant="primary",
                interactive=False,
            )

        with gr.Column(visible=False) as progress_view:
            progress_status = gr.Markdown()

        with gr.Column(visible=False) as results_view:
            cards = gr.State()
            export = gr.State(delete_callback=cleanup_export)

            rendered_cards = gr.Markdown(container=True, max_height="60vh")

            with gr.Group(), gr.Row():
                format_dropdown = gr.Dropdown(
                    choices=["JSON", "CSV"],
                    value="JSON",
                    container=False,
                    interactive=True,
                )
                download_button = gr.DownloadButton(
                    variant="primary",
                    label="Download JSON",
                    value=get_filepath,
                    inputs=[format_dropdown, export],
                )

            share_button = gr.Button(value="Share", variant="primary")

            start_over_button = gr.ClearButton(
                value="Start Over",
                components=[files, progress_status, rendered_cards],
            )

        with gr.Column(visible=False) as share_view:
            share_instructions = gr.Markdown()
            stop_sharing_button = gr.Button(value="Stop Sharing")

        app.load(
            fn=update_model_choices,
            outputs=model_dropdown,
        )

        # Gradio's type stubs don't expose gr.api yet
        gr.api(get_shared_cards, api_name="cards", queue=False)  # type: ignore[attr-defined]

        files.change(
            fn=lambda files: gr.Button(interactive=bool(files)),
            inputs=files,
            outputs=generate_button,
        )

        format_dropdown.change(
            fn=lambda format_: gr.update(label=f"Download {format_}"),
            inputs=format_dropdown,
            outputs=download_button,
        )

        outputs = [
            upload_view,
            progress_view,
            results_view,
            share_view,
            progress_status,
            rendered_cards,
            cards,
            export,
            share_instructions,
        ]

        generate_button.click(
            fn=run_flow,
            inputs=[files, model_dropdown],
            outputs=outputs,
        )

        share_button.click(
            fn=start_sharing,
            inputs=cards,
            outputs=outputs,
            show_progress="hidden",
        )

        stop_sharing_button.click(
            fn=stop_sharing,
            outputs=outputs,
            show_progress="hidden",
        )

        start_over_button.click(
            fn=reset_app_state,
            inputs=export,
            outputs=outputs,
        )

    return app


demo = create_app()


def configure_logging() -> None:
    """Configure logging from the environment."""
    logging.basicConfig()
    logging_level = os.getenv("FLASHCARD_GENERATOR_LOG_LEVEL", logging.WARNING)
    logging.getLogger("flashcard_generator").setLevel(logging_level)


def main() -> None:
    """Launch the app."""
    configure_logging()
    demo.launch(css=CSS, server_name=BIND_ADDRESS)


if __name__ == "__main__":
    main()
