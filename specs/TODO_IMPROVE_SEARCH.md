# TODO: Improve Search for Structured Identifiers (UC Numbers etc.)

**Project:** ServeMD  
**Status:** Proposed  
**Created:** 2026-04-14  
**Motivation:** Searching for `UC-2-002` or `UC2-002` returns no relevant hits even though
the identifier appears verbatim in h3 headings throughout the docs.

---

## Problem Statement

When users search for a structured identifier like `UC-2-002` they expect to land directly
on the section that describes that use case. Currently they get zero useful results.

The same class of identifiers appears in many structured documentation sets:
- Use case IDs: `UC-2-002`, `UC3-067`, `UC-DEV-05`
- Gap IDs: `G-02`, `G-14`
- Route IDs: `AUTH-01`, `UC3-01`
- Screen IDs: `AUTH_01`, `UC4_01`

These are **the primary keys** users type when they know exactly what they are looking for.
A search engine that cannot resolve them is effectively broken for this use case.

---

## Root Cause Analysis

Three independent bugs interact to produce the failure. They are ordered by impact.

### Bug 1 — h3+ headings are silently dropped from the `headings` field (HIGH)

**Location:** `src/docs_server/mcp/indexer.py` → `extract_headings()`

```python
# Current code — only captures h2
matches = re.findall(r"^##\s+(.+)$", content, re.MULTILINE)
```

UC identifiers appear in h3 headings throughout the spec files, e.g.:

```markdown
### UC-2-002 Create a Template from Scratch
### UC-2-003 Clone an Existing Template
```

These never make it into the `headings` field (boost=1.5). They land only in the raw
`content` field (boost=1.0) where they compete with the entire body text. The `headings`
field only ever contains `##` section titles like `## Actors` or `## Preconditions`.

**Fix:** Capture all heading levels h1–h6 (or at minimum h1–h4):

```python
matches = re.findall(r"^#{1,6}\s+(.+)$", content, re.MULTILINE)
```

For identifiers specifically, h3 is the most important level because that is where
individual UC entries are defined.

---

### Bug 2 — single-character tokens silently dropped, breaking hyphenated identifiers (HIGH)

**Location:** `src/docs_server/mcp/schema.py` → `StemmingAnalyzer` pipeline

`StemmingAnalyzer()` composes a `StopFilter(min=2, ...)`. Any token shorter than
2 characters is discarded before it reaches the index.

When the `RegexTokenizer` splits `UC-2-002` on the hyphen (which is not a `\w` character),
it produces three tokens: `UC`, `2`, `002`. After lowercasing, `2` has length 1 and is
**silently dropped**. The remaining indexed tokens are `["uc", "002"]`.

At query time the user's input `UC-2-002` goes through the same pipeline, yielding the
same `["uc", "002"]`. This does match documents — but the match is **far too broad**:
any document containing both the word "uc" and the string "002" scores equally, regardless
of whether they actually reference UC-2-002.

Worse, `UC-3-002` and `UC-4-002` score identically because their middle digit is also
discarded. Precision collapses.

**Fix A (minimal):** Lower `min` to `1` in the custom analyzer:

```python
from whoosh.analysis import StemmingAnalyzer, RegexTokenizer, LowercaseFilter, StopFilter, StemFilter

STOP_WORDS = frozenset({'with', 'the', 'in', 'by', ...})  # keep existing set

analyzer = (
    RegexTokenizer()
    | LowercaseFilter()
    | StopFilter(stoplist=STOP_WORDS, minsize=1)  # was min=2
    | StemFilter()
)
```

**Fix B (better):** Keep `min=2` for prose text but use a separate non-stemming
`ID`-style field for identifiers (see Bug 3 / New Field below).

---

### Bug 3 — hyphenated identifiers are not preserved as atomic terms (MEDIUM)

**Location:** `src/docs_server/mcp/schema.py` — tokenizer regex

The `RegexTokenizer` default pattern `[\w\*]+(\.?[\w\*]+)*` matches word-characters
and dots only. A hyphen between alphanumeric segments is treated as a boundary,
splitting `UC-2-002` into three tokens instead of one.

This means there is **no way** to search for the exact string `UC-2-002` as a phrase.
The closest the user can do is use Whoosh's phrase syntax `"UC-2-002"`, which requires
all three tokens to appear in order — but still loses the single-digit "2" via Bug 2.

**Fix:** Add a `PhraseSplitter` filter or a custom regex that joins tokens separated by
hyphens when both sides are alphanumeric. Alternatively, extend the tokenizer pattern
to also emit a composite token:

```python
# Extended pattern: also matches hyphenated identifiers like UC-2-002
tokenizer = RegexTokenizer(r'[\w][\w\-]*[\w]|[\w]+')
```

This emits `UC-2-002` as a single token in addition to (or instead of) splitting it.

---

## Proposed New Field: `identifiers`

Rather than patching the existing text fields, the cleanest solution is to add a
dedicated `identifiers` field that:

1. Extracts all tokens matching a structured identifier pattern from headings
2. Preserves them verbatim (no stemming, no stop-word filtering)
3. Gives them a very high boost (e.g., `field_boost=5.0`)

**Extraction regex (covers UC, AUTH, G- patterns):**

