# Testing Documentation — COMP3011 Coursework 2

## Overview

The test suite covers the three core modules (crawler, indexer, search) plus advanced retrieval features and performance characteristics. Tests are written with Python's built-in `unittest` framework and use `unittest.mock` for network isolation.

**68 tests — all pass.**

```
Ran 68 tests in ~0.28s

OK
```

---

## Running the Tests

### Run all tests (recommended)
```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

### Run a single test file
```bash
python3 -m unittest tests.test_crawler -v
python3 -m unittest tests.test_indexer -v
python3 -m unittest tests.test_search -v
python3 -m unittest tests.test_advanced_search -v
python3 -m unittest tests.test_performance -v
```

### Run a single test method
```bash
python3 -m unittest tests.test_indexer.TestInvertedIndex.test_search_single_word -v
```

### Run benchmark script
```bash
python3 scripts/benchmark.py
```

---

## Test File Breakdown

### `tests/test_crawler.py` — 13 tests

Tests the `WebCrawler` class in `src/crawler.py`.

| Test | Description |
|---|---|
| `test_crawler_initialization` | Correct default attribute values on construction |
| `test_url_validation_same_domain` | Valid same-domain URLs accepted |
| `test_url_validation_different_domain` | External domains rejected |
| `test_text_extraction_from_html` | Script/style tags stripped; body text preserved |
| `test_text_extraction_empty_html` | Empty body returns empty string |
| `test_text_extraction_with_special_chars` | Special characters handled without crash |
| `test_link_extraction` | Relative and absolute links resolved; external links filtered |
| `test_link_extraction_removes_fragments` | `#fragment` stripped from URLs |
| `test_politeness_window_enforcement` | `sleep()` called when elapsed < politeness window |
| `test_duplicate_url_tracking` | Already-visited URLs return empty without re-fetching |
| `test_fetch_page_success` | Mocked `requests.get` — URL and HTML returned correctly |
| `test_fetch_page_network_error` | `RequestException` caught; empty tuple returned |
| `test_crawl_multiple_pages` | Multi-page crawl via mocked HTTP; link-following verified |

**Mocking strategy:** All HTTP calls are patched with `@patch('src.crawler.requests.get')` to avoid real network traffic during tests. Response objects are mocked with `unittest.mock.Mock`.

---

### `tests/test_indexer.py` — 23 tests

Tests the `InvertedIndex` class in `src/indexer.py`.

**`TestInvertedIndex` (17 tests)**

| Test | Description |
|---|---|
| `test_index_initialization` | Empty index has zero words and entries |
| `test_tokenization_basic` | Lowercase split on whitespace |
| `test_tokenization_case_insensitive` | All tokens are lowercase |
| `test_tokenization_removes_punctuation` | Commas, periods, exclamation marks stripped |
| `test_tokenization_handles_special_chars` | Apostrophes split; hyphens within words preserved |
| `test_tokenization_empty_string` | Empty input → empty list |
| `test_index_single_page` | Page indexed; words appear in `all_words` |
| `test_index_word_frequency` | Frequency count correct for repeated words |
| `test_index_multiple_pages` | Word spanning multiple pages has correct page count |
| `test_search_nonexistent_word` | Returns empty list for unknown word |
| `test_search_case_insensitive` | `HELLO`, `hello`, `HeLLo` all return same results |
| `test_search_all_words` | AND query returns intersection correctly |
| `test_search_all_words_empty_result` | No common page → empty result |
| `test_search_all_words_single_word` | Single-element AND query works |
| `test_index_statistics` | `get_statistics()` returns correct unique_words/indexed_pages |
| `test_get_word_pages_empty_index` | Empty index returns `[]` without error |
| `test_duplicate_indexing` | Re-indexing same page creates separate entries |

**`TestInvertedIndexEdgeCases` (6 tests)**

| Test | Description |
|---|---|
| `test_index_empty_content` | Empty string → zero index entries |
| `test_index_whitespace_only` | Whitespace-only → zero index entries |
| `test_index_single_word` | Single-token content indexed correctly |
| `test_very_long_text` | 1,000-word document; frequency=1000 recorded |
| `test_special_characters_only` | `!@#$%^&*()` → no tokens extracted |
| `test_numbers_in_text` | Numeric tokens included in index |

---

### `tests/test_search.py` — 24 tests

Tests the `SearchEngine` class in `src/search.py`.

**`TestSearchEngine` (17 tests)**

