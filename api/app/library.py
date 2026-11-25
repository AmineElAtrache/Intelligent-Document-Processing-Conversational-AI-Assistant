"""Catalog plus a FAISS index over locally hashed chunks."""

from __future__ import annotations

import json
import shutil
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.classify import classify_and_extract
from app.config import SAMPLES_DIR, data_dir
from app.embeddings import LocalHashEmbeddings
from app.extract import Page, extract_file


def utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class Library:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or data_dir()
        self.uploads = self.root / "uploads"
        self.pages_dir = self.root / "pages"
        self.index_dir = self.root / "faiss"
        self.catalog_path = self.root / "catalog.json"
        self.uploads.mkdir(parents=True, exist_ok=True)
        self.pages_dir.mkdir(parents=True, exist_ok=True)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.embeddings = LocalHashEmbeddings()
        self.catalog: list[dict] = []
        self.store: FAISS | None = None
        self._lock = threading.Lock()

    def load(self) -> None:
        if self.catalog_path.exists():
            self.catalog = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        index_file = self.index_dir / "index.faiss"
        if index_file.exists():
            self.store = FAISS.load_local(
                str(self.index_dir),
                self.embeddings,
                allow_dangerous_deserialization=True,
            )
        elif self.catalog:
            self.rebuild()

    def chunk_count(self) -> int:
        if self.store is None:
            return 0
        return int(self.store.index.ntotal)

    def ingest_path(
        self,
        path: Path,
        filename: str,
        source: str,
        doc_id: str | None = None,
    ) -> dict:
        pages = extract_file(path)
        if not any(page.text.strip() for page in pages):
            raise ValueError("No text could be read from this file")
        full_text = "\n".join(page.text for page in pages)
        fields = classify_and_extract(full_text)
        doc_id = doc_id or uuid.uuid4().hex
        documents = _chunks(doc_id, filename, pages)
        if not documents:
            raise ValueError("No text could be read from this file")
        record = {
            "id": doc_id,
            "filename": filename,
            "doc_type": fields["doc_type"],
            "type_score": fields["type_score"],
            "pages": len(pages),
            "chunks": len(documents),
            "ocr_used": any(page.ocr for page in pages),
            "created_at": utcnow(),
            "source": source,
            "fields": fields,
            "preview": full_text.strip()[:1200],
        }
        destination = self.uploads / f"{doc_id}{path.suffix.lower()}"
        if path.resolve() != destination.resolve():
            shutil.copyfile(path, destination)
        (self.pages_dir / f"{doc_id}.json").write_text(
            json.dumps(
                [
                    {"number": page.number, "text": page.text, "ocr": page.ocr}
                    for page in pages
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        with self._lock:
            if self.store is None:
                self.store = FAISS.from_documents(documents, self.embeddings)
            else:
                self.store.add_documents(documents)
            self.catalog.append(record)
            self._persist()
        return record

    def search(self, query: str, k: int = 4) -> list[tuple[Document, float]]:
        if k <= 0:
            raise ValueError("Retrieval count must be positive")
        with self._lock:
            if self.store is None:
                return []
            hits = self.store.similarity_search_with_score(query, k=k)
        return [(doc, float(score)) for doc, score in hits]

    def rebuild(self) -> None:
        documents: list[Document] = []
        for record in self.catalog:
            page_path = self.pages_dir / f"{record['id']}.json"
            if not page_path.exists():
                continue
            raw_pages = json.loads(page_path.read_text(encoding="utf-8"))
            pages = [
                Page(int(item["number"]), item["text"], bool(item["ocr"]))
                for item in raw_pages
            ]
            documents.extend(_chunks(record["id"], record["filename"], pages))
        if not documents:
            self.store = None
            return
        self.store = FAISS.from_documents(documents, self.embeddings)
        self._persist()

    def _persist(self) -> None:
        self.catalog_path.write_text(
            json.dumps(self.catalog, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        if self.store is not None:
            self.store.save_local(str(self.index_dir))


def _chunks(doc_id: str, filename: str, pages: list[Page]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=80)
    documents: list[Document] = []
    chunk_index = 0
    for page in pages:
        text = page.text.strip()
        if not text:
            continue
        pieces = splitter.split_text(text) or [text]
        for piece in pieces:
            documents.append(
                Document(
                    page_content=piece,
                    metadata={
                        "doc_id": doc_id,
                        "filename": filename,
                        "page": int(page.number),
                        "chunk": int(chunk_index),
                        "ocr": bool(page.ocr),
                    },
                )
            )
            chunk_index += 1
    return documents


def seed_samples(library: Library, samples_dir: Path | None = None) -> int:
    if library.catalog:
        return 0
    folder = samples_dir or SAMPLES_DIR
    added = 0
    for path in sorted(folder.glob("*.txt")):
        library.ingest_path(
            path,
            filename=path.name,
            source="seed",
            doc_id=f"seed-{path.stem}",
        )
        added += 1
    return added
