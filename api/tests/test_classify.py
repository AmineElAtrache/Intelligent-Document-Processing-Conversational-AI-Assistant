"""Field extraction edge cases without OCR dependencies."""
import unittest
from app.classify import classify_and_extract


class ClassificationEdgeTests(unittest.TestCase):
    def test_headings(self):
        for heading in ("INVOICE", "Receipt", "contract"):
            with self.subTest(heading=heading):
                self.assertEqual(classify_and_extract(heading)["doc_type"], heading.lower())

    def test_empty_document(self):
        fields = classify_and_extract("")
        self.assertEqual(fields["doc_type"], "unknown")
        self.assertEqual(fields["dates"], [])
        self.assertEqual(fields["amounts"], [])
        self.assertEqual(fields["names"], [])
