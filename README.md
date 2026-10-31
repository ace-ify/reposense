# Report Navigator

**Ask questions about a long statistics report and trace each answer back to its source page.**

Report Navigator is a document question-answering project built for **Problem 05: LLM / RAG**. Governments publish reports containing hundreds of pages of prose, tables, and footnotes. Finding one statistic can take time, and an answer without a source is difficult to trust. This application lets a user upload a PDF, ask a question in plain language, and inspect the evidence and page citation used to answer it.

## Problem and solution

The problem is to make information in a long government statistics report easy to find and check. A useful system must retrieve relevant evidence, handle tabular values and calculations carefully, cite the source page, and say when the report does not support an answer.

Report Navigator provides a browser interface and a FastAPI service for uploading PDF reports, extracting page text and tables, searching the extracted evidence, answering questions, and navigating to cited evidence in the PDF. It includes a deterministic calculation path for supported numeric comparisons and an abstention outcome for unsupported questions.

## Try it

The Render configuration is in [`render.yaml`](render.yaml). It defines an API service and a static web service, but automatic deploys are disabled. The repository does not confirm that either service has been deployed or that its public URL is active. Render assigns the frontend URL when the Blueprint is deployed; the API hostname configured as the frontend default is:

- **Web app:** Open the `report-navigator-web` service in the Render dashboard for its assigned public URL. The expected default is `https://report-navigator-web.onrender.com` if that name is available.
- **API:** `https://report-navigator-api.onrender.com`
- **API docs:** `https://report-navigator-api.onrender.com/docs`
- **Health check:** `https://report-navigator-api.onrender.com/api/v1/health`

Treat these as configured deployment targets until the services have been deployed and checked in Render. If Render assigns a different API hostname, update `VITE_API_BASE_URL` on the web service and redeploy it. See [`docs/deployment-render.md`](docs/deployment-render.md).

## Features

- Upload and parse PDF reports through the web app or API.
- Extract narrative text and structured tables, retaining page provenance and normalized page coordinates where available.
- Search report evidence using BM25 lexical ranking and token-overlap similarity, combined with Reciprocal Rank Fusion (RRF); expand retrieved table evidence with its parent table context.
- Route questions into lookup, comparison, aggregation, trend, definition, multi-hop, unanswerable, or ambiguous intents.
- Calculate supported numeric differences and percentage changes in Python rather than asking the LLM to do arithmetic.
- Return answer status, claims, citations, evidence IDs, page references, and calculation details in the API response.
- Open a citation in the PDF viewer and highlight its available bounding box; inspect extracted tables in the table explorer.
- Load built-in sample reports and suggested questions for a quick demo.
- Run a built-in evaluation benchmark through the API and review its scorecard in the interface.
- Use an optional Groq or OpenAI-compatible chat completion integration for answer synthesis when its API key is configured. Deterministic fallback synthesis remains available without a key.

### Current implementation notes

The implemented retriever is an in-process hybrid of BM25 and lexical/token-overlap similarity. Although `.env.example` includes embedding and reranker model settings for future work, the current retrieval code does not call a dense embedding model or a cross-encoder reranker. The document registry, parsed evidence, and indexes are held in process memory; PDFs and parse-cache files are written under the configured upload directory. PostgreSQL and Qdrant are present in the local Docker Compose file but are not currently wired into the runtime registry or retrieval path.

PDF parsing is implemented with PyMuPDF. The deployment Docker image installs Tesseract, but the current parser behavior should be checked against the report being used; this README does not claim universal OCR or PDF-layout support. Table extraction and citation precision depend on the PDF layout and the quality of the parser output.

## Architecture

```text
PDF upload
   │
   ▼
FastAPI document route
   │ validate PDF, store copy, consult content-hash parse cache
   ▼
PyMuPDF parser ──► page provenance, narrative evidence, tables
   │
   ▼
In-memory document registry + BM25 / token-overlap indexes
   │
Question ──► intent classification ──► evidence retrieval + RRF
                                          │
                                          ▼
                      deterministic calculation / optional LLM synthesis
                                          │
                                          ▼
                     answer status + claims + citations + calculations
                                          │
                                          ▼
React UI + PDF.js viewer + evidence/table navigation and highlights
```

