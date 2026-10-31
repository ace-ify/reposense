import shutil
import tempfile
from pathlib import Path
from typing import Any
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from backend.app.pipeline.registry import get_registry
from backend.app.schemas.evidence import DocumentItem, EvidenceItem, TableItem

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("", response_model=DocumentItem, status_code=201)
async def upload_document(file: UploadFile = File(...)) -> DocumentItem:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    registry = get_registry()
    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = Path(tmp.name)

    try:
        doc_item = registry.register_file(tmp_path, file.filename)
        return doc_item
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
