# Architecture

```text
PDF upload
  -> document registry
  -> page inspection
  -> layout/text extraction + selective OCR
  -> narrative evidence + structured tables/charts
  -> canonical evidence store
  -> BM25 index + vector index
  -> hybrid retrieval + fusion + reranking
  -> question router
  -> lookup / calculation / multi-hop workflow
  -> evidence verification
  -> answer or abstention
  -> API + citations + PDF highlighting
```

## Boundaries
- Ingestion: validation, parsing, OCR and extraction.
- Evidence: canonical structures and provenance.
- Indexing: lexical and vector representations.
- Retrieval: ranked evidence candidates.
- Reasoning: workflow selection and deterministic operations.
- Verification: decide whether evidence supports the answer.
- Presentation: answers, citations and document highlights.

## Design rules
- Keep model calls behind replaceable adapters.
- Never use an LLM as the source of truth for arithmetic.
- Preserve source coordinates and original extracted text.
- Keep zero-based PDF page index separate from printed page label.
- Treat headers, units and footnotes as part of a table value's meaning.
- Never couple question logic to a particular report, page or table number.

## Proposed stack
PyMuPDF and Docling for parsing; PaddleOCR as selective OCR fallback; BM25 and BGE-M3 for retrieval; Reciprocal Rank Fusion and BGE reranker for ranking; LangGraph for multi-step orchestration; Python/Pandas/NumPy for calculations; FastAPI; PostgreSQL; Qdrant; React/TypeScript; PDF.js.