### Main components

| Area | Implementation |
| --- | --- |
| API | Python 3.11+, FastAPI, Pydantic, Uvicorn |
| PDF extraction | PyMuPDF; Tesseract is installed in the API container |
| Retrieval | In-process BM25, token-overlap similarity, RRF fusion, table-parent context expansion |
| Question processing | Intent classifier, evidence-driven answer service, verifier, deterministic calculator |
| Optional generation | Groq (`llama-3.3-70b-versatile`) or OpenAI (`gpt-4o-mini`) via chat completions |
| Web client | React 18, TypeScript, Vite, PDF.js |
| Local infrastructure | Docker Compose definitions for PostgreSQL 16 and Qdrant; not required by the current runtime path |
| Deployment | Render Blueprint with a Docker API service and Vite static site |

### Evidence and citations

The API keeps the zero-based PDF page index (`pdf_page_index`) separate from an optional printed page label (`printed_page_number`). Citations refer to extracted evidence IDs and can include normalized bounding-box coordinates. The viewer uses the PDF page index for navigation and uses the bounding box when one is available. Table highlights are table-level when cell-level coordinates are unavailable.

Answers can have `answered`, `not_found`, `ambiguous`, or `conflicting` status. For calculated answers, the response can include source evidence IDs, input values, the operation, formula, and result. Numerical values still require review against the source report, especially where units, headers, footnotes, or table extraction are unclear.

## Quickstart

### Requirements

- Python 3.11 or newer
- Node.js and npm (the frontend lockfile is provided)
- Tesseract OCR is optional for local use; it is installed in the API Docker image

### 1. Set up the API

From the repository root:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

Start the API:

```powershell
uvicorn backend.app.main:app --reload --port 8000
```

The interactive API docs are at [http://localhost:8000/docs](http://localhost:8000/docs).

### 2. Set up the web app

In another terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). Leave `VITE_API_BASE_URL` empty for local development; Vite proxies `/api/v1` requests to `http://localhost:8000`.

On macOS or Linux, create/activate the virtual environment with the usual `python3 -m venv .venv` and `source .venv/bin/activate` commands; the remaining Python and npm commands are the same.

### One-command Windows launcher

After installing the Python and npm dependencies, run:

```powershell
.\scripts\start_dev.ps1
```

The script opens separate backend and frontend terminal windows.

## Configuration

Copy `.env.example` to `.env`. Settings are read by the backend from the environment or `.env`:

| Variable | Purpose | Default / example |
| --- | --- | --- |
| `ENVIRONMENT` | Runtime environment label | `development` |
| `UPLOAD_DIR` | Uploaded PDFs and parse cache location | `data/uploads` |
| `MAX_UPLOAD_MB` | Configured maximum upload size | `100` |
| `GROQ_API_KEY` | Enables Groq chat-completion synthesis when set | Empty |
| `OPENAI_API_KEY` | Enables OpenAI chat-completion synthesis when set and Groq is not set | Empty |
| `SEED_SAMPLE_DOCUMENTS` | Seeds sample PDFs during application startup when true | `false` |
| `VITE_API_BASE_URL` | API base URL baked into the frontend build | Empty locally; API URL in Render config |
| `POSTGRES_DSN` | Reserved/configured PostgreSQL connection string | `postgresql://postgres:postgres@localhost:5432/report_intelligence` |
| `QDRANT_URL` | Reserved/configured Qdrant URL | `http://localhost:6333` |
| `EMBEDDING_MODEL` | Reserved model setting; not used by current retriever | `BAAI/bge-m3` |
| `RERANKER_MODEL` | Reserved model setting; not used by current retriever | `BAAI/bge-reranker-v2-m3` |

Keep provider keys in the backend environment only. Do not add secrets to frontend variables or commit `.env`.

## API

