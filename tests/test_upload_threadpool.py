from concurrent.futures import ThreadPoolExecutor
from threading import Event, get_ident

from fastapi.testclient import TestClient

from backend.app.api.routes import documents
from backend.app.main import app
from backend.app.pipeline.registry import DocumentRegistry
from tests.test_upload_cache import make_pdf


def test_health_responds_during_registration_and_temp_survives(tmp_path, monkeypatch):
    registry = DocumentRegistry(upload_dir=tmp_path)
    original = registry.register_file
    entered, release = Event(), Event()
    paths = []
    worker_threads = []

    def blocked_registration(path, filename):
        paths.append(path)
        worker_threads.append(get_ident())
        entered.set()
        assert release.wait(10)
        assert path.is_file()
        return original(path, filename)

    monkeypatch.setattr(registry, 'register_file', blocked_registration)
    monkeypatch.setattr(documents, 'get_registry', lambda: registry)
    with TestClient(app) as client, ThreadPoolExecutor(max_workers=2) as pool:
        loop_thread = client.portal.call(get_ident)
        upload = pool.submit(client.post, '/api/v1/documents',
                             files={'file': ('report.pdf', make_pdf('Upload test'), 'application/pdf')})
        try:
            assert entered.wait(5)
            health = pool.submit(client.get, '/api/v1/health')
            assert health.result(timeout=2).status_code == 200
            assert not upload.done()
            assert paths[0].is_file()
            assert worker_threads[0] != loop_thread
        finally:
            release.set()
        response = upload.result(timeout=10)
        assert response.status_code == 201
        assert response.json()['processing_status'] == 'ready'
        assert registry.retriever.evidence_by_doc[response.json()['document_id']]
        assert not paths[0].exists()


def test_registrations_are_serialized(tmp_path, monkeypatch):
    registry = DocumentRegistry(upload_dir=tmp_path)
    entered, release, second_entered = Event(), Event(), Event()
    original = registry.parser.parse_document
    def parse(path, document_id):
        if not entered.is_set():
            entered.set()
            assert release.wait(10)
        else:
            second_entered.set()
        return original(path, document_id)
    monkeypatch.setattr(registry.parser, 'parse_document', parse)
    first_pdf, second_pdf = tmp_path / 'first.pdf', tmp_path / 'second.pdf'
    first_pdf.write_bytes(make_pdf('First report'))
    second_pdf.write_bytes(make_pdf('Second report'))
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(registry.register_file, first_pdf, 'first.pdf')
        assert entered.wait(5)
        second = pool.submit(registry.register_file, second_pdf, 'second.pdf')
        try:
            assert not second_entered.wait(0.3)
        finally:
            release.set()
        a, b = first.result(timeout=10), second.result(timeout=10)
    assert a.document_id != b.document_id
    assert len(registry.list_documents()) == 2

