import logging
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from starlette.concurrency import run_in_threadpool

from backend.app.pipeline.registry import get_registry
from backend.app.core.upload_observability import emit
from backend.app.schemas.evidence import DocumentItem, EvidenceItem, TableItem

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("", response_model=DocumentItem, status_code=201)
async def upload_document(file: UploadFile = File(...)) -> DocumentItem:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    emit("[UPLOAD] Multipart parsed")

    registry = get_registry()
    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = Path(tmp.name)

    logger.info(f"[UPLOAD] File saved to temp: path={tmp_path.name}")

    try:
        doc_item = await run_in_threadpool(registry.register_file, tmp_path, file.filename)
        logger.info(f"[UPLOAD] Document registered successfully: doc_id={doc_item.document_id}")
        return doc_item
    except Exception as exc:
        logger.exception(f"[UPLOAD] Document processing failed for filename={file.filename}")
        raise HTTPException(status_code=500, detail=f"Failed to process document: {exc}") from exc
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

@router.get("", response_model=list[DocumentItem])
def list_documents() -> list[DocumentItem]:
    registry = get_registry()
    return registry.list_documents()

@router.get("/{document_id}", response_model=DocumentItem)
def get_document(document_id: str) -> DocumentItem:
    registry = get_registry()
    doc = registry.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")
    return doc

@router.get("/{document_id}/pdf")
def get_document_pdf(document_id: str):
    registry = get_registry()
    pdf_path = registry.get_pdf_path(document_id)
    if not pdf_path or not pdf_path.is_file():
        raise HTTPException(status_code=404, detail=f"PDF file for '{document_id}' not found.")
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=pdf_path.name,
    )

@router.get("/{document_id}/evidence", response_model=dict[str, Any])
def get_document_evidence(document_id: str) -> dict[str, Any]:
    registry = get_registry()
    doc = registry.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")

    evidence = registry.get_evidence(document_id)
    tables = registry.get_tables(document_id)
    provenances = registry.get_page_provenances(document_id)

    return {
        "document_id": document_id,
        "page_count": doc.page_count,
        "provenances": [p.model_dump() for p in provenances],
        "evidence_count": len(evidence),
        "table_count": len(tables),
        "evidence": [e.model_dump() for e in evidence],
        "tables": [t.model_dump() for t in tables],
    }

@router.get("/{document_id}/suggestions", response_model=list[dict[str, Any]])
def get_document_suggestions(document_id: str) -> list[dict[str, Any]]:
    registry = get_registry()
    doc = registry.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")

    tables = registry.get_tables(document_id)
    evidence = registry.get_evidence(document_id)
    suggestions: list[dict[str, Any]] = []

    # If we have structured tables, generate domain-agnostic questions from the table
    if tables:
        # Pick the most populated table
        best_table = max(tables, key=lambda t: len(t.rows) * len(t.headers))
        t_title = best_table.title or f"Table on Page {best_table.printed_page_number}"
        t_clean_title = t_title.replace("Title:", "").strip()

        # Flatten headers (headers can be list[list[str]] or list[str])
        flat_headers: list[str] = []
        for h in best_table.headers:
            if isinstance(h, list):
                flat_headers.extend([str(item) for item in h if item])
            elif h:
                flat_headers.append(str(h))

        # Find year columns if any
        year_headers = [h for h in flat_headers if re.search(r"\b(20\d\d|19\d\d)\b", h)]
        
        # 1. Row lookup
        first_row_label = ""
        for r in best_table.rows:
            label = r[1] if len(r) > 1 and r[1] and not str(r[1]).isdigit() else r[0]
            if label and not str(label).isdigit() and str(label).lower() not in ("total", "s.no.", "s. no.", "sl"):
                first_row_label = str(label)
                break

        if first_row_label:
            if year_headers:
                year_match = re.search(r"\b(20\d\d|19\d\d)\b", year_headers[-1])
                latest_year = year_match.group(1) if year_match else "2023"
                suggestions.append({
                    "category": "Table Lookup",
                    "label": f"🎯 Table Lookup: {first_row_label} ({latest_year})",
                    "question": f"What was the value for {first_row_label} in {latest_year}?",
                    "intent": "lookup",
                })
            else:
                suggestions.append({
                    "category": "Table Lookup",
                    "label": f"🎯 Table Lookup: {first_row_label}",
                    "question": f"What were the recorded figures for {first_row_label} in {t_clean_title}?",
                    "intent": "lookup",
                })

        # 2. Deterministic Arithmetic (Percentage Change across periods)
        if len(year_headers) >= 2 and first_row_label:
            m1 = re.search(r"\b(20\d\d|19\d\d)\b", year_headers[-2])
            m2 = re.search(r"\b(20\d\d|19\d\d)\b", year_headers[-1])
            if m1 and m2:
                y1 = m1.group(1)
                y2 = m2.group(1)
                suggestions.append({
                    "category": "Deterministic Arithmetic",
                    "label": f"🔢 Deterministic Math: {first_row_label} ({y1}-{y2})",
                    "question": f"What was the percentage change in {first_row_label} between {y1} and {y2}?",
                    "intent": "comparison",
                })

        # 3. Cross-Entity Difference
        valid_row_labels = []
        for r in best_table.rows:
            lbl = r[1] if len(r) > 1 and r[1] and not str(r[1]).isdigit() else r[0]
            if lbl and not str(lbl).isdigit() and str(lbl).lower() not in ("total", "s.no.", "s. no.", "sl"):
                valid_row_labels.append(str(lbl))
                if len(valid_row_labels) >= 2:
                    break

        if len(valid_row_labels) >= 2:
            period_suffix = ""
            if year_headers:
                year_match = re.search(r"\b(20\d\d|19\d\d)\b", year_headers[-1])
                if year_match:
                    period_suffix = f" in {year_match.group(1)}"
            suggestions.append({
                "category": "Multi-Entity Difference",
                "label": f"⚖️ Comparison: {valid_row_labels[0]} vs {valid_row_labels[1]}",
                "question": f"What was the difference between {valid_row_labels[0]} and {valid_row_labels[1]}{period_suffix}?",
                "intent": "comparison",
            })

        # 4. Total/Overall Query
        suggestions.append({
            "category": "Total / Category Breakdown",
            "label": f"📊 Total Breakdown: {t_clean_title[:35]}",
            "question": f"What was the total and overall breakdown in {t_clean_title}?",
            "intent": "lookup",
        })

    # 5. Domain-Agnostic Abstention Query
    suggestions.append({
        "category": "Honest Abstention",
        "label": "🛡️ Abstention Check: Unreported Future Metric",
        "question": "What is the projected outcome for fiscal year 2049?",
        "intent": "unanswerable",
    })

    return suggestions
