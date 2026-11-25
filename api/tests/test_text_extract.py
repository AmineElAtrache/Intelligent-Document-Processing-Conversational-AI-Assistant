"""Text files exported by Windows editors should lose their BOM."""
import tempfile
import unittest
from pathlib import Path
from app.extract import extract_file


class TextExtractTests(unittest.TestCase):
    def test_bom_and_null_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "invoice.txt"
            path.write_bytes(b"\xef\xbb\xbfINVOICE\x00\nTotal: 42")
            pages = extract_file(path)
            self.assertEqual(pages[0].text, "INVOICE\nTotal: 42")
            self.assertFalse(pages[0].ocr)
