"""Offline checks for classification and sample-document retrieval."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from app.classify import classify_and_extract
from app.library import Library, seed_samples
from app.rag import ProviderError, answer

SAMPLES = Path(__file__).resolve().parents[1] / "samples"


class ClassifyTests(unittest.TestCase):
    def test_invoice_fields(self) -> None:
        text = (SAMPLES / "northwind-invoice.txt").read_text(encoding="utf-8")
        fields = classify_and_extract(text)
        self.assertEqual(fields["doc_type"], "invoice")
        self.assertIn("4,280.50 MAD", fields["amounts"])
        self.assertIn("12 March 2026", fields["dates"])
        self.assertIn("11 April 2026", fields["dates"])
        self.assertIn("Amal Benyoussef", fields["names"])
        self.assertIn("Sara El Fassi", fields["names"])

    def test_receipt_heading(self) -> None:
        text = (
            "RECEIPT\nCafe Atlas\nDate: 2 January 2026\n"
            "Name: Amal Benyoussef\nTotal due: 86.00 MAD\n"
        )
        fields = classify_and_extract(text)
        self.assertEqual(fields["doc_type"], "receipt")
        self.assertIn("2 January 2026", fields["dates"])
        self.assertIn("86.00 MAD", fields["amounts"])
        self.assertIn("Amal Benyoussef", fields["names"])

    def test_letter_fields(self) -> None:
        text = (SAMPLES / "reading-room-letter.txt").read_text(encoding="utf-8")
        fields = classify_and_extract(text)
        self.assertEqual(fields["doc_type"], "letter")
        self.assertIn("14 February 2026", fields["dates"])
        self.assertIn("Amal Benyoussef", fields["names"])
        self.assertIn("Youssef Amrani", fields["names"])
        self.assertEqual(fields["amounts"], [])


class RetrievalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.library = Library(Path(self.tmp.name))
        added = seed_samples(self.library, SAMPLES)
        self.assertEqual(added, 2)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_total_due_cites_invoice(self) -> None:
        result = answer(
            self.library,
            "What is the total due on the Northwind Studio invoice?",
            "mock",
            "total-due",
        )
        self.assertIn("4,280.50", result["answer"])
        self.assertTrue(result["citations"])
        self.assertIn("northwind-invoice", result["citations"][0]["document"])
        self.assertEqual(result["citations"][0]["page"], 1)
        self.assertIn("chunk", result["citations"][0])

    def test_follow_up_due_date(self) -> None:
        answer(
            self.library,
            "What is the total due on the Northwind Studio invoice?",
            "mock",
            "follow-up",
        )
        result = answer(self.library, "When is it due?", "mock", "follow-up")
        self.assertIn("11 April 2026", result["answer"])

    def test_amount_stays_on_the_named_document(self) -> None:
        receipt = Path(self.tmp.name) / "cafe-atlas-receipt.txt"
        receipt.write_text(
            "RECEIPT\nCafe Atlas\nDate: 2 January 2026\n"
            "Name: Amal Benyoussef\nTotal due: 86.00 MAD\n",
            encoding="utf-8",
        )
        self.library.ingest_path(receipt, receipt.name, "upload")
        invoice = answer(
            self.library,
            "What is the total due on the Northwind Studio invoice?",
            "mock",
            "named-invoice",
        )
        cafe = answer(
            self.library,
            "What is the total due at Cafe Atlas?",
            "mock",
            "named-cafe",
        )
        self.assertIn("4,280.50", invoice["answer"])
        self.assertNotIn("86.00", invoice["answer"])
        self.assertIn("northwind-invoice", invoice["citations"][0]["document"])
        self.assertIn("86.00", cafe["answer"])
        self.assertNotIn("4,280.50", cafe["answer"])
        self.assertIn("cafe-atlas-receipt", cafe["citations"][0]["document"])

    def test_billed_to(self) -> None:
        result = answer(
            self.library,
            "Who is the invoice billed to?",
            "mock",
            "who-billed",
        )
        self.assertIn("Amal Benyoussef", result["answer"])

    def test_openai_without_key_is_refused(self) -> None:
        previous = os.environ.pop("OPENAI_API_KEY", None)
        try:
            with self.assertRaises(ProviderError) as caught:
                answer(self.library, "What is the total due?", "openai", "no-key")
            self.assertEqual(caught.exception.status, 400)
            self.assertNotIn("sk-", caught.exception.detail)
        finally:
            if previous is not None:
                os.environ["OPENAI_API_KEY"] = previous


if __name__ == "__main__":
    unittest.main()
