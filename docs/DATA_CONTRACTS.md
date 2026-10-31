# Data contracts

Map parser-specific output into these canonical structures before indexing.

## Document
```json
{
  "document_id": "doc_...",
  "filename": "report.pdf",
  "content_hash": "sha256:...",
  "page_count": 0,
  "processing_status": "pending|processing|ready|failed"
}
```

## Page provenance
```json
{
  "document_id": "doc_...",
  "pdf_page_index": 0,
  "printed_page_number": null,
  "page_width": 0,
  "page_height": 0,
  "rotation": 0,
  "extraction_method": "native_text|ocr|mixed",
  "warnings": []
}
```
`pdf_page_index` is zero-based and is the PDF viewer navigation key. Printed page labels are optional display metadata.

## Evidence item
```json
{
  "evidence_id": "ev_...",
  "document_id": "doc_...",
  "pdf_page_index": 0,
  "printed_page_number": null,
  "kind": "paragraph|heading|table|table_cell|chart|caption|footnote",
  "text": "",
  "normalized_text": null,
  "bbox": [0, 0, 0, 0],
  "parent_id": null,
  "metadata": {},
  "extraction_confidence": null,
  "warnings": []
}
```

## Table
```json
{
  "table_id": "tbl_...",
  "document_id": "doc_...",
  "pdf_page_index": 0,
  "printed_page_number": null,
  "title": null,
  "headers": [],
  "rows": [],
  "units": {},
  "footnotes": [],
  "bbox": [0, 0, 0, 0],
  "extraction_confidence": null,
  "warnings": []
}
```
Preserve multi-level header paths; do not flatten away year, metric, category or unit context.

## Answer
```json
{
  "status": "answered|not_found|ambiguous|conflicting",
  "answer": null,
  "claims": [{"text": "", "evidence_ids": [], "calculation": null}],
  "citations": [{
    "document_id": "doc_...",
    "pdf_page_index": 0,
    "printed_page_number": null,
    "evidence_id": "ev_...",
    "bbox": null
  }],
  "warnings": []
}
```

## Invariants
- Evidence references an existing document and valid PDF page.
- Citation resolves to evidence from the same document and page.
- Derived claims record source values and calculation steps.
- Unknown labels, units and periods remain unknown; never infer silently.
