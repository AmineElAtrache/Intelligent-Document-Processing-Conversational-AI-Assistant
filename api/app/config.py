"""Paths and environment. API keys are read from the environment only."""

from __future__ import annotations

import os
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SAMPLES_DIR = PACKAGE_ROOT / "samples"
MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_PAGES = 30


def data_dir() -> Path:
    raw = os.environ.get("DATA_DIR", "").strip()
    return Path(raw) if raw else PACKAGE_ROOT / "data"


def openai_api_key() -> str:
    return os.environ.get("OPENAI_API_KEY", "").strip()


def openai_model() -> str:
    return os.environ.get("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"


def ollama_base_url() -> str:
    return os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").strip().rstrip("/")


def ollama_model() -> str:
    return os.environ.get("OLLAMA_MODEL", "llama3.2").strip() or "llama3.2"


def default_provider() -> str:
    value = os.environ.get("LLM_PROVIDER", "mock").strip().lower()
    if value in {"mock", "ollama", "openai"}:
        return value
    return "mock"
