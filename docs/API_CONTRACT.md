# Initial API contract

Base path: `/api/v1`

- `GET /health` — service health.
- `POST /documents` — multipart PDF upload; returns document ID and processing status.
- `GET /documents/{document_id}` — document metadata and processing status.
- `POST /questions` — accepts `{ "question": "...", "document_ids": ["doc_..."] }` and returns the answer/citation contract in `DATA_CONTRACTS.md`.

Version schemas and tests together when changing this contract.
