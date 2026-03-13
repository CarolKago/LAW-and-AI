"""
Tests for scripts/Legal_text_summariser.py

Coverage areas:
  - Happy-path summarisation
  - Edge cases: empty input, single sentence, num_sentences > available sentences
  - Output type and length guarantees
  - Stop-word filtering
  - Sentence-scoring correctness
"""

import sys
import os
import pytest

# Allow importing the script without executing its module-level side effects
# (the nltk.download calls and the example print at the bottom).
import unittest.mock as mock

# Patch nltk.download before importing so the tests don't hit the network.
with mock.patch("nltk.download"):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
    # We need to reload if already cached
    if "Legal_text_summariser" in sys.modules:
        del sys.modules["Legal_text_summariser"]
    # Suppress the module-level print by redirecting stdout during import
    import io
    with mock.patch("sys.stdout", new_callable=io.StringIO):
        from Legal_text_summariser import summarize_text


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

LEGAL_TEXT_MULTI = (
    "The contract is governed by the laws of England and Wales. "
    "Either party may terminate this agreement with thirty days written notice. "
    "All disputes shall be resolved through binding arbitration. "
    "Confidential information must not be disclosed to third parties. "
    "The licensee agrees to pay royalties on a quarterly basis."
)

LEGAL_TEXT_SHORT = "This agreement is binding. Both parties must comply."


# ---------------------------------------------------------------------------
# Return-type and structure tests
# ---------------------------------------------------------------------------

class TestReturnType:
    def test_returns_string(self):
        result = summarize_text(LEGAL_TEXT_MULTI)
        assert isinstance(result, str)

    def test_returns_non_empty_for_valid_input(self):
        result = summarize_text(LEGAL_TEXT_MULTI)
        assert len(result.strip()) > 0

    def test_default_num_sentences_is_three(self):
        """Default num_sentences=3 should return at most 3 sentences."""
        result = summarize_text(LEGAL_TEXT_MULTI)
        # A rough proxy: count sentence-ending punctuation
        sentence_count = result.count(".") + result.count("!") + result.count("?")
        assert sentence_count <= 3


# ---------------------------------------------------------------------------
# num_sentences parameter tests
# ---------------------------------------------------------------------------

class TestNumSentences:
    def test_num_sentences_one(self):
        result = summarize_text(LEGAL_TEXT_MULTI, num_sentences=1)
        # Should be a single sentence (one terminal punctuation mark)
        sentence_count = result.count(".") + result.count("!") + result.count("?")
        assert sentence_count == 1

    def test_num_sentences_two(self):
        result = summarize_text(LEGAL_TEXT_MULTI, num_sentences=2)
        sentence_count = result.count(".") + result.count("!") + result.count("?")
        assert sentence_count <= 2

    def test_num_sentences_exceeds_available(self):
        """When num_sentences > total sentences, return all available sentences."""
        result = summarize_text(LEGAL_TEXT_SHORT, num_sentences=10)
        assert isinstance(result, str)
        assert len(result.strip()) > 0

    def test_num_sentences_equals_total(self):
        """Requesting exactly as many sentences as available should work."""
        result = summarize_text(LEGAL_TEXT_SHORT, num_sentences=2)
        assert isinstance(result, str)
        assert len(result.strip()) > 0


# ---------------------------------------------------------------------------
# Edge-case input tests
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_single_sentence_input(self):
        single = "Artificial intelligence shall not replace human judgement in court."
        result = summarize_text(single, num_sentences=1)
        assert isinstance(result, str)
        assert len(result.strip()) > 0

    def test_single_sentence_num_sentences_greater_than_one(self):
        single = "Artificial intelligence shall not replace human judgement in court."
        result = summarize_text(single, num_sentences=5)
        assert isinstance(result, str)

    def test_repeated_sentences(self):
        """Repeated sentences still produce a valid summary."""
        repeated = "All parties must sign. All parties must sign. All parties must sign."
        result = summarize_text(repeated, num_sentences=2)
        assert isinstance(result, str)

    def test_text_with_numbers_and_punctuation(self):
        text = (
            "Section 4.2 requires payment within 30 days. "
            "Clause 7(b) restricts sub-licensing. "
            "Appendix A lists the permitted jurisdictions."
        )
        result = summarize_text(text, num_sentences=2)
        assert isinstance(result, str)
        assert len(result.strip()) > 0

    def test_text_with_uppercase(self):
        text = (
            "THE LICENSOR GRANTS NO WARRANTIES. "
            "LIABILITY IS LIMITED TO DIRECT DAMAGES. "
            "CONSEQUENTIAL DAMAGES ARE EXCLUDED."
        )
        result = summarize_text(text, num_sentences=2)
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Stop-word filtering tests
# ---------------------------------------------------------------------------

class TestStopWordFiltering:
    def test_stop_words_do_not_dominate_scoring(self):
        """
        A sentence rich in content words should score higher than one
        composed mostly of stop words.
        """
        # 'the', 'is', 'a', 'of', 'and' are common English stop words.
        # The algorithm should not rank a sentence of stop words above
        # one with meaningful content.
        content_heavy = (
            "Artificial intelligence algorithms predict litigation outcomes "
            "with statistically significant accuracy. "
            "The case is a matter of law. "
            "It is the duty of the court."
        )
        result = summarize_text(content_heavy, num_sentences=1)
        # The content-heavy sentence should be included
        assert "Artificial intelligence" in result or "algorithms" in result or "accuracy" in result

    def test_output_contains_words_from_input(self):
        result = summarize_text(LEGAL_TEXT_MULTI, num_sentences=2)
        # The output must be derived from the input sentences
        input_words = set(LEGAL_TEXT_MULTI.lower().split())
        output_words = set(result.lower().split())
        assert len(input_words & output_words) > 0


# ---------------------------------------------------------------------------
# Sentence-scoring / ranking tests
# ---------------------------------------------------------------------------

class TestSentenceScoring:
    def test_high_frequency_terms_elevate_sentence(self):
        """
        A sentence that repeats a key term (relative to the corpus)
        should be ranked in the summary.
        """
        text = (
            "Liability is central to contract law. "
            "Liability arises when a party breaches its obligations. "
            "Weather is unpredictable this time of year. "
            "Liability clauses protect both parties in a dispute."
        )
        # 'liability' appears 3 times; sentences containing it should rank higher.
        result = summarize_text(text, num_sentences=2)
        assert "liability" in result.lower() or "Liability" in result

    def test_summary_is_subset_of_original_sentences(self):
        """Every sentence in the summary must be drawn verbatim from the source."""
        original_sentences = [s.strip() for s in LEGAL_TEXT_MULTI.split(".") if s.strip()]
        result = summarize_text(LEGAL_TEXT_MULTI, num_sentences=3)
        # Each summary sentence should match at least one original sentence fragment
        for part in result.split(". "):
            part = part.strip()
            if part:
                assert any(part in orig or orig in part for orig in original_sentences), (
                    f"Summary sentence '{part}' not found in original text"
                )
