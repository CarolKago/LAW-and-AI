"""
Tests for docs/index.html

Coverage areas:
  - Required structural elements (DOCTYPE, html, head, body, header, nav)
  - All 8 navigation links are present and anchor-IDs exist in the page
  - Every <img> has a non-empty alt attribute (basic accessibility)
  - No placeholder "[Add content" strings remain in the rendered page
  - Required meta tags (charset, viewport) are present
  - Each <details> section contains a <summary> and at least one <p>
  - Page title is set correctly
"""

import os
import pytest
from html.parser import HTMLParser

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

HTML_PATH = os.path.join(
    os.path.dirname(__file__), "..", "docs", "index.html"
)


def load_html() -> str:
    with open(HTML_PATH, encoding="utf-8") as fh:
        return fh.read()


class SimpleHTMLInspector(HTMLParser):
    """Minimal parser that collects tags, ids, and attribute data."""

    def __init__(self):
        super().__init__()
        self.tags_seen: list[str] = []
        self.ids: set[str] = set()
        self.hrefs: list[str] = []
        self.images: list[dict] = []           # {'src': ..., 'alt': ...}
        self.meta_attrs: list[dict] = []
        self.title_text: str = ""
        self._in_title = False
        self._title_parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        self.tags_seen.append(tag)
        attr_dict = dict(attrs)

        if "id" in attr_dict:
            self.ids.add(attr_dict["id"])

        if tag == "a" and "href" in attr_dict:
            self.hrefs.append(attr_dict["href"])

        if tag == "img":
            self.images.append({"src": attr_dict.get("src", ""), "alt": attr_dict.get("alt", "")})

        if tag == "meta":
            self.meta_attrs.append(attr_dict)

        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
            self.title_text = "".join(self._title_parts).strip()

    def handle_data(self, data):
        if self._in_title:
            self._title_parts.append(data)


@pytest.fixture(scope="module")
def html_content():
    return load_html()


@pytest.fixture(scope="module")
def inspector(html_content):
    p = SimpleHTMLInspector()
    p.feed(html_content)
    return p


# ---------------------------------------------------------------------------
# Structural tests
# ---------------------------------------------------------------------------

class TestHtmlStructure:
    def test_doctype_present(self, html_content):
        assert html_content.strip().lower().startswith("<!doctype html")

    def test_html_tag_present(self, inspector):
        assert "html" in inspector.tags_seen

    def test_head_tag_present(self, inspector):
        assert "head" in inspector.tags_seen

    def test_body_tag_present(self, inspector):
        assert "body" in inspector.tags_seen

    def test_header_tag_present(self, inspector):
        assert "header" in inspector.tags_seen

    def test_nav_tag_present(self, inspector):
        assert "nav" in inspector.tags_seen

    def test_page_title(self, inspector):
        assert inspector.title_text == "LAW and AI"

    def test_charset_meta(self, inspector):
        charsets = [m.get("charset", "").lower() for m in inspector.meta_attrs]
        assert "utf-8" in charsets

    def test_viewport_meta(self, inspector):
        viewports = [m for m in inspector.meta_attrs if m.get("name", "").lower() == "viewport"]
        assert len(viewports) >= 1
        assert "width=device-width" in viewports[0].get("content", "")


# ---------------------------------------------------------------------------
# Navigation tests
# ---------------------------------------------------------------------------

EXPECTED_NAV_ANCHORS = [
    "#ai-applications",
    "#challenges",
    "#case-studies",
    "#regulatory",
    "#ip-ai",
    "#privacy",
    "#ethical",
    "#future",
]

EXPECTED_SECTION_IDS = [a.lstrip("#") for a in EXPECTED_NAV_ANCHORS]


