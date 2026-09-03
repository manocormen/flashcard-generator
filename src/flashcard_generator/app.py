"""Gradio UI for the flashcard generator."""

import logging
import os
import shutil
import time
from collections.abc import Generator  # noqa: TC003
from pathlib import Path
from typing import Any

import gradio as gr

from flashcard_generator.card import GeneratedCards  # noqa: TC001
from flashcard_generator.export import ExportedCards  # noqa: TC001
from flashcard_generator.generate import DEFAULT_MODEL, list_model_names
from flashcard_generator.pipeline import PipelineStep, run_pipeline
from flashcard_generator.share import CardShare, QRCode, get_lan_ip, make_qr

type ScreenUpdate = dict[gr.Component | gr.Column, Any]

# Explicit name needed because just dev runs this file as __main__
LOGGER = logging.getLogger("flashcard_generator.app")

CSS = """
#app-title {
    text-align: center;
}
"""

STEP_LABELS = {
    PipelineStep.FILES_UPLOADED: "Files uploaded",
    PipelineStep.CONTENT_EXTRACTED: "Content extracted",
    PipelineStep.TEXT_CLEANED: "Text cleaned",
    PipelineStep.PROMPT_BUILT: "Prompt built",
    PipelineStep.CARDS_GENERATED: "Cards generated",
    PipelineStep.CARDS_EXPORTED: "Downloads ready",
}

STEP_DELAY_SECONDS = 1  # To see the steps cascade in the UI

# TODO: Tighten sharing: e.g. short-lived token + temp endpoint
BIND_ADDRESS = "0.0.0.0"  # noqa: S104
CARDS_ENDPOINT = "/gradio_api/api/cards"

card_share = CardShare()


def render_progress(completed_step: PipelineStep) -> str:
    """Render pipeline progress as Markdown."""
    lines = ["### Processing...", ""]

    for step in PipelineStep:
        checkbox = "[x]" if step <= completed_step else "[ ]"
        lines.append(f"- {checkbox} {STEP_LABELS[step]}")

    return "\n".join(lines)


def render_cards(cards: GeneratedCards) -> str:
    """Return the generated cards cleanly formatted in Markdown."""
    if not cards.cards:
        return "No cards generated."

    return "\n\n---\n\n".join(
        f"### Card {index}\n\n{card.front}\n\n{card.back}"
        for index, card in enumerate(cards.cards, start=1)
    )


def show_screen(target: gr.Column) -> ScreenUpdate:
    """Show the requested screen."""
    return {screen: gr.Column(visible=screen is target) for screen in SCREENS}


def show_upload_screen() -> ScreenUpdate:
    """Show the file upload screen."""
    return show_screen(upload_screen) | {
        progress_status: "",
        cards_markdown: "",
        cards_state: None,
        export_state: None,
    }


def show_progress_screen(progress: str) -> ScreenUpdate:
    """Show the progress screen with a pipeline progress indicator."""
    return show_screen(progress_screen) | {progress_status: progress}


def show_results_screen(
    cards: GeneratedCards,
    rendered_cards: str,
    export: ExportedCards,
) -> ScreenUpdate:
    """Show the rendered cards and export options."""
    return show_screen(results_screen) | {
        progress_status: "",
        cards_markdown: rendered_cards,
        cards_state: cards,
        export_state: export,
    }


def show_share_screen(share_url: str, share_qr: QRCode) -> ScreenUpdate:
    """Show the card-sharing screen."""
    return show_screen(share_screen) | {
        share_instructions: f"Card sharing endpoint: POST `{share_url}`",
        share_qr_image: share_qr,
    }


def update_model_choices() -> gr.Dropdown:
    """Update the model dropdown to reflect the models available locally."""
    choices = list_model_names()

    if not choices:
        return gr.Dropdown()

    value = DEFAULT_MODEL if DEFAULT_MODEL in choices else choices[0]

    return gr.Dropdown(choices=choices, value=value)


def run_generation(gradio_paths: list[str], model: str) -> Generator[ScreenUpdate]:
    """Run card generation and translate pipeline events into Gradio updates."""
    # Gradio passes paths to cached upload copies, not raw user-provided paths
    paths = [Path(path) for path in gradio_paths]

    try:
        for event in run_pipeline(paths, model):
            if isinstance(event, PipelineStep):
                yield show_progress_screen(render_progress(event))
                time.sleep(STEP_DELAY_SECONDS)
                continue

            rendered_cards = render_cards(event.cards)
            yield show_results_screen(event.cards, rendered_cards, event.export)
    except Exception as e:
        LOGGER.exception("There was an unexpected error while generating cards.")
        gr.Warning(
            f"Something went wrong while processing your files.<br>"
            f"Error: {type(e).__name__}: {e}<br>"
            f"Please try again.",
        )
        yield show_upload_screen()


def get_export_path(format_: str, export: ExportedCards | None) -> Path | None:
    """Return the export path for the chosen format."""
    if export is None:
        return None

    return {"CSV": export.csv_path, "JSON": export.json_path}.get(format_)


def cleanup_export(export: ExportedCards | None) -> None:
    """Delete the exported card files."""
    if export is not None:
        shutil.rmtree(export.json_path.parent)