```python
IDENTIFIER_PATTERN = re.compile(
    r'\b(?:UC[-_]?[\w][\w\-]*|AUTH[-_]\d+|G[-_]\d+|[A-Z]{2,6}[-_]\d{1,3}(?:[-_]\d{1,3})*)\b'
)

def extract_identifiers(content: str) -> list[str]:
    """Extract structured identifiers from headings only (not body text)."""
    identifiers = []
    for line in content.splitlines():
        if line.startswith('#'):  # any heading level
            identifiers.extend(IDENTIFIER_PATTERN.findall(line))
    return list(dict.fromkeys(identifiers))  # deduplicate, preserve order
```

**Schema addition:**

```python
# schema.py
from whoosh.analysis import IDTokenizer

identifiers=TEXT(
    analyzer=IDTokenizer() | LowercaseFilter(),
    stored=True,
    field_boost=5.0,
),
```

Using `IDTokenizer` (splits on whitespace only) ensures `UC-2-002` is a single token.

**Indexer addition:**

```python
# indexer.py → WhooshSearchBackend.add_document
self._writer.add_document(
    ...
    identifiers=" ".join(doc.identifiers),
    ...
)
```

**Query parser addition:**

```python
# search.py
parser = MultifieldParser(
    ["identifiers", "title", "content", "headings"],
    schema=whoosh_index.schema,
    fieldboosts={"identifiers": 5.0, "title": 2.0, "headings": 1.5},
)
```

With this in place, `UC-2-002` becomes an exact lookup: one token, one field,
maximum boost — it should be the first result every time.

---

## Additional Improvements

### 4. Include `path` as a searchable text field (LOW)

Currently `path` is `ID(unique=True)` — exact match only. File names like
`00_specs/screens/AUTH_01_login_screen.md` contain useful identifier signal.
Adding a separate `path_text` field with a `RegexTokenizer` on slashes and
underscores would let users find documents by filename fragment.

### 5. Add `fieldboosts` at query time (LOW)

`MultifieldParser` accepts a `fieldboosts` kwarg that **multiplies** on top of
schema-time boosts. Currently no `fieldboosts` are passed at query time, so all
tuning lives in the schema. Separating concerns makes it easier to tune without
rebuilding the index:

```python
parser = MultifieldParser(
    ["title", "content", "headings"],
    schema=whoosh_index.schema,
    fieldboosts={"title": 2.0, "headings": 1.5},  # separate from schema boosts
)
```

### 6. Add heading-level weights (LOW)

All heading levels contribute equally to the `headings` field. An h3 that names a
specific UC entry is more specific than an h2 section title like `## Actors`. A
multi-field approach (separate `h2_headings`, `h3_headings` fields) would allow
`h3` items to score higher than `h2` items, but this may be over-engineering for
the current doc size (50 docs). The `identifiers` field in Proposal 3 already
solves this for identifier lookups specifically.

---

## Implementation Plan

Ordered by priority and effort:

| # | Change | File(s) | Effort | Impact |
|---|--------|---------|--------|--------|
| 1 | Extend `extract_headings()` to h1–h4 | `indexer.py` | 1 line | HIGH |
| 2 | Add `identifiers` field + `extract_identifiers()` | `schema.py`, `indexer.py`, `search.py` | ~40 lines | HIGH |
| 3 | Add `identifiers` to `MultifieldParser` with `fieldboosts` | `search.py` | 5 lines | HIGH |
| 4 | Lower `StopFilter` minsize from 2 to 1 | `schema.py` | 1 line | MEDIUM |
| 5 | Extend tokenizer pattern to preserve hyphenated tokens | `schema.py` | 5 lines | MEDIUM |
| 6 | Add `path_text` searchable field | `schema.py`, `indexer.py`, `search.py` | ~20 lines | LOW |

Items 1–3 together fully resolve the `UC-2-002` failure case. Items 4–5 improve
precision for other hyphenated identifiers. Item 6 is a nice-to-have.

**Schema version must be bumped** whenever field definitions change, to invalidate
the Whoosh cache automatically:

```python
# schema.py
SCHEMA_VERSION = "2.0"  # was "1.0"
```

---

## Test Cases to Add

```python
# tests/test_mcp_search.py

def test_uc_identifier_exact(search_index):
    """UC-2-002 should return the document containing that UC as first result."""
    results = search_docs("UC-2-002")
    assert results, "Expected at least one result"
    assert results[0].path == "00_specs/02_use_cases_UC2_template_management_v1.md"

def test_uc_identifier_variant(search_index):
    """UC2-002 (no separator) should still match."""
    results = search_docs("UC2-002")
    assert results

def test_hyphenated_identifier_preserved(search_index):
    """AUTH-01 should return the login screen document."""
    results = search_docs("AUTH-01")
    assert results
    assert any("AUTH_01" in r.path for r in results)

def test_single_digit_token_not_dropped(search_index):
    """Searching UC-3-002 must NOT return the same results as UC-4-002."""
    r3 = search_docs("UC-3-002")
    r4 = search_docs("UC-4-002")
    # Top results should differ
    assert r3[0].path != r4[0].path
```

---

## References

- `src/docs_server/mcp/schema.py` — Whoosh schema definition
- `src/docs_server/mcp/indexer.py` — document parsing and index building
- `src/docs_server/mcp/search.py` — query execution
- [Whoosh analysis docs](https://whoosh.readthedocs.io/en/latest/analysis.html)
- [Whoosh field boosting](https://whoosh.readthedocs.io/en/latest/searching.html#scoring-and-sorting)