class TestNavigation:
    def test_all_nav_links_present(self, inspector):
        for anchor in EXPECTED_NAV_ANCHORS:
            assert anchor in inspector.hrefs, f"Nav link '{anchor}' not found in <a href=...> tags"

    def test_all_section_ids_exist(self, inspector):
        for section_id in EXPECTED_SECTION_IDS:
            assert section_id in inspector.ids, (
                f"Section id='{section_id}' not found in the HTML"
            )

    def test_nav_link_count(self, inspector):
        """There should be exactly 8 internal navigation links."""
        internal_links = [h for h in inspector.hrefs if h.startswith("#")]
        assert len(internal_links) == 8


# ---------------------------------------------------------------------------
# Accessibility tests
# ---------------------------------------------------------------------------

class TestAccessibility:
    def test_lang_attribute_on_html(self, html_content):
        assert 'lang="en"' in html_content or "lang='en'" in html_content

    def test_all_images_have_alt_text(self, inspector):
        for img in inspector.images:
            assert img["alt"].strip() != "", (
                f"Image '{img['src']}' is missing alt text"
            )

    def test_all_images_have_nonempty_src(self, inspector):
        for img in inspector.images:
            assert img["src"].strip() != "", "An <img> tag has an empty src attribute"

    def test_eight_images_present(self, inspector):
        assert len(inspector.images) == 8, (
            f"Expected 8 images, found {len(inspector.images)}"
        )


# ---------------------------------------------------------------------------
# Content completeness tests
# ---------------------------------------------------------------------------

PLACEHOLDER_PATTERNS = [
    "[Add content",
    "Fill in with",
    "Manually fill",
]


class TestContentCompleteness:
    def test_no_placeholder_text_in_ai_applications(self, html_content):
        """The AI Applications section should not contain placeholder text."""
        for pattern in PLACEHOLDER_PATTERNS:
            # Find the section between id="ai-applications" and the next <details>
            start = html_content.find('id="ai-applications"')
            end = html_content.find('<details', start + 1)
            section = html_content[start:end]
            assert pattern not in section, (
                f"Placeholder '{pattern}' found in ai-applications section"
            )

    def test_no_placeholder_text_in_challenges(self, html_content):
        start = html_content.find('id="challenges"')
        end = html_content.find('<details', start + 1)
        section = html_content[start:end]
        for pattern in PLACEHOLDER_PATTERNS:
            assert pattern not in section, (
                f"Placeholder '{pattern}' found in challenges section"
            )

    def test_placeholder_sections_identified(self, html_content):
        """
        Document which sections still contain placeholder text.
        This test explicitly flags incomplete sections so they are visible
        in the test report. It is expected to fail until the content is added.
        """
        incomplete = []
        for section_id in EXPECTED_SECTION_IDS:
            start = html_content.find(f'id="{section_id}"')
            end_pos = html_content.find('<details', start + 1)
            if end_pos == -1:
                end_pos = html_content.find('</div>', start + 1)
            section = html_content[start:end_pos]
            for pattern in PLACEHOLDER_PATTERNS:
                if pattern in section:
                    incomplete.append(section_id)
                    break

        assert incomplete == [], (
            f"The following sections still contain placeholder content: {incomplete}"
        )


# ---------------------------------------------------------------------------
# Details/Summary structure tests
# ---------------------------------------------------------------------------

class TestDetailsSections:
    def test_eight_details_sections(self, html_content):
        count = html_content.count("<details")
        assert count == 8, f"Expected 8 <details> sections, found {count}"

    def test_each_details_has_summary(self, html_content):
        """Every <details> should be immediately followed (within it) by a <summary>."""
        import re
        # Find each details block
        details_blocks = re.findall(r'<details[^>]*>(.*?)</details>', html_content, re.DOTALL)
        for i, block in enumerate(details_blocks):
            assert "<summary>" in block, f"<details> block #{i+1} is missing a <summary>"

    def test_each_section_has_paragraph(self, html_content):
        import re
        details_blocks = re.findall(r'<details[^>]*>(.*?)</details>', html_content, re.DOTALL)
        for i, block in enumerate(details_blocks):
            assert "<p>" in block, f"<details> block #{i+1} has no <p> element"
