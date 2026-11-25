"""Keyword document type and lightweight field extraction.

LayoutLM is not used. Type is the keyword list with the most hits, when at
least two of its phrases appear. A line that is only "invoice", "receipt", or
"contract" is enough on its own. Dates, amounts, and names come from patterns
and labels.
"""

from __future__ import annotations

import re

# A one-word title is a type even when the rest of a short page has no second hit.
HEADINGS = {"invoice": "invoice", "receipt": "receipt", "contract": "contract"}

TYPE_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "invoice",
        ("invoice number", "invoice", "bill to", "total due", "amount due", "subtotal"),
    ),
    (
        "receipt",
        ("receipt", "cashier", "change due", "purchased", "tendered"),
    ),
    (
        "contract",
        ("agreement", "whereas", "hereinafter", "parties agree", "governing law"),
    ),
    (
        "letter",
        ("dear ", "sincerely", "yours faithfully", "kind regards"),
    ),
    (
        "resume",
        ("curriculum vitae", "work experience", "professional summary", "education"),
    ),
)

MONTHS = (
    "january|february|march|april|may|june|july|august|"
    "september|october|november|december"
)
DATE_RE = re.compile(
    rf"\b(?:\d{{1,2}}\s+(?:{MONTHS})\s+\d{{4}}|\d{{4}}-\d{{2}}-\d{{2}}|\d{{1,2}}[/-]\d{{1,2}}[/-]\d{{2,4}})\b",
    re.IGNORECASE,
)
AMOUNT_RE = re.compile(
    r"(?:[$€£]\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d{1,3}(?:,\d{3})*(?:\.\d{2})\s?(?:MAD|USD|EUR|GBP|DH))",
    re.IGNORECASE,
)
NAME_RE = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}\b")
LABEL_RE = re.compile(
    r"^(?:bill to|prepared by|prepared for|from|dear|name)\s*[:\-]?\s*(.+)$",
    re.IGNORECASE,
)
CLOSING_RE = re.compile(r"^(sincerely|yours faithfully|kind regards|regards)\b", re.IGNORECASE)


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        cleaned = re.sub(r"\s+", " ", value).strip(" \t,.;")
        if not cleaned or cleaned.casefold() in seen:
            continue
        seen.add(cleaned.casefold())
        ordered.append(cleaned)
    return ordered


def _names(text: str) -> list[str]:
    found: list[str] = []
    lines = text.splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        label = LABEL_RE.match(stripped)
        if label:
            candidate = NAME_RE.search(label.group(1))
            if candidate:
                found.append(candidate.group(0))
            continue
        if CLOSING_RE.match(stripped.strip(",")):
            for follow in lines[index + 1 : index + 3]:
                candidate = NAME_RE.fullmatch(follow.strip().strip(","))
                if candidate:
                    found.append(candidate.group(0))
                    break
    return _unique(found)


def _heading(text: str) -> str | None:
    lines = {
        re.sub(r"[^a-z]", "", line.casefold())
        for line in text.splitlines()
        if line.strip()
    }
    hits = [label for label, word in HEADINGS.items() if word in lines]
    if len(hits) == 1:
        return hits[0]
    return None


def classify_and_extract(text: str) -> dict:
    folded = text.casefold()
    scores = {
        label: sum(1 for phrase in phrases if phrase in folded)
        for label, phrases in TYPE_RULES
    }
    best_label, best_score = max(scores.items(), key=lambda item: item[1])
    heading = _heading(text)
    doc_type = best_label if best_score >= 2 else heading or "unknown"
    return {
        "doc_type": doc_type,
        "type_score": int(scores.get(doc_type, 0) if doc_type != "unknown" else best_score),
        "dates": _unique(DATE_RE.findall(text)),
        "amounts": _unique(match.group(0) for match in AMOUNT_RE.finditer(text)),
        "names": _names(text),
    }