Base path: `/api/v1`. Interactive schema: `/docs`.

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Health check |
| `POST` | `/documents` | Upload and parse a PDF (`multipart/form-data`, field `file`) |
| `GET` | `/documents` | List documents registered in this process |
| `GET` | `/documents/{document_id}` | Get document metadata |
| `GET` | `/documents/{document_id}/pdf` | Retrieve the uploaded PDF |
| `GET` | `/documents/{document_id}/evidence` | Get page provenance, extracted evidence, and tables |
| `GET` | `/documents/{document_id}/suggestions` | Generate question suggestions from extracted content |
| `POST` | `/questions` | Ask a question about one or more document IDs |
| `GET` | `/samples` | Seed and list built-in sample report definitions/questions |
| `GET` | `/evaluation` | Run and return the built-in benchmark scorecard |

Example upload:

```bash
curl -X POST http://localhost:8000/api/v1/documents \
  -F "file=@./report.pdf"
```

Example question (replace the ID with the ID returned by upload):

```bash
curl -X POST http://localhost:8000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{"question":"What was the reported value?","document_ids":["doc_1"]}'
```

The request model is defined in [`backend/app/schemas/question.py`](backend/app/schemas/question.py); the answer and evidence models are in [`backend/app/schemas/evidence.py`](backend/app/schemas/evidence.py). Responses include status, answer text, claims, citations, and optional calculation information.

## Evaluation and development commands

The repo includes a pytest suite and a benchmark endpoint/script. Run them locally when working on the project:

```powershell
python -m pytest -q
python scripts/run_eval.py
```

Other available commands:

```powershell
ruff check .
docker compose up -d       # Start optional local PostgreSQL and Qdrant services
docker compose down
```

Benchmark results are a development aid, not a guarantee of accuracy on unseen reports. Review retrieval, arithmetic, citations, abstentions, OCR, and table extraction separately. See [`docs/EVALUATION.md`](docs/EVALUATION.md).

## Deployment on Render

1. Create a Render Blueprint from this repository and inspect the services defined in `render.yaml`.
2. Deploy `report-navigator-api` and `report-navigator-web` from the Render dashboard; automatic deploys are currently off.
3. If using LLM synthesis, set `GROQ_API_KEY` or `OPENAI_API_KEY` as a secret environment variable on the API service.
4. Confirm `VITE_API_BASE_URL` points to the actual API hostname, then redeploy the frontend.
5. Check `/api/v1/health`, open `/docs`, upload a report, and ask a known question before sharing the app URL.

The Blueprint currently uses Render's Free plan and a temporary upload directory. Uploaded PDFs, the registry, and indexes are not durable across service restarts or sleeps. Upload reports again after a restart. Persistent report availability requires durable storage and a corresponding registry/index rehydration strategy.

## Project layout

```text
backend/app/
  api/routes/       FastAPI endpoints
  core/             Runtime settings
  pipeline/         PDF parsing, registry, retrieval, reasoning, verification, calculation
  schemas/          Pydantic request/response and evidence models
frontend/src/       React application, API client, PDF viewer, table explorer
docs/               Product, architecture, API, deployment, privacy, and evaluation notes
scripts/            Local launcher and benchmark runner
tests/              Parser, retrieval, calculation, contract, and API tests
```

## Limitations

- The registry and search indexes are process-local; multi-worker or durable shared indexing is not implemented.
- PostgreSQL and Qdrant are not currently connected to the request path.
- OCR and layout extraction quality varies by PDF; scanned, rotated, or complex multi-level tables need validation.
- The current “semantic” ranking is token overlap, not a neural embedding search.
- Citation boxes can cover an entire table or evidence region rather than an exact cell or text span.
- Free Render services may sleep, and local service files are temporary.
- There is no user authentication or per-document access control in the current app; do not expose sensitive reports on a public deployment.

## Further documentation

- [Product brief](docs/PRODUCT_BRIEF.md)
- [Architecture](docs/ARCHITECTURE.md)
- [API contract](docs/API_CONTRACT.md)
- [Data contracts](docs/DATA_CONTRACTS.md)
- [Retrieval and reasoning](docs/RETRIEVAL_AND_REASONING.md)
- [Evaluation](docs/EVALUATION.md)
- [Security and privacy](docs/SECURITY_AND_PRIVACY.md)
- [Render deployment](docs/deployment-render.md)
