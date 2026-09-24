"""Evaluate generated cards."""

from dataclasses import dataclass
from pprint import pprint

from rouge_score import rouge_scorer, tokenizers  # type: ignore[import-untyped]

from flashcard_generator.card import BasicCard, GeneratedCards

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


def _includes(fields: list[str], term: str) -> bool:
    """Check if given term shows in at least one field."""
    # Term may comprise slash-separated coterms. All should be present.
    coterms = [_normalize(coterm) for coterm in term.split("/")]

    return all(any(coterm in f for f in fields) for coterm in coterms)


def main() -> None:
    """Run the evaluations."""
    # TODO: Remove toy example, once I wired the actual eval PDFs.
    reference = Reference(
        abstract="Frogs hatch from eggs. Tadpoles grow legs and become adult frogs.",
        glossary_terms=["Eggs/Tadpoles", "Adult frogs"],
    )

    cards = GeneratedCards(
        cards=[
            BasicCard(front="What hatches from eggs?", back="Tadpoles."),
            BasicCard(front="What do tadpoles grow?", back="Legs."),
        ],
    )

    scores = score_cards(cards, reference)
    pprint(scores)  # noqa: T203


if __name__ == "__main__":
    main()