| Test | Description |
|---|---|
| `test_find_single_word` | Correct URLs returned for one-word query |
| `test_find_multiple_words` | Implicit AND: both words must appear |
| `test_find_three_words` | Three-word AND query returns single page |
| `test_find_case_insensitive` | Mixed-case queries yield identical results |
| `test_find_nonexistent_word` | Unknown word → empty list |
| `test_find_impossible_combination` | Words never co-occurring → empty list |
| `test_find_empty_query` | Empty string and whitespace → empty list |
| `test_print_word_found` | Returns correct structure for found word |
| `test_print_word_not_found` | `found=False` and empty `pages` for unknown word |
| `test_print_word_frequency_sorting` | Pages sorted by frequency, descending |
| `test_format_find_output_single_result` | Output includes URL and count |
| `test_format_find_output_multiple_results` | Multiple URLs listed in output |
| `test_format_find_output_no_results` | "No pages found" message shown |
| `test_format_print_output_found` | Frequency and URL present in formatted output |
| `test_format_print_output_not_found` | "not found" message shown |
| `test_search_with_whitespace_padding` | Leading/trailing spaces ignored |
| `test_search_results_sorted` | Results consistently sorted alphabetically |

**`TestSearchEngineEdgeCases` (6 tests)**

| Test | Description |
|---|---|
| `test_search_empty_index` | Search on empty index returns `[]` |
| `test_print_empty_index` | Print on empty index returns not-found |
| `test_search_special_characters` | HTML-punctuated content still searchable |
| `test_multiple_spaces_in_query` | Multi-space queries treated same as single space |
| `test_results_are_unique` | Duplicate-word pages yield unique URL list |
| `test_single_word_query_ordering` | Alphabetical ordering consistent across calls |

**`TestSearchIntegration` (1 test)**

| Test | Description |
|---|---|
| `test_realistic_search_scenario` | End-to-end: 4 pages indexed, single/multi/impossible queries verified |

---

### `tests/test_advanced_search.py` — 6 tests

Tests phrase search, boolean operators, and TF-IDF ranking.

| Test | Description |
|---|---|
| `test_phrase_search` | `"good friends"` matches only pages with consecutive tokens |
| `test_or_query` | `friendship OR death` returns union of both word's pages |
| `test_and_not_query` | `life AND NOT death` correctly excludes pages containing death |
| `test_implicit_and_with_parentheses` | `good AND (friends OR people)` respects operator precedence |
| `test_ranked_results_descending` | TF-IDF scores strictly non-increasing; top result is correct page |
| `test_rank_output_contains_scores` | Formatted rank output contains `score=` and header line |

---

### `tests/test_performance.py` — 2 tests

Latency assertions on large synthetic indices. These guard against regressions that make the system unacceptably slow.

| Test | Description | Threshold |
|---|---|---|
| `test_large_index_search_latency` | 800-page index built; AND query executed | build < 3.5 s, query < 0.1 s |
| `test_ranked_query_latency` | 600-page index; phrase+OR ranked query | rank < 0.2 s |

---

## Testing Strategy

### Layers

| Layer | Files | Purpose |
|---|---|---|
| Unit | `test_crawler`, `test_indexer`, `test_search` | Each public method tested in isolation |
| Integration | `TestCrawlerIntegration`, `TestSearchIntegration` | Components composed together |
| Advanced / behavioural | `test_advanced_search` | Complex query semantics verified end-to-end |
| Performance | `test_performance` | Latency bounds prevent algorithmic regressions |

### Network isolation

The crawler tests mock `requests.get` at the module level using `@patch('src.crawler.requests.get')`. This ensures:
- Tests are deterministic (no dependency on network or target site availability)
- Tests run fast (no real HTTP delays)
- The politeness window can be reduced to 0.01s for speed

### Edge cases covered

- Empty or whitespace-only content/queries
- Non-existent words
- Words appearing only on some pages (AND intersection)
- Repeated words (frequency counting)
- Case variations (`HELLO`, `hello`, `HeLLo`)
- Special characters and punctuation
- Numeric tokens
- Hyphenated words (`well-known`)
- Very long documents (1,000 tokens)
- Phrase queries requiring consecutive position matching
- Boolean NOT applied to the entire indexed URL universe
- Operator precedence with parentheses

### What is not unit-tested

- The actual `build` and `load` CLI commands — these are covered by manual demonstration in the video, as they require a live network connection or a full index file on disk.
- `persistence.py` save/load round-trip — exercised indirectly; the `data/index.json` in this repo is a real artefact of running `build`.

---

## Continuous Integration

The CI pipeline is defined in `.github/workflows/ci.yml` and runs automatically on every push and pull request.

```
Platforms : ubuntu-latest
Python    : 3.10, 3.11, 3.12 (matrix)
Steps     : install deps → run full test suite → run benchmark smoke check
```

This ensures the codebase is tested across three Python minor versions and that the benchmark does not error.
