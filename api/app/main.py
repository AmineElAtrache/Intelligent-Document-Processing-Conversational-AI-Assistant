"""HTTP desk: upload, fields, and chat with citations."""

from __future__ import annotations

import logging
import urllib.request
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app import __version__
from app.config import (
    MAX_UPLOAD_BYTES,
    default_provider,
    ollama_base_url,
    openai_api_key,
)
from app.library import Library, seed_samples
from app.rag import ProviderError, answer

logger = logging.getLogger("folio")

_LIBRARY: Library | None = None

ALLOWED_SUFFIXES = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
    ".bmp",
    ".webp",
    ".docx",
    ".txt",
}


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=4000)
    provider: str = Field(default="mock", pattern="^(mock|ollama|openai)$")
    session_id: str = Field(default="default", pattern=r"^[A-Za-z0-9_-]{1,80}$")

    @field_validator("message")
    @classmethod
    def nonblank_message(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Message must contain non-whitespace text")
        return value.strip()


def get_library() -> Library:
    if _LIBRARY is None:
        raise HTTPException(status_code=503, detail="Library is not ready")
    return _LIBRARY


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _LIBRARY
    logging.basicConfig(level=logging.INFO)
    library = Library()
    library.load()
    added = seed_samples(library)
    if added:
        logger.info("Seeded %s sample documents into FAISS", added)
    _LIBRARY = library
    try:
        yield
    finally:
        _LIBRARY = None


app = FastAPI(title="Folio", version=__version__, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict:
    return {
        "service": "folio-api",
        "health": "/api/health",
        "docs": "/docs",
        "ui": "http://127.0.0.1:8080",
    }


@app.get("/api/health")
def health() -> dict:
    library = get_library()
    return {
        "status": "ok",
        "service": "folio-api",
        "version": __version__,
        "documents": len(library.catalog),
        "chunks": library.chunk_count(),
        "embeddings": "local-hash",
        "classifier": "keyword-rules",
        "layoutlm": False,
        "ocr": "paddleocr",
        "ollama_bundled": False,
        "openai_configured": bool(openai_api_key()),
        "default_provider": default_provider(),
    }


@app.get("/api/providers")
def providers() -> dict:
    return {
        "default": default_provider(),
        "mock": {
            "available": True,
            "detail": "Quotes the indexed text on this machine. No key and no GPU.",
        },
        "openai": {
            "available": bool(openai_api_key()),
            "detail": "Uses OPENAI_API_KEY from the API environment. The browser does not send a key.",
        },
        "ollama": {
            "available": _ollama_up(),
            "detail": (
                f"Optional server at {ollama_base_url()}. "
                "Ollama is not running inside this image."
            ),
        },
    }


@app.get("/api/documents")
def list_documents() -> list[dict]:
    return get_library().catalog


@app.get("/api/documents/{doc_id}")
def get_document(doc_id: str) -> dict:
    for record in get_library().catalog:
        if record["id"] == doc_id:
            return record
    raise HTTPException(status_code=404, detail="Document not found")


@app.post("/api/documents")
async def upload_document(file: UploadFile = File(...)) -> dict:
    filename = Path((file.filename or "").replace("\\", "/")).name
    if not filename or filename.startswith("."):
        raise HTTPException(status_code=400, detail="Upload needs a filename")
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file. Use PDF, PNG, JPEG, TIFF, BMP, WEBP, DOCX, or TXT.",
        )
    payload = await file.read(MAX_UPLOAD_BYTES + 1)
    if not payload:
        raise HTTPException(status_code=400, detail="That file is empty")
    if len(payload) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File is larger than 20 MB")
    library = get_library()
    temporary = library.uploads / f".incoming-{uuid_name()}{suffix}"
    temporary.write_bytes(payload)
    try:
        return library.ingest_path(temporary, filename=filename, source="upload")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("upload failed")
        raise HTTPException(status_code=400, detail="Could not read that file") from exc
    finally:
        temporary.unlink(missing_ok=True)


@app.post("/api/chat")
def chat(body: ChatRequest) -> dict:
    try:
        return answer(get_library(), body.message, body.provider, body.session_id)
    except ProviderError as exc:
        raise HTTPException(status_code=exc.status, detail=exc.detail) from exc


def uuid_name() -> str:
    from uuid import uuid4

    return uuid4().hex


def _ollama_up() -> bool:
    try:
        with urllib.request.urlopen(ollama_base_url() + "/api/tags", timeout=0.8) as response:
            return response.status == 200
    except Exception:
        return False
