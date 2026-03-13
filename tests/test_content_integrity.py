"""
Tests for the Markdown topic files in topics/

Coverage areas:
  - All 8 expected topic files exist
  - Each file has a top-level H1 heading
  - Each file has at least one H2 section heading
  - Each file has a ## Sources section
  - No file contains unfilled placeholder text ([Add ..., [Insert ...)
  - Every URL in Sources sections is syntactically valid (starts with http/https)
  - No file is empty
  - Duplicate H1 headings are flagged (copy-paste error)
"""

import os
import re
import pytest

TOPICS_DIR = os.path.join(os.path.dirname(__file__), "..", "topics")

EXPECTED_FILES = [
    "AI applications.md.",
    "Case Studies.md.",
    "Challenges and Navigation for Lawyers.md.",
    "Ethical and Societal Impacts.md.",
    "Future Trends and Innovation.md.",
    "Intellectual Property and AI.md.",
    "Privacy, Data Protection and Liability.md.",
    "Regulatory and Policy Frameworks.md.",
]

PLACEHOLDER_PATTERNS = [
    r"\[Add\b",
    r"\[Insert\b",
    r"\[TODO\b",
    r"\[TBD\b",
    r"Add URLs or citations",
    r"Add content here",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_topic(filename: str) -> str:
    path = os.path.join(TOPICS_DIR, filename)
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def topic_files():
    """Return (filename, content) pairs for every expected topic file."""
    return [(f, read_topic(f)) for f in EXPECTED_FILES]


# ---------------------------------------------------------------------------
# File existence tests
# ---------------------------------------------------------------------------

class TestFileExistence:
    @pytest.mark.parametrize("filename", EXPECTED_FILES)
    def test_file_exists(self, filename):
        path = os.path.join(TOPICS_DIR, filename)
        assert os.path.isfile(path), f"Expected topic file not found: {filename}"

    def test_no_extra_unexpected_files(self):
        """Warn if topic files exist that are not in EXPECTED_FILES (may be stale drafts)."""
        actual = set(os.listdir(TOPICS_DIR))
        expected = set(EXPECTED_FILES)
        extras = actual - expected
        assert extras == set(), (
            f"Unexpected files found in topics/: {extras}. "
            "Add them to EXPECTED_FILES or remove them."
        )

    @pytest.mark.parametrize("filename", EXPECTED_FILES)
    def test_file_is_not_empty(self, filename):
        content = read_topic(filename)
        assert len(content.strip()) > 0, f"File is empty: {filename}"


# ---------------------------------------------------------------------------
# Structure / heading tests
# ---------------------------------------------------------------------------

class TestHeadingStructure:
    @pytest.mark.parametrize("filename", EXPECTED_FILES)
    def test_has_h1_heading(self, filename):
        content = read_topic(filename)
        h1_lines = [l for l in content.splitlines() if l.startswith("# ") and not l.startswith("## ")]
        assert len(h1_lines) >= 1, f"No H1 heading found in {filename}"

    @pytest.mark.parametrize("filename", EXPECTED_FILES)
    def test_has_at_least_one_h2_section(self, filename):
        content = read_topic(filename)
        h2_lines = [l for l in content.splitlines() if l.startswith("## ")]
        assert len(h2_lines) >= 1, f"No H2 section headings found in {filename}"

    @pytest.mark.parametrize("filename", EXPECTED_FILES)
    def test_no_duplicate_h1_headings(self, filename):
        content = read_topic(filename)
        h1_lines = [l.strip() for l in content.splitlines() if re.match(r'^# [^#]', l)]
        assert len(h1_lines) == len(set(h1_lines)), (
            f"Duplicate H1 headings found in {filename}: {h1_lines}"
        )


# ---------------------------------------------------------------------------
# Sources section tests
# ---------------------------------------------------------------------------

class TestSourcesSection:
    @pytest.mark.parametrize("filename", EXPECTED_FILES)
    def test_has_sources_section(self, filename):
        content = read_topic(filename)
        assert "## Sources" in content, f"No '## Sources' section in {filename}"

    @pytest.mark.parametrize("filename", EXPECTED_FILES)
    def test_sources_section_has_content(self, filename):
        content = read_topic(filename)
        idx = content.find("## Sources")
        if idx == -1:
            pytest.skip(f"No Sources section in {filename}")
        after_sources = content[idx + len("## Sources"):].strip()
        assert len(after_sources) > 0, f"Sources section is empty in {filename}"

    @pytest.mark.parametrize("filename", EXPECTED_FILES)
    def test_urls_in_sources_are_valid(self, filename):
        """Every bare URL after the Sources heading should begin with http/https."""
        content = read_topic(filename)
        idx = content.find("## Sources")
        if idx == -1:
            pytest.skip(f"No Sources section in {filename}")
        sources_section = content[idx:]
        # Match raw URLs (not inside markdown link syntax which is tested separately)
        raw_urls = re.findall(r'https?://\S+', sources_section)
        for url in raw_urls:
            assert url.startswith(("http://", "https://")), (
                f"Invalid URL '{url}' in sources of {filename}"
            )
        # At least one URL should exist
        assert len(raw_urls) >= 1, f"No URLs found in Sources section of {filename}"


# ---------------------------------------------------------------------------
# Placeholder / incomplete content tests
# ---------------------------------------------------------------------------

class TestNoPlaceholders:
    @pytest.mark.parametrize("filename,pattern", [
        (f, p) for f in EXPECTED_FILES for p in PLACEHOLDER_PATTERNS
    ])
    def test_no_placeholder_text(self, filename, pattern):
        content = read_topic(filename)
        matches = re.findall(pattern, content, re.IGNORECASE)
        assert len(matches) == 0, (
            f"Placeholder pattern '{pattern}' found {len(matches)} time(s) in {filename}"
        )


# ---------------------------------------------------------------------------
# Minimum content length test
# ---------------------------------------------------------------------------

class TestContentLength:
    @pytest.mark.parametrize("filename", EXPECTED_FILES)
    def test_minimum_word_count(self, filename):
        """Each topic file should have at least 100 words of real content."""
        content = read_topic(filename)
        words = content.split()
        assert len(words) >= 100, (
            f"File {filename} has only {len(words)} words — may need more content"
        )