def reset_app_state(export: ExportedCards | None) -> ScreenUpdate:
    """Delete exported files and return to the upload screen."""
    cleanup_export(export)
    card_share.stop()

    return show_upload_screen() | {
        files_input: None,
        share_instructions: "",
        share_qr_image: None,
    }


def get_share_url(request: gr.Request) -> str:
    """Return the URL exposing the shared cards on LAN."""
    host = get_lan_ip()
    port = request.url.port

    return f"http://{host}:{port}{CARDS_ENDPOINT}"


def start_sharing(cards: GeneratedCards | None, request: gr.Request) -> ScreenUpdate:
    """Start sharing the generated cards."""
    if cards is None or not cards.cards:
        gr.Warning("No cards to share.")
        return show_screen(results_screen)

    url = get_share_url(request)
    qr = make_qr(url)

    card_share.start(cards)
    LOGGER.info("Started sharing %s card(s).", len(cards.cards))
    LOGGER.debug("Shared card(s):\n%s", cards.model_dump_json(indent=2))

    return show_share_screen(url, qr)


def stop_sharing() -> ScreenUpdate:
    """Stop sharing the generated cards."""
    card_share.stop()
    LOGGER.info("Stopped sharing.")

    return show_screen(results_screen)


def get_shared_cards() -> dict[str, Any] | None:
    """Return the currently-shared cards."""
    cards = card_share.get()

    if cards is None:
        return None

    LOGGER.info("Served %s card(s).", len(cards.cards))
    LOGGER.debug("Served card(s):\n%s", cards.model_dump_json(indent=2))

    return cards.model_dump()


with gr.Blocks(title="Flashcard Generator") as demo:
    gr.Markdown("# Flashcard Generator", elem_id="app-title")

    with gr.Column() as upload_screen:
        files_input = gr.Files(
            label="Learning materials: .txt .md .markdown .pdf",
            file_types=[".txt", ".md", ".markdown", ".pdf"],
        )
        model_dropdown = gr.Dropdown(
            label="Model",
            choices=[DEFAULT_MODEL],
            value=DEFAULT_MODEL,
        )
        generate_button = gr.Button(
            value="Generate Flashcards",
            variant="primary",
            interactive=False,
        )

    with gr.Column(visible=False) as progress_screen:
        progress_status = gr.Markdown(padding=True)

    with gr.Column(visible=False) as results_screen:
        cards_state = gr.State()
        export_state = gr.State(delete_callback=cleanup_export)

        cards_markdown = gr.Markdown(container=True, max_height="60vh")

        with gr.Group(), gr.Row():
            export_format_dropdown = gr.Dropdown(
                choices=["JSON", "CSV"],
                value="JSON",
                container=False,
            )
            download_button = gr.DownloadButton(
                variant="primary",
                label="Download JSON",
                value=get_export_path,
                inputs=[export_format_dropdown, export_state],
            )

        share_button = gr.Button(value="Share", variant="primary")
        start_over_button = gr.Button(value="Start Over")

    with gr.Column(visible=False) as share_screen:
        share_instructions = gr.Markdown()
        share_qr_image = gr.Image(show_label=False, buttons=[])
        stop_sharing_button = gr.Button(value="Stop Sharing")

    SCREENS = [
        upload_screen,
        progress_screen,
        results_screen,
        share_screen,
    ]

    GENERATION_OUTPUTS = [
        *SCREENS,
        progress_status,
        cards_markdown,
        cards_state,
        export_state,
    ]

    SHARE_OUTPUTS = [
        *SCREENS,
        share_instructions,
        share_qr_image,
    ]

    RESET_OUTPUTS = [
        files_input,
        *GENERATION_OUTPUTS,
        share_instructions,
        share_qr_image,
    ]

    demo.load(
        fn=update_model_choices,
        outputs=model_dropdown,
    )

    # Gradio's type stubs don't expose gr.api yet
    gr.api(get_shared_cards, api_name="cards", queue=False)  # type: ignore[attr-defined]

    files_input.change(
        fn=lambda files: gr.Button(interactive=bool(files)),
        inputs=files_input,
        outputs=generate_button,
    )

    generate_button.click(
        fn=run_generation,
        inputs=[files_input, model_dropdown],
        outputs=GENERATION_OUTPUTS,
    )

    export_format_dropdown.change(
        fn=lambda format_: gr.DownloadButton(label=f"Download {format_}"),
        inputs=export_format_dropdown,
        outputs=download_button,
    )

    share_button.click(
        fn=start_sharing,
        inputs=cards_state,
        outputs=SHARE_OUTPUTS,
        show_progress="hidden",
    )

    stop_sharing_button.click(
        fn=stop_sharing,
        outputs=SCREENS,
        show_progress="hidden",
    )

    start_over_button.click(
        fn=reset_app_state,
        inputs=export_state,
        outputs=RESET_OUTPUTS,
    )


def configure_logging() -> None:
    """Configure logging from the environment."""
    logging.basicConfig()
    logging_level = os.getenv("FLASHCARD_GENERATOR_LOG_LEVEL", logging.WARNING)
    logging.getLogger("flashcard_generator").setLevel(logging_level)


def main() -> None:
    """Launch the app."""
    configure_logging()
    demo.launch(css=CSS, footer_links=[], server_name=BIND_ADDRESS)


if __name__ == "__main__":
    main()
