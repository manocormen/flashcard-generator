# Flashcard Generator

Open-source Python app for generating flashcards from learning materials using open LLMs, developed as part of [GSoC 2026](https://summerofcode.withgoogle.com/programs/2026/projects/XGTDRLdf), with [AnkiDroid](https://github.com/ankidroid/anki-android) as mentoring organization.

## Features

- Takes learning materials as input: supports .txt, .PDF, and .md/.markdown.
- Uses a local Ollama model for generation: users may pick their model of choice.
- Generates basic-style flashcards: Q&A format, atomic, concise, grounded.
- Writes the generated cards to disk: exports them as JSON or CSV.
- Shares the cards with AnkiDroid via the companion Android app (coming soon).

## Setup

1. Clone the project.
2. Install [`uv`](https://docs.astral.sh/uv/getting-started/installation/).
3. Install [`ollama`](https://ollama.com/download) and run `ollama pull gemma4`.

Optional but recommended, for shorter commands, install [`just`](https://github.com/casey/just):

```bash
uv tool install rust-just
```

If you don't install it, replace `just` with `uv run just` in the commands below.

## Usage

1. Run the app with `just run` and open it in the browser.
2. Upload learning materials, pick a model, and start generation.
3. Download the cards or share them with AnkiDroid via the companion app (coming soon).

## Demo

https://github.com/user-attachments/assets/7c85cf79-20fd-40d2-a1ba-4d97af894ccb

## Constraints

For now, the app has the following constraints:

- Supports only UTF-8-encoded text and Markdown files.
- Supports only PDFs with highlightable text, not scanned PDFs.
- Requires the companion Android app for pushing cards to AnkiDroid. 
- Generated flashcards in Q&A format only, i.e. [basic notes](https://docs.ankiweb.net/getting-started.html#note-types).

## Development

The `justfile` contains useful development commands. Here's a selection:

```bash
just                # Show all commands
just format         # Format the code
just lint           # Lint the code
just typecheck      # Typecheck the code
just test           # Run all tests
just fix            # Run all mutable QA: auto-fix issues
just check          # Run all non-mutable QA: signal issues
```

## Pipeline

The app is structured as a pipeline with the following components:

<img width="4414" height="410" alt="flashcard-generator-pipeline" src="https://github.com/user-attachments/assets/144344fc-7987-4588-87e3-f3cbfa633d1d" />

## Structure

The project is broken down into the following modules, which roughly correspond to each step in our pipeline.

```bash
.
├── LICENSE
├── README.md
├── justfile
├── pyproject.toml
├── src
│   └── flashcard_generator
│       ├── app.py          # UI and app flow
│       ├── card.py         # Pydantic card models
│       ├── clean.py        # Document cleaning
│       ├── export.py       # Card exporting
│       ├── extract.py      # Document extracting
│       ├── generate.py     # Card generation
│       ├── pipeline.py     # Pipeline orchestration
│       ├── prompt.py       # Prompt definitions
│       └── share.py        # Card sharing
├── tests
│   └── ...
└── uv.lock
```

## License

This software is distributed with an AGPL licence. Refer to LICENSE for more details.
