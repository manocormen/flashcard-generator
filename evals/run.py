"""Evaluate generated cards."""

import json
import re
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from pprint import pprint
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
    started = datetime.now(UTC)
    output = EVALS_DIR / "runs" / started.strftime("%Y%m%dT%H%M%S.%fZ")
    output.mkdir(parents=True)

    pdf = EVALS_DIR / "data" / "sjk" / "mayan-droughts_article.pdf"
    reference_path = pdf.with_suffix(".json")
    reference_data = json.loads(reference_path.read_text(encoding="utf-8"))
    reference = Reference(**reference_data)

    print(f"Evaluating {pdf.name}...")  # noqa: T201
    for event in run_pipeline([pdf], DEFAULT_MODEL):
        if isinstance(event, PipelineResult):
            scores = score_cards(event.cards, reference)

            scores_json = json.dumps(scores, indent=2)
            (output / "results.json").write_text(scores_json, encoding="utf-8")

            shutil.move(event.export.json_path.parent, output / pdf.stem)

            pprint(scores)  # noqa: T203
            print(f"Scores saved in: {output}")  # noqa: T201


if __name__ == "__main__":
    main()
