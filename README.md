# Report Intelligence Assistant

> **Evidence-first Question Answering & Verification Engine for Complex Statistical and Financial Reports.**

[![Tests](https://img.shields.io/badge/tests-13%20passed-brightgreen.svg)]()
[![Benchmark Accuracy](https://img.shields.io/badge/eval%20scorecard-100%25-brightgreen.svg)]()
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.13-blue.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)]()
[![React](https://img.shields.io/badge/React-18.3-61DAFB.svg)]()

---

## 🏆 Key Innovations (Why this wins hackathons)

Most standard RAG pipelines fail catastrophically on statistical and financial reports because:
1. **They flatten tables into raw text**, destroying row/column relationships and multi-level header paths.
2. **They let LLMs estimate arithmetic**, hallucinating growth rates, percentage changes, and totals.
3. **They cite vague or inaccurate page numbers**, confusing zero-based PDF page indexes with printed page labels.
4. **They cannot visually pinpoint proof**, lacking bounding box coordinate provenance on the actual PDF.
5. **They guess instead of refusing**, generating believable falsehoods when data is absent.

### Our Moats:
- **First-Class Table Intelligence**: Extracts tables with multi-level header trees, row labels, cell bounding boxes `[x0, y0, x1, y1]`, units, and footnotes using PyMuPDF.
- **Deterministic Python Arithmetic Engine (ADR-003)**: Never lets an LLM do mental math. Percentage change, differences, ratios, and aggregations are computed with safe AST-evaluated Python code and audited in the response.
- **Dual Hybrid Retrieval (BM25 + Semantic + Table Expansion)**: RRF (Reciprocal Rank Fusion) ranking with automatic parent table context expansion.
- **Strict Verification & Honest Abstention (ADR-004)**: Verifies entity, period, and metric grounding. Cleanly abstains with `not_found` or `ambiguous` rather than hallucinating.
- **Interactive PDF Viewer with Real-Time Bounding Box Highlights**: Clicking any citation navigates to the PDF page and renders an animated glowing highlight overlay right over the cited passage or table cell.
- **Instant Demo Experience**: Pre-seeded benchmark reports with 1-click test questions for zero-friction judge evaluation.

---

## 🚀 Quickstart

### 1. Start Both Backend & Frontend (One Command)
```powershell
.\scripts\start_dev.ps1
```

Or start them manually:

**Backend:**
```powershell
.\.venv\Scripts\Activate.ps1
uvicorn backend.app.main:app --reload --port 8000
```
API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

**Frontend:**
```powershell
cd frontend
npm run dev
```
UI Application: [http://localhost:5173](http://localhost:5173)

---

## 🧪 Testing & Evaluation

### Run Test Suite
```powershell
.\.venv\Scripts\pytest.exe tests
```
*Result: 13 passed tests (Contracts, Health, Parser, Table Extraction, AST Calculator, Hybrid Retriever, End-to-End API)*

### Run Benchmark Evaluation Scorecard
```powershell
.\.venv\Scripts\python.exe scripts/run_eval.py
```
*Result: 5/5 (100.0% Accuracy across Lookups, Percentage Change, Multi-Entity Differences, and Honest Abstentions)*

---

## 🏛️ Architecture

```text
PDF Upload / Benchmark
  ├──> PyMuPDF Parser (Preserves normalized [x0, y0, x1, y1] coordinates & printed page labels)
  ├──> Document Registry (In-memory & disk persistence)
  ├──> Hybrid Retriever (Okapi BM25 + Semantic + RRF Fusion + Table Context Expansion)
  ├──> Question Classifier (Lookup, Comparison, Aggregation, Trend, Multi-Hop, Unanswerable)
  ├──> Deterministic Arithmetic Engine (Safe AST-evaluated Python formulas)
  ├──> Grounding Verifier (Entity, Metric, Period, Unit, and Provenance checks)
  └──> Interactive Frontend (Studio layout, live stepper, PDF.js canvas with bounding box overlays)
```
