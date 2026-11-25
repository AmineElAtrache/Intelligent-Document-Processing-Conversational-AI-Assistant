"""Tokenization checks independent of model packages."""
import unittest

from app.textutil import raw_tokens, tokens


class TokenTests(unittest.TestCase):
    def test_only_question_glue(self):
        self.assertEqual(tokens("Can you please tell me?"), [])

    def test_amount_tokens(self):
        self.assertEqual(tokens("4,280.50 MAD"), ["280", "50", "mad"])

    def test_filename_tokens(self):
        self.assertEqual(tokens("northwind-invoice_2026.txt"), ["northwind", "invoice", "2026", "txt"])

    def test_case_and_punctuation(self):
        self.assertEqual(raw_tokens("Invoice: TOTAL 42!"), ["invoice", "total", "42"])

    def test_question_glue_is_removed(self):
        self.assertEqual(tokens("What is the total due?"), ["total", "due"])

    def test_empty_input(self):
        self.assertEqual(tokens(""), [])
