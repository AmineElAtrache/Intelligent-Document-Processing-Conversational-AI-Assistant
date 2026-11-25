"""HTTP checks: health, sample retrieval, upload, and a missing OpenAI key."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

SAMPLES = Path(__file__).resolve().parents[1] / "samples"


class HttpTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["DATA_DIR"] = self.tmp.name
        os.environ["OPENAI_API_KEY"] = ""
        os.environ["LLM_PROVIDER"] = "mock"
        os.environ["OLLAMA_BASE_URL"] = "http://127.0.0.1:9"
        import app.main as main

        main._LIBRARY = None
        self.main = main

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_health_retrieval_and_upload(self) -> None:
        from fastapi.testclient import TestClient

        with TestClient(self.main.app) as client:
            health = client.get("/api/health")
            self.assertEqual(health.status_code, 200)
            body = health.json()
            self.assertEqual(body["status"], "ok")
            self.assertGreaterEqual(body["documents"], 2)
            self.assertGreaterEqual(body["chunks"], 2)
            self.assertEqual(body["embeddings"], "local-hash")
            self.assertFalse(body["layoutlm"])
            self.assertFalse(body["ollama_bundled"])
            self.assertFalse(body["openai_configured"])

            chat = client.post(
                "/api/chat",
                json={
                    "message": "What is the total due on the Northwind Studio invoice?",
                    "provider": "mock",
                    "session_id": "http",
                },
            )
            self.assertEqual(chat.status_code, 200, chat.text)
            payload = chat.json()
            self.assertIn("4,280.50", payload["answer"])
            self.assertIn("northwind-invoice", payload["citations"][0]["document"])

            refused = client.post(
                "/api/chat",
                json={
                    "message": "What is the total due?",
                    "provider": "openai",
                    "session_id": "http",
                },
            )
            self.assertEqual(refused.status_code, 400)
            self.assertNotIn("sk-", refused.json()["detail"])

            leaked = client.post(
                "/api/chat",
                json={
                    "message": "What is the total due?",
                    "provider": "mock",
                    "session_id": "http",
                    "api_key": "sk-not-allowed",
                },
            )
            self.assertEqual(leaked.status_code, 422)

            with (SAMPLES / "northwind-invoice.pdf").open("rb") as handle:
                uploaded = client.post(
                    "/api/documents",
                    files={"file": ("northwind-invoice.pdf", handle, "application/pdf")},
                )
            self.assertEqual(uploaded.status_code, 200, uploaded.text)
            record = uploaded.json()
            self.assertEqual(record["doc_type"], "invoice")
            self.assertFalse(record["ocr_used"])
            self.assertIn("4,280.50 MAD", record["fields"]["amounts"])

            with (SAMPLES / "northwind-invoice.docx").open("rb") as handle:
                docx = client.post(
                    "/api/documents",
                    files={
                        "file": (
                            "northwind-invoice.docx",
                            handle,
                            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        )
                    },
                )
            self.assertEqual(docx.status_code, 200, docx.text)
            self.assertEqual(docx.json()["doc_type"], "invoice")
            self.assertIn("Sara El Fassi", docx.json()["fields"]["names"])
