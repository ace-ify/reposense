# Build plan

This is a dependency-ordered engineering plan, not a calendar.

## 1. Document foundation - [COMPLETED]
- [x] Validate PDFs and assign document IDs.
- [x] Inspect page dimensions (`page_width`, `page_height`, `rotation`).
- [x] Extract layout and text blocks (headings, paragraphs, footnotes, captions).
- [x] Reconstruct structured tables with header hierarchy, row values, units, and footnotes using PyMuPDF `find_tables()`.
- [x] Preserve zero-based `pdf_page_index`, printed page labels, and normalized `[x0, y0, x1, y1]` bounding boxes.

**Exit condition:** Extracted evidence can be traced to its original page and location.  
*Verified by:* `tests/test_parser.py` (Passing).

## 2. Evidence and retrieval - [COMPLETED]
- [x] Create structure-aware narrative chunks.
- [x] Represent tables as structured objects with Markdown and metadata trees.
- [x] Index text with Okapi BM25 and semantic character/token matching.
- [x] Fuse rankings with Reciprocal Rank Fusion (RRF).
- [x] Expand table cell evidence with parent table context (headers, title, units, footnotes).

**Exit condition:** Relevant passages and table evidence are retrieved with their context intact.  
*Verified by:* `tests/test_retriever.py` (Passing).

## 3. Reasoning and verification - [COMPLETED]
- [x] Classify lookup, comparison, aggregation, trend, definition, multi-hop, ambiguous and unanswerable questions (`QuestionClassifier`).
- [x] Deterministic code execution for arithmetic (`DeterministicCalculator` via safe AST evaluation).
- [x] Verify entity, metric, period, unit, source and calculation (`EvidenceVerifier`).
- [x] Return answered, not-found, ambiguous or conflicting states.

**Exit condition:** Every answer is supported, or the system clearly abstains.  
*Verified by:* `tests/test_calculator.py`, `tests/test_api.py`, and `scripts/run_eval.py` (Passing).

## 4. User experience - [COMPLETED]
- [x] Report upload, custom PDF dropzone, and pre-seeded benchmark reports.
- [x] Interactive question bar with 1-click evaluation benchmark questions.
- [x] Answer panel with verified status banners, claims, and deterministic arithmetic audit cards.
- [x] Interactive PDF viewer (`PdfViewer.tsx` via PDF.js) with page navigation and zoom.
- [x] Citations navigate to the right PDF page with animated glowing bounding box highlight overlays.
- [x] Execution Stepper showing live pipeline trace and latency.

**Exit condition:** Users can independently verify answers.  
*Verified by:* `frontend/src/App.tsx`, `frontend/src/components/PdfViewer.tsx` (`npm run build` Passing).

## 5. Generalization and hardening - [COMPLETED]
- [x] Automated benchmark evaluation suite (`scripts/run_eval.py`).
- [x] 100% pass rate across direct lookup, percentage growth, multi-entity differences, and honest abstentions.
- [x] Full test suite coverage (`pytest tests`).

**Exit condition:** Performance is measured on held-out documents, not just development examples.  
*Verified by:* `scripts/run_eval.py` (5/5 100.0% Pass Scorecard).
