# Production Readiness: Upload and Cache Implementation Plan

**Goal:** Make startup seeding opt-in, show real upload/indexing stages, and cache extraction by PDF SHA-256 while preserving P015 page-101 behavior.

**Architecture:** Add a false-by-default backend setting for demo seeding. Compute the SHA-256 from upload bytes in the registry and use that digest as the cache filename; when loading cached extraction, bind document references to the new upload ID. Track browser upload transfer completion with XMLHttpRequest and show named states only.

**Tech Stack:** FastAPI, Pydantic Settings, PyMuPDF, React, TypeScript, pytest.

## Tasks

1. Add `seed_sample_documents: bool = False`, gate the startup lifespan call, and document `SEED_SAMPLE_DOCUMENTS=true` for demos.
2. Change registry cache paths to the PDF SHA-256 digest; preserve per-upload document IDs in cached evidence, provenance, and table objects; test first parse, exact-byte cache reuse, and differing-byte isolation.
3. Replace the upload boolean with `uploading | indexing | null`, use XHR upload events to switch stages after transfer completes, and render those labels without a percentage.
4. Run the cache/upload regression test and the P015 HTTP verification; ensure P015 answers 500 with page 101 evidence.
