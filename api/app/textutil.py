"""Token helpers shared by the local embedder and the extractive reader."""

from __future__ import annotations

import re

TOKEN_RE = re.compile(r"[a-z0-9]+")

# Question glue and function words. Content words such as "total" and "due" stay.
STOP = frozenset(
    {
        "a",
        "an",
        "the",
        "is",
        "are",
        "was",
        "were",
        "what",
        "which",
        "who",
        "whom",
        "whose",
        "when",
        "where",
        "why",
        "how",
        "of",
        "for",
        "to",
        "and",
        "or",
        "on",
        "in",
        "at",
        "by",
        "from",
        "with",
        "about",
        "this",
        "that",
        "it",
        "its",
        "be",
        "do",
        "does",
        "did",
        "please",
        "tell",
        "me",
        "show",
        "can",
        "you",
        "your",
        "my",
        "we",
        "our",
        "there",
        "here",
        "as",
        "if",
        "than",
        "then",
        "into",
        "over",
        "under",
        "up",
        "down",
        "not",
        "no",
        "yes",
        "just",
        "also",
    }
)


def raw_tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def tokens(text: str) -> list[str]:
    return [token for token in raw_tokens(text) if token not in STOP and len(token) > 1]
