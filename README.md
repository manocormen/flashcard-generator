# Flashcard Generator

⚠️ 🚧 🛠️ Project Under Construction: Not Functional Yet 🛠️ 🚧 ⚠️

Open-source Python app for generating flashcards from learning materials using open LLMs, developed as part of [GSoC 2026](https://summerofcode.withgoogle.com/programs/2026/projects/XGTDRLdf), with [AnkiDroid](https://github.com/ankidroid/anki-android) as mentoring organization.

## Setup

1. Clone the project.
2. Install [`uv`](https://docs.astral.sh/uv/getting-started/installation/).

Optional but recommended, for shorter commands, install [`just`](https://github.com/casey/just):

```bash
uv tool install rust-just
```

If you don't install it, replace `just` with `uv run just` in the commands below.

## Usage

```bash
just run            # Run the app
```

## Development

The `justfile` contains useful development commands. Here's a selection:

```bash
just                # Show all commands
just format         # Format the code
just lint           # Lint the code
just typecheck      # Typecheck the code
just test           # Run all tests
```