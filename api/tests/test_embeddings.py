"""Embedding shape and empty input invariants."""
import unittest
from app.embeddings import LocalHashEmbeddings


class EmbeddingTests(unittest.TestCase):
    def test_invalid_dimensions(self):
        for value in (0, -1, True, 1.5):
            with self.subTest(value=value), self.assertRaises(ValueError):
                LocalHashEmbeddings(value)

    def test_empty_query_has_zero_vector(self):
        self.assertEqual(LocalHashEmbeddings(8).embed_query(""), [0.0] * 8)

    def test_query_matches_document_embedding(self):
        embedder = LocalHashEmbeddings(16)
        self.assertEqual(embedder.embed_query("invoice total"), embedder.embed_documents(["invoice total"])[0])
