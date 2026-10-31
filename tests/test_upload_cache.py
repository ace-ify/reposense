import io

import pymupdf
from fastapi.testclient import TestClient

from backend.app.api.routes import documents
from backend.app.main import app
from backend.app.pipeline.registry import DocumentRegistry


def make_pdf(text: str) -> bytes:
    pdf = pymupdf.open()
    page = pdf.new_page()
    page.insert_text((72, 72), text)
    contents = pdf.tobytes(deflate=False)
    pdf.close()
    return contents


def test_upload_cache_uses_pdf_sha256_and_indexes_each_document(tmp_path, monkeypatch):
    registry = DocumentRegistry(upload_dir=tmp_path)
    original_parser = registry.parser.parse_document
    parse_calls = 0

    def count_parse_calls(file_path, document_id):
        nonlocal parse_calls
        parse_calls += 1
        return original_parser(file_path, document_id)

    registry.parser.parse_document = count_parse_calls
    monkeypatch.setattr(documents, "get_registry", lambda: registry)

    original_pdf = make_pdf("Same exact PDF content")
    changed_pdf = make_pdf("Other PDF content here!")
    assert len(original_pdf) == len(changed_pdf)

    with TestClient(app) as client:
        first = client.post(
            "/api/v1/documents",
            files={"file": ("original.pdf", io.BytesIO(original_pdf), "application/pdf")},
        )
        assert first.status_code == 201
        first_document = first.json()
        assert first_document["processing_status"] == "ready"
        assert registry.retriever.evidence_by_doc[first_document["document_id"]]
        assert parse_calls == 1

        identical = client.post(
            "/api/v1/documents",
            files={"file": ("renamed-copy.pdf", io.BytesIO(original_pdf), "application/pdf")},
        )
        assert identical.status_code == 201
        identical_document = identical.json()
        assert identical_document["document_id"] != first_document["document_id"]
        assert identical_document["filename"] == "renamed-copy.pdf"
        assert registry.retriever.evidence_by_doc[identical_document["document_id"]]
        assert all(
            item.document_id == identical_document["document_id"]
            for item in registry.get_evidence(identical_document["document_id"])
        )
        assert parse_calls == 1

        different = client.post(
            "/api/v1/documents",
            files={"file": ("original.pdf", io.BytesIO(changed_pdf), "application/pdf")},
        )
        assert different.status_code == 201
        assert different.json()["content_hash"] != first_document["content_hash"]
        assert parse_calls == 2
        assert len(list((tmp_path / ".cache").glob("*.json.gz"))) == 2
