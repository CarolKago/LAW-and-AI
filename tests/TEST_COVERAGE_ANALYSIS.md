# Test Coverage Analysis — LAW-and-AI

## 1. Current State (Baseline)

| Asset | Type | Lines | Tests before this PR |
|---|---|---|---|
| `scripts/Legal_text_summariser.py` | Python utility | 30 | **0** |
| `docs/index.html` | Static HTML | 265 | **0** |
| `topics/*.md.` (8 files) | Markdown content | ~400 | **0** |

**Overall coverage: 0% — no test infrastructure existed.**

---

## 2. What Was Added

Three new test modules under `tests/`:

| Test file | Scope | Test count |
|---|---|---|
| `test_legal_text_summariser.py` | Python `summarize_text()` function | 17 |
| `test_html_structure.py` | `docs/index.html` structure & accessibility | 17 |
| `test_content_integrity.py` | All 8 Markdown topic files | ~48 (parametrized) |

Run with: `pytest tests/ -v`

---

## 3. Coverage by Area

### 3.1 `scripts/Legal_text_summariser.py`

**What is now tested:**

| Test class | Scenarios covered |
|---|---|
| `TestReturnType` | Returns `str`; non-empty output; default of 3 sentences |
| `TestNumSentences` | `num_sentences=1`, `=2`; exceeds available; equals available |
| `TestEdgeCases` | Single sentence; single sentence + large `num_sentences`; repeated sentences; numbers & punctuation; uppercase |
| `TestStopWordFiltering` | Stop words don't dominate scoring; output words are subset of input |
| `TestSentenceScoring` | High-frequency terms elevate a sentence; summary sentences come verbatim from source |

**Gaps / further improvements needed:**

| Gap | Priority | Suggested test |
|---|---|---|
| `empty string` input — `sent_tokenize("")` returns `[]`; `nlargest` on an empty dict currently returns `[]` and `' '.join([])` → `""`. This silently returns an empty string with no error. | **High** | `test_empty_string_returns_empty_or_raises` |
| `num_sentences=0` — `nlargest(0, ...)` returns `[]`, silently producing `""`. Callers may not expect this. | **High** | `test_zero_num_sentences` |
| Unicode / non-ASCII text (e.g. French legal text with accented characters) | Medium | `test_unicode_input` |
| Very large input (10,000 word contract) — performance regression guard | Medium | `test_large_input_completes_in_reasonable_time` |
| Punctuation-only or whitespace-only input | Medium | `test_whitespace_only_input` |
| `num_sentences` as a float or string — type safety | Low | `test_invalid_num_sentences_type` |
| Missing NLTK data — currently `nltk.download` is called at module level; if the download fails silently the function will crash with a LookupError | Low | Mock `nltk.data.find` to raise and assert LookupError propagates cleanly |

---

### 3.2 `docs/index.html`

**What is now tested:**

| Test class | Scenarios covered |
|---|---|
| `TestHtmlStructure` | DOCTYPE, `<html>`, `<head>`, `<body>`, `<header>`, `<nav>` present; correct `<title>`; charset & viewport meta |
| `TestNavigation` | All 8 `href="#..."` links; all 8 `id="..."` anchors; exactly 8 internal links |
| `TestAccessibility` | `lang="en"` on `<html>`; all images have non-empty alt text; 8 images present |
| `TestContentCompleteness` | No placeholder text in `ai-applications` and `challenges` sections; flags all sections with placeholders |
| `TestDetailsSections` | 8 `<details>` elements; each has `<summary>`; each has `<p>` |

**Gaps / further improvements needed:**

