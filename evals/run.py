"""Evaluate generated cards."""

import argparse
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from pprint import pprint
from time import perf_counter
from typing import TYPE_CHECKING

from rouge_score import rouge_scorer, tokenizers  # type: ignore[import-untyped]

from flashcard_generator.generate import DEFAULT_MODEL
from flashcard_generator.pipeline import PipelineResult, run_pipeline

if TYPE_CHECKING:
    from flashcard_generator.card import GeneratedCards

EVALS_DIR = Path("evals")

ROUGE = rouge_scorer.RougeScorer(["rouge1"], use_stemmer=True)
WORD_TOKENIZER = tokenizers.DefaultTokenizer()
WORD_TOKENIZER_STEMMER = tokenizers.DefaultTokenizer(use_stemmer=True)


@dataclass(kw_only=True)
class Reference:
    """Reference text for evaluating generated cards."""

    abstract: str
    glossary_terms: list[str]


def score_cards(cards: GeneratedCards, reference: Reference) -> dict[str, object]:
    """Measure abstract and glossary recall, and deck size."""
    abstract, glossary = reference.abstract, reference.glossary_terms

    card_text = "\n".join(f"{card.front}\n{card.back}" for card in cards.cards)
    rouge1 = ROUGE.score(abstract, card_text)["rouge1"]

    fields = [_normalize(f) for c in cards.cards for f in (c.front, c.back)]
    matches = [term for term in glossary if _includes(fields, term)]

    return {
        "abstract_recall": rouge1.recall,
        "glossary_recall": len(matches) / len(glossary),
        "card_count": len(cards.cards),
        "word_count": len(WORD_TOKENIZER.tokenize(card_text)),
        "matched_terms": matches,
        "missing_terms": [t for t in glossary if t not in matches],
    }


def _normalize(text: str) -> str:
    """Lowercase, remove punctuation, and stem and pad words, for matching."""
    return " " + " ".join(WORD_TOKENIZER_STEMMER.tokenize(text)) + " "


def _includes(fields: list[str], entry: str) -> bool:
    """Check if the given glossary entry shows in at least one field."""
    pattern = r"(.+?)\s+\(([A-Z][A-Z0-9]*)\)"  # words + acronym: e.g. Common Era (CE)

    # Entries may comprise slash-separated coterms. All must be present.
    for coterm in map(str.strip, entry.split("/")):
        # Coterms may comprise acronym alternatives. Either must be present.
        match_ = re.fullmatch(pattern, coterm)
        alts = match_.groups() if match_ else (coterm,)
        norm = [_normalize(alt) for alt in alts]

        if not any(alt in f for alt in norm for f in fields):
            return False

    return True


def main() -> None:
    """Run the evaluations."""
    parser = argparse.ArgumentParser(description="Evaluate generated cards.")
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Ollama model to use.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=EVALS_DIR / "data" / "sjk",
        help="Directory with article PDFs and their JSON references.",
    )
    args = parser.parse_args()

    started = datetime.now(UTC)
    timer = perf_counter()

    git_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],  # noqa: S607
        stdout=subprocess.PIPE,
        text=True,
        check=True,
    ).stdout.strip()
    git_status = subprocess.run(
        [  # noqa: S607
            "git",
            "status",
            "--porcelain",
            "--",  # Only monitor paths that may impact generation and thereby evals
            "src",
            "evals",
            "pyproject.toml",
            "uv.lock",
        ],
        stdout=subprocess.PIPE,
        text=True,
        check=True,
    ).stdout

    output = EVALS_DIR / "runs" / started.strftime("%Y%m%dT%H%M%S.%fZ")
    output.mkdir(parents=True)

    all_scores: dict[str, dict[str, object]] = {}

    for pdf in sorted(args.data_dir.glob("*.pdf")):
        reference_path = pdf.with_suffix(".json")
        reference_data = json.loads(reference_path.read_text(encoding="utf-8"))
        reference = Reference(**reference_data)

        print(f"Evaluating {pdf.name}...")  # noqa: T201
        for event in run_pipeline([pdf], args.model):
            if isinstance(event, PipelineResult):
                all_scores[pdf.stem] = score_cards(event.cards, reference)
                shutil.move(event.export.json_path.parent, output / pdf.stem)

    scores_json = json.dumps(all_scores, indent=2)
    (output / "results.json").write_text(scores_json, encoding="utf-8")

    metadata = {
        "started_at": started.isoformat(),
        "duration_seconds": perf_counter() - timer,
        "model": args.model,
        "data_dir": str(args.data_dir),
        "git_commit": git_commit,
        "git_dirty": bool(git_status),
    }
    metadata_json = json.dumps(metadata, indent=2)
    (output / "metadata.json").write_text(metadata_json, encoding="utf-8")

    pprint(all_scores)  # noqa: T203
    print(f"Scores saved in: {output}")  # noqa: T201


if __name__ == "__main__":
    main()
