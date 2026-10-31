# Pipeline implementation notes

Keep concrete adapters separate from API routes. Suggested modules:
- `parsing/pdf_parser.py`: PyMuPDF/Docling adapter and page inspection.
- `parsing/ocr.py`: selective OCR adapter.
- `parsing/table_normalizer.py`: header hierarchy, rows, units and footnotes.
- `indexing/lexical.py`: BM25.
- `indexing/vector.py`: BGE-M3 embeddings and Qdrant.
- `retrieval/hybrid.py`: fusion and reranking.
- `reasoning/router.py`: question routing.
- `reasoning/calculator.py`: deterministic calculations with provenance.
- `verification/answer_verifier.py`: evidence and citation checks.

Do not put model-specific code in API route handlers.