| Gap | Priority | Suggested test |
|---|---|---|
| **Broken internal links** — the nav links (`#ai-applications`, etc.) must correspond to actual element IDs. Currently partly tested, but not end-to-end with a real browser | **High** | Use `playwright` or `selenium` to click each nav link and assert the correct section is visible |
| **JavaScript behaviour** — the `hashchange` event handler that opens/closes `<details>` is untested | **High** | Add a `pytest-playwright` or Jest/JSDOM test that verifies the correct `<details>` is opened after a hash change |
| **Image src paths resolve** — tests confirm `src` is non-empty but don't verify `images/image-N.png` files actually exist on disk | High | `test_all_image_files_exist_on_disk` (straightforward `os.path.isfile` check) |
| **Responsive layout** — the `@media (max-width: 768px)` breakpoint is untested | Medium | Playwright viewport resize test asserting `.topic-column` stacks vertically at ≤768 px |
| **Spelling / typos in visible text** — current HTML has "Lawyrers", "doesnt", "intergrating", "transaprency", "Regualtions" | Medium | Integrate `pyspellchecker` or `codespell` into CI to catch typos automatically |
| **Valid HTML (W3C)** — no validator runs against the document | Medium | Use the `html5-parser` or `tidy` library to assert zero errors / warnings |
| **Contrast / WCAG AA** — white text on black nav is fine, but black text on white is not verified programmatically | Low | Axe-core accessibility scan via Playwright |

---

### 3.3 `topics/*.md.` (Content files)

**What is now tested:**

| Test class | Scenarios covered |
|---|---|
| `TestFileExistence` | All 8 expected files present; no unexpected extra files; none empty |
| `TestHeadingStructure` | Each file has ≥1 H1; ≥1 H2; no duplicate H1 headings |
| `TestSourcesSection` | `## Sources` section exists; has content; all URLs start with `http/https` |
| `TestNoPlaceholders` | 6 placeholder patterns checked across all 8 files (parametrized) |
| `TestContentLength` | Minimum 100-word count per file |

**Gaps / further improvements needed:**

| Gap | Priority | Suggested test |
|---|---|---|
| **Placeholder content is widespread** — 6 of 8 files still contain `[Add ...]` blocks (confirmed by grep). These are flagged by `test_no_placeholder_text` and expected to fail until content is added. | **High** | Fix the content gaps, then the tests pass automatically |
| **Dead / unreachable URLs in sources** — URLs are syntactically valid but not checked for HTTP 200 | High | Add a `test_sources_urls_return_200` that makes HEAD requests (use `responses` mock in unit tests; real HTTP in integration tests) |
| **Markdown link syntax** — `[text](url)` links are not parsed and validated separately from raw URLs | Medium | Extract and validate all `[...]( )` markdown links |
| **File naming convention** — files use a non-standard `.md.` extension (note trailing dot); this may cause rendering issues on some platforms | Medium | `test_file_extension_is_standard` (assert ends with `.md`) |
| **Cross-reference consistency** — content referenced in HTML (`docs/index.html`) should match the corresponding topic file | Medium | For each `<details>` section, assert that key terms from the matching `.md.` file appear in the HTML |
| **Minimum source count** — some files may have only one citation | Low | Assert ≥ 2 sources per file |

---

## 4. Infrastructure Gaps

Beyond individual test gaps, the project needs foundational testing infrastructure:

| Item | Recommendation |
|---|---|
| **No `requirements.txt` or `pyproject.toml`** | Add `requirements-dev.txt` with `pytest`, `pytest-cov`, `nltk` |
| **No CI pipeline** | Add a GitHub Actions workflow (`.github/workflows/test.yml`) that runs `pytest` on every push/PR |
| **No coverage reporting** | Add `pytest-cov` and enforce a minimum coverage threshold (start at 70%) |
| **No linting** | Add `flake8` or `ruff` to catch issues like the module-level `print` in the script |
| **NLTK data download in tests** | Tests currently mock `nltk.download`; a CI environment needs `punkt` and `stopwords` pre-downloaded (add a `conftest.py` fixture or download step in CI) |

---

## 5. Recommended Priority Order

1. **Fix `empty string` and `num_sentences=0` edge cases** in `Legal_text_summariser.py` — these are silent bugs
2. **Add GitHub Actions CI** — makes all tests run automatically
3. **Add `test_all_image_files_exist_on_disk`** — catches broken image paths before deployment
4. **Add JS behaviour tests** (Playwright) — the accordion open/close logic is a user-visible feature with zero test coverage
5. **Fix placeholder content** in 6 topic files — currently 6 of 8 files have unfilled sections
6. **Add URL liveness checks** for sources — ensures citations remain reachable
7. **Add spelling/typo check** — several typos exist in rendered HTML
