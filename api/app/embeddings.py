"""Signed feature hashing into a fixed vector.

This is a local embedder with no downloaded weights. The same function embeds
documents and queries, so a FAISS index built here stays usable offline.
"""

from __future__ import annotations

import hashlib

import numpy as np
from langchain_core.embeddings import Embeddings

from app.textutil import tokens


class LocalHashEmbeddings(Embeddings):
    def __init__(self, dim: int = 384) -> None:
        self.dim = dim

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    def _embed(self, text: str) -> list[float]:
        vector = np.zeros(self.dim, dtype=np.float32)
        words = tokens(text)
        if not words:
            return vector.tolist()
        features = list(words)
        features.extend(f"{left}_{right}" for left, right in zip(words, words[1:]))
        for feature in features:
            digest = hashlib.sha256(feature.encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:4], "little") % self.dim
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[bucket] += sign
        norm = float(np.linalg.norm(vector))
        if norm > 0:
            vector /= norm
        return vector.tolist()
