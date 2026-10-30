# Flashcard Generator

Open-source Python app for generating flashcards from learning materials using open LLMs, developed as part of [GSoC 2026](https://summerofcode.withgoogle.com/programs/2026/projects/XGTDRLdf), with [AnkiDroid](https://github.com/ankidroid/anki-android) as mentoring organization.

## Features

- Takes learning materials as input: supports `.txt`, `.pdf`, and `.md`/`.markdown`.
- Uses a local Ollama model for generation: users may pick their model of choice.
- Supports topic-based generation: selects relevant input passages using [RAG](https://en.wikipedia.org/wiki/Retrieval-augmented_generation).
- Accounts for images: extracts figures from PDFs and makes cards based on them.
- Generates basic-style flashcards: Q&A format, atomic, concise, and grounded.
- Writes the generated cards to disk: exports them as JSON or CSV.
- Shares the cards with AnkiDroid via the companion [Flashcard Importer](https://github.com/manocormen/flashcard-importer) app.

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
2. Upload learning materials, specify a topic (optional), pick a model, and start generation.
3. Download the cards directly or share them with AnkiDroid via the companion [Flashcard Importer](https://github.com/manocormen/flashcard-importer) app.

## Demo

https://github.com/user-attachments/assets/8f33ac35-f200-4daf-bee3-26074ee2735f

## Constraints

For now, the app has the following constraints:

- Supports only UTF-8-encoded text and Markdown files.
- Supports only PDFs with highlightable text, not scanned PDFs.
- PDFs with images require a vision-capable model, such as `gemma4`.
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
just eval           # Run all evals
just fix            # Run all mutable QA: auto-fix issues
just check          # Run all non-mutable QA: signal issues
```

## Flow

The app is structured as a flow with the following components:

<img width="4467" height="1830" alt="flashcard-generator-flow" src="https://github.com/user-attachments/assets/71e108bf-76fd-4b42-9589-8cd9ce57e378" />

## Structure

The project is broken down into the following modules, which roughly correspond to a component in our flow.

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
│       ├── chunk.py        # Document chunking
│       ├── clean.py        # Document cleaning
│       ├── embed.py        # Document embedding
│       ├── export.py       # Card exporting
│       ├── extract.py      # Document extracting
│       ├── generate.py     # Card generation
│       ├── pipeline.py     # Pipeline orchestration
│       ├── prompt.py       # Prompt definitions
│       ├── retrieve.py     # Passage retrieval
│       └── share.py        # Card sharing
├── tests
│   └── ...
└── uv.lock
```

## License

This software is distributed with an AGPL licence. Refer to LICENSE for more details.
