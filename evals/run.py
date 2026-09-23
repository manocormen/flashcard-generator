"""Evaluate generated cards."""

from dataclasses import dataclass

from rouge_score import rouge_scorer, tokenizers  # type: ignore[import-untyped]

from flashcard_generator.card import BasicCard, GeneratedCards

ROUGE = rouge_scorer.RougeScorer(["rouge1"], use_stemmer=True)
WORD_TOKENIZER = tokenizers.DefaultTokenizer()


@dataclass(kw_only=True)
class Reference:
    """Reference text for evaluating generated cards."""

    abstract: str
    glossary_terms: list[str]


def score_cards(cards: GeneratedCards, reference: Reference) -> dict[str, float]:
    """Measure abstract word recall and deck size."""
    card_text = "\n".join(f"{card.front}\n{card.back}" for card in cards.cards)
    rouge1 = ROUGE.score(reference.abstract, card_text)["rouge1"]

    return {
        "rouge1_recall": rouge1.recall,
        "card_count": len(cards.cards),
        "word_count": len(WORD_TOKENIZER.tokenize(card_text)),
    }


def main() -> None:
    """Run the evaluations."""
    # TODO: Remove toy example, once I wired the actual eval PDFs.
    reference = Reference(
        abstract="Frogs hatch from eggs. Tadpoles grow legs and become adult frogs.",
        glossary_terms=["Eggs", "Tadpoles", "Adult frogs"],
    )

    cards = GeneratedCards(
        cards=[
            BasicCard(front="What hatches from eggs?", back="Tadpoles."),
            BasicCard(front="What do tadpoles grow?", back="Legs."),
        ],
    )

    scores = score_cards(cards, reference)
    print(scores)  # noqa: T201


if __name__ == "__main__":
    main()
