"""Gradio upload UI for the flashcard generator."""

import logging
import os
import shutil
import socket
import time
from collections.abc import Generator  # noqa: TC003
from enum import Enum, auto
from pathlib import Path
from typing import Any

import gradio as gr
import qrcode  # type: ignore[import-untyped]
from PIL import Image

from flashcard_generator.card import GeneratedCards
from flashcard_generator.export import ExportedCards
from flashcard_generator.generate import DEFAULT_MODEL, list_model_names
from flashcard_generator.pipeline import PipelineProgress, run_pipeline
from flashcard_generator.share import CardShare

type QrCode = Image.Image

# TODO: Once stabilized, update to types with named slots, for readability
type ScreenUpdate = tuple[
    gr.Column,
    gr.Column,
    gr.Column,
    gr.Column,
]

type GenerationUpdate = tuple[
    *ScreenUpdate,
    str,  # progress
    str,  # rendered cards
    GeneratedCards | None,
    ExportedCards | None,
]

type ShareUpdate = tuple[
    *ScreenUpdate,
    str,
    QrCode,
]

type ResetUpdate = tuple[
    *GenerationUpdate,
    str,  # share instructions
    QrCode | None,
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

# TODO: Tighten sharing: e.g. short-lived token + temp endpoint
BIND_ADDRESS = "0.0.0.0"  # noqa: S104
CARDS_ENDPOINT = "/gradio_api/api/cards"


class Screen(Enum):
    """App screens."""

    UPLOAD = auto()
    PROGRESS = auto()
    RESULTS = auto()
    SHARE = auto()


def render_progress(steps_completed: int) -> str:
    """Render pipeline progress as Markdown."""
    lines = ["### Processing...", ""]

    for index, stage in enumerate(STEPS):
        checkbox = "[x]" if index < steps_completed else "[ ]"

        lines.append(f"- {checkbox} {stage}")

    return "\n".join(lines)


def show_screen(screen: Screen) -> ScreenUpdate:
    """Show the requested screen."""
    return (
        gr.Column(visible=screen is Screen.UPLOAD),
        gr.Column(visible=screen is Screen.PROGRESS),
        gr.Column(visible=screen is Screen.RESULTS),
        gr.Column(visible=screen is Screen.SHARE),
    )


def show_upload_screen() -> GenerationUpdate:
    """Show the file upload screen."""
    return (
        *show_screen(Screen.UPLOAD),
        "",
        "",
        None,
        None,
    )


def show_progress_screen(progress: str) -> GenerationUpdate:
    """Show the progress screen with a pipeline progress indicator."""
    return (
        *show_screen(Screen.PROGRESS),
        progress,
        gr.skip(),
        gr.skip(),
        gr.skip(),
    )


def show_results_screen(
    generated_cards: GeneratedCards | None,
    rendered_cards: str | None,
    export: ExportedCards,
) -> GenerationUpdate:
    """Show the rendered cards and export options."""
    return (
        *show_screen(Screen.RESULTS),
        "",
        rendered_cards if rendered_cards is not None else "No cards generated.",
        generated_cards,
        export,
    )


def show_share_screen(share_url: str, share_qr: QrCode) -> ShareUpdate:
    """Show the card-sharing screen."""
    return (
        *show_screen(Screen.SHARE),
        f"Card sharing endpoint: POST `{share_url}`",
        share_qr,
    )


def run_flow(gradio_paths: list[str], model: str) -> Generator[GenerationUpdate]:
    """Run the pipeline and translate its events into Gradio updates."""
    # Gradio passes paths to cached upload copies, not raw user-provided paths
    filepaths = [Path(gp) for gp in gradio_paths]

    try:
        for event in run_pipeline(filepaths, model):
            if isinstance(event, PipelineProgress):
                yield show_progress_screen(render_progress(event.steps_completed))
                time.sleep(STEPS_DELAY_SECONDS)
                continue

            rendered_cards = render_cards(event.cards)
            yield show_results_screen(event.cards, rendered_cards, event.export)

    except Exception as e:
        LOGGER.exception("There was an unexpected error while running the Gradio flow.")
        gr.Warning(
            f"Something went wrong while processing your files.<br>"
            f"Error: {type(e).__name__}: {e}<br>"
            f"Please try again.",
        )
        yield show_upload_screen()


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


def reset_app_state(export: ExportedCards | None) -> ResetUpdate:
    """Delete exported files and return to the upload screen."""
    cleanup_export(export)
    card_share.stop()

    return (*show_upload_screen(), "", None)


def update_model_choices() -> GradioUpdate:
    """Update the model dropdown to reflect the models available locally."""
    choices = list_model_names()

    if not choices:
        return gr.update()

    value = DEFAULT_MODEL if DEFAULT_MODEL in choices else choices[0]

    return gr.update(choices=choices, value=value)


def start_sharing(cards: GeneratedCards | None, request: gr.Request) -> ShareUpdate:
    """Start sharing the generated cards."""
    if cards is None or not cards.cards:
        gr.Warning("No cards to share.")
        return (
            *show_screen(Screen.RESULTS),
            gr.skip(),
            gr.skip(),
        )

    card_share.start(cards)
    LOGGER.info("Started sharing %s card(s).", len(cards.cards))
    LOGGER.debug("Shared card(s):\n%s", cards.model_dump_json(indent=2))

    url = get_share_url(request)
    qr = make_qr(url)

    return show_share_screen(url, qr)


def stop_sharing() -> ScreenUpdate:
    """Stop sharing the generated cards."""
    card_share.stop()

    LOGGER.info("Stopped sharing.")

    return show_screen(Screen.RESULTS)


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


def make_qr(url: str) -> QrCode:
    """Return a QR code that encodes the input URL."""
    qr_code: QrCode = qrcode.make(url).get_image()

    return qr_code


def create_app() -> gr.Blocks:
    """Return an app instance."""
    app = gr.Blocks(title="Flashcard Generator")
    with app:
        gr.Markdown("# Flashcard Generator", elem_id="app-title")

        with gr.Column(visible=True) as upload_screen:
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

        with gr.Column(visible=False) as progress_screen:
            progress_status = gr.Markdown()

        with gr.Column(visible=False) as results_screen:
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

        with gr.Column(visible=False) as share_screen:
            share_instructions = gr.Markdown()
            share_qr = gr.Image(show_label=False, buttons=[])
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

        screen_outputs = [
            upload_screen,
            progress_screen,
            results_screen,
            share_screen,
        ]

        generation_outputs = [
            *screen_outputs,
            progress_status,
            rendered_cards,
            cards,
            export,
        ]

        share_outputs = [
            *screen_outputs,
            share_instructions,
            share_qr,
        ]

        reset_outputs = [
            *generation_outputs,
            share_instructions,
            share_qr,
        ]

        generate_button.click(
            fn=run_flow,
            inputs=[files, model_dropdown],
            outputs=generation_outputs,
        )

        share_button.click(
            fn=start_sharing,
            inputs=cards,
            outputs=share_outputs,
            show_progress="hidden",
        )

        stop_sharing_button.click(
            fn=stop_sharing,
            outputs=screen_outputs,
            show_progress="hidden",
        )

        start_over_button.click(
            fn=reset_app_state,
            inputs=export,
            outputs=reset_outputs,
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
