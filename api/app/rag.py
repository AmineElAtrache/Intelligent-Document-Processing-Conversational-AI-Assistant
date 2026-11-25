"""Retrieve from FAISS, then answer with the local reader, Ollama, or OpenAI."""

from __future__ import annotations

import re
import threading

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate

from app.classify import AMOUNT_RE, DATE_RE, NAME_RE
from app.config import ollama_base_url, ollama_model, openai_api_key, openai_model
from app.library import Library
from app.textutil import raw_tokens, tokens

SYSTEM = (
    "You are Folio, a document desk. Answer only from the excerpts. "
    "If they do not contain the answer, say you cannot find it in the uploaded documents. "
    "Do not invent amounts, dates, or names. Name the document you used."
)

_SESSIONS: dict[str, list[dict[str, str]]] = {}
_SESSION_LOCK = threading.Lock()


class ProviderError(Exception):
    def __init__(self, status: int, detail: str) -> None:
        super().__init__(detail)
        self.status = status
        self.detail = detail


def answer(library: Library, question: str, provider: str, session_id: str) -> dict:
    question = question.strip()
    if not question:
        raise ProviderError(400, "Message is empty")
    if provider not in {"mock", "ollama", "openai"}:
        raise ProviderError(400, "Provider must be mock, ollama, or openai")
    history = _history(session_id)
    query = _retrieval_query(question, history)
    hits = library.search(query, k=4)
    citations = [_citation(doc, distance) for doc, distance in hits]
    if provider == "mock":
        text = _extractive(question, hits)
    else:
        text = _generate(provider, question, hits, history)
    _remember(session_id, question, text)
    return {
        "answer": text,
        "provider": provider,
        "retrieval_query": query,
        "citations": citations,
    }


def _history(session_id: str) -> list[dict[str, str]]:
    with _SESSION_LOCK:
        return list(_SESSIONS.get(session_id, []))


def _remember(session_id: str, question: str, reply: str) -> None:
    with _SESSION_LOCK:
        turns = _SESSIONS.setdefault(session_id, [])
        turns.append({"role": "user", "content": question})
        turns.append({"role": "assistant", "content": reply})
        del turns[:-8]


def _retrieval_query(question: str, history: list[dict[str, str]]) -> str:
    content = tokens(question)
    if len(content) > 3 or not history:
        return question
    previous = next(
        (item["content"] for item in reversed(history) if item["role"] == "user"),
        "",
    )
    if not previous:
        return question
    return f"{previous} {question}"


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [part.strip() for part in parts if part.strip()]


def _extractive(question: str, hits) -> str:
    if not hits:
        return "The index is empty, so there is nothing to quote yet."
    raw = set(raw_tokens(question))
    content = set(tokens(question))
    asks_amount = bool(raw & {"total", "amount", "price", "tax", "cost", "pay", "payment"})
    asks_date = "when" in raw or "date" in raw or ("due" in raw and not asks_amount)
    asks_who = bool(raw & {"who", "whom", "billed", "name", "prepared"})
    ranked: list[tuple[float, str, str]] = []
    for index, (doc, _distance) in enumerate(hits):
        filename_tokens = set(tokens(str(doc.metadata.get("filename", ""))))
        # A named document in the question outranks the same phrase in another file.
        doc_boost = 1.5 * len(content & filename_tokens)
        closeness = max(0.0, 0.2 - index * 0.03)
        doc_id = str(doc.metadata.get("doc_id", index))
        for sentence in _sentences(doc.page_content):
            sentence_tokens = set(tokens(sentence))
            score = float(len(content & sentence_tokens)) + doc_boost + closeness
            if asks_amount and AMOUNT_RE.search(sentence):
                score += 1.2
            if asks_date and DATE_RE.search(sentence):
                score += 1.0
            if asks_who and NAME_RE.search(sentence):
                score += 2.0
            if asks_who and "bill" in sentence_tokens:
                score += 0.6
            if score > 0:
                ranked.append((score, doc_id, sentence))
    ranked.sort(key=lambda item: item[0], reverse=True)
    if not ranked:
        return "I cannot find that in the indexed documents."
    winning_doc = ranked[0][1]
    chosen: list[str] = []
    for _score, doc_id, sentence in ranked:
        if doc_id != winning_doc or sentence in chosen:
            continue
        chosen.append(sentence)
        if len(chosen) == 2:
            break
    if not chosen:
        return (
            "I cannot find that in the indexed documents. "
            "The nearest excerpts are listed with the citations."
        )
    body = "\n".join(chosen)
    return (
        body
        + "\n\nLocal extractive answer from the indexed text. "
        "Choose Ollama or OpenAI for a composed reply."
    )


def _generate(provider: str, question: str, hits, history: list[dict[str, str]]) -> str:
    if not hits:
        return "The index is empty, so there is nothing to answer from."
    llm = _llm(provider)
    context = "\n\n".join(
        (
            f"[{index}] {doc.metadata.get('filename')} "
            f"page {doc.metadata.get('page')} chunk {doc.metadata.get('chunk')}\n"
            f"{doc.page_content}"
        )
        for index, (doc, _distance) in enumerate(hits, start=1)
    )
    prior = []
    for item in history:
        if item["role"] == "user":
            prior.append(HumanMessage(content=item["content"]))
        else:
            prior.append(AIMessage(content=item["content"]))
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM),
            ("placeholder", "{history}"),
            (
                "human",
                "Excerpts:\n{context}\n\nQuestion: {question}\n\nAnswer from the excerpts only.",
            ),
        ]
    )
    chain = prompt | llm
    try:
        message = chain.invoke(
            {"history": prior, "context": context, "question": question}
        )
    except Exception as exc:
        detail = _public_error(exc)
        if provider == "ollama":
            raise ProviderError(
                503,
                "Ollama is not reachable at "
                f"{ollama_base_url()} ({detail}). It is optional and is not part of this image. "
                "Start Ollama on the host, or switch the desk to mock.",
            ) from exc
        raise ProviderError(502, f"OpenAI request failed: {detail}") from exc
    return _message_text(getattr(message, "content", message)).strip()


def _llm(provider: str):
    if provider == "openai":
        key = openai_api_key()
        if not key:
            raise ProviderError(
                400,
                "OPENAI_API_KEY is not set on the API. The browser never sends a key. "
                "Mock mode works without one.",
            )
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=openai_model(), api_key=key, temperature=0, timeout=45, max_retries=1)
    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=ollama_model(),
            base_url=ollama_base_url(),
            temperature=0,
            timeout=45,
        )
    raise ProviderError(400, "Unknown provider")


def _message_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                parts.append(str(block.get("text", "")))
        return "\n".join(part for part in parts if part)
    return str(content)


def _public_error(exc: Exception) -> str:
    text = re.sub(r"sk-[A-Za-z0-9_\-]+", "sk-***", str(exc))
    return text[:500]


def _citation(doc, distance: float) -> dict:
    meta = doc.metadata
    excerpt = re.sub(r"\s+", " ", doc.page_content).strip()
    if len(excerpt) > 280:
        excerpt = excerpt[:277] + "..."
    return {
        "document": str(meta.get("filename", "")),
        "doc_id": str(meta.get("doc_id", "")),
        "page": int(meta.get("page", 1)),
        "chunk": int(meta.get("chunk", 0)),
        "distance": round(float(distance), 4),
        "excerpt": excerpt,
    }
