import gzip
import hashlib
import json
import logging
import shutil
from pathlib import Path
from backend.app.core.config import get_settings
from backend.app.pipeline.parser import PyMuPDFDocumentParser
from backend.app.pipeline.retriever import HybridEvidenceRetriever
from backend.app.schemas.evidence import (
    DocumentItem,
    EvidenceItem,
    PageProvenance,
    TableItem,
)

logger = logging.getLogger(__name__)

class DocumentRegistry:
    """
    Central in-memory and disk registry storing processed documents,
    page provenances, structured tables, evidence items, and hybrid indexes.
    """

    def __init__(self, upload_dir: str | Path | None = None):
        settings = get_settings()
        self.upload_dir = Path(upload_dir or settings.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        self.documents: dict[str, DocumentItem] = {}
        self.provenances: dict[str, list[PageProvenance]] = {}
        self.evidence: dict[str, list[EvidenceItem]] = {}
        self.tables: dict[str, list[TableItem]] = {}
        self.file_paths: dict[str, Path] = {}

        self.parser = PyMuPDFDocumentParser()
        self.retriever = HybridEvidenceRetriever()

    def register_file(self, file_path: Path, filename: str, doc_id: str | None = None) -> DocumentItem:
        if not file_path.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")

        document_id = doc_id or f"doc_{len(self.documents) + 1}"
        destination = self.upload_dir / f"{document_id}_{filename}"
        shutil.copy2(file_path, destination)
        self.file_paths[document_id] = destination

        # Check disk cache
        cache_dir = self.upload_dir / ".cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        content_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        cache_file = cache_dir / f"{content_hash}.json.gz"

        if cache_file.exists():
            try:
                with gzip.open(cache_file, "rt", encoding="utf-8") as f:
                    cache_data = json.load(f)
                doc_item = DocumentItem(**cache_data["doc_item"])
                cached_document_id = doc_item.document_id
                doc_item.document_id = document_id
                doc_item.filename = filename

                def rebind_id(value: str | None) -> str | None:
                    return value.replace(cached_document_id, document_id) if value else value

                page_provs = [
                    PageProvenance(**{**p, "document_id": document_id})
                    for p in cache_data["page_provs"]
                ]
                evidence_items = [
                    EvidenceItem(**{
                        **e,
                        "document_id": document_id,
                        "evidence_id": rebind_id(e.get("evidence_id")),
                        "parent_id": rebind_id(e.get("parent_id")),
                        "metadata": {
                            key: rebind_id(value) if isinstance(value, str) else value
                            for key, value in e.get("metadata", {}).items()
                        },
                    })
                    for e in cache_data["evidence_items"]
                ]
                table_items = [
                    TableItem(**{
                        **t,
                        "document_id": document_id,
                        "table_id": rebind_id(t.get("table_id")),
                    })
                    for t in cache_data["table_items"]
                ]
            except Exception:
                doc_item, page_provs, evidence_items, table_items = self.parser.parse_document(
                    destination, document_id
                )
                with gzip.open(cache_file, "wt", encoding="utf-8") as f:
                    json.dump(
                        {
                            "doc_item": doc_item.model_dump(),
                            "page_provs": [p.model_dump() for p in page_provs],
                            "evidence_items": [e.model_dump() for e in evidence_items],
                            "table_items": [t.model_dump() for t in table_items],
                        },
                        f,
                    )
        else:
            # Parse document
            logger.info(f"[PIPELINE] Parsing started: doc_id={document_id}, filename={filename}")
            try:
                doc_item, page_provs, evidence_items, table_items = self.parser.parse_document(
                    destination, document_id
                )
            except Exception as e:
                logger.exception(f"[PIPELINE] Parsing failed: doc_id={document_id}")
                raise
            logger.info(
                f"[PIPELINE] Parsing completed: doc_id={document_id}, page_count={doc_item.page_count}"
            )
            try:
                with gzip.open(cache_file, "wt", encoding="utf-8") as f:
                    json.dump(
                        {
                            "doc_item": doc_item.model_dump(),
                            "page_provs": [p.model_dump() for p in page_provs],
                            "evidence_items": [e.model_dump() for e in evidence_items],
                            "table_items": [t.model_dump() for t in table_items],
                        },
                        f,
                    )
            except Exception:
                pass

        # Store in registry
        self.documents[document_id] = doc_item
        self.provenances[document_id] = page_provs
        self.evidence[document_id] = evidence_items
        self.tables[document_id] = table_items

        # Index in hybrid retriever
        try:
            self.retriever.index_document(document_id, evidence_items, table_items)
            logger.info(f"[PIPELINE] Indexing completed: doc_id={document_id}")
        except Exception as e:
            logger.exception(f"[PIPELINE] Indexing failed: doc_id={document_id}")
            raise

        return doc_item

    def get_document(self, document_id: str) -> DocumentItem | None:
        return self.documents.get(document_id)

    def list_documents(self) -> list[DocumentItem]:
        return list(self.documents.values())

    def get_evidence(self, document_id: str) -> list[EvidenceItem]:
        return self.evidence.get(document_id, [])

    def get_tables(self, document_id: str) -> list[TableItem]:
        return self.tables.get(document_id, [])

    def get_page_provenances(self, document_id: str) -> list[PageProvenance]:
        return self.provenances.get(document_id, [])

    def get_pdf_path(self, document_id: str) -> Path | None:
        return self.file_paths.get(document_id)


_global_registry: DocumentRegistry | None = None

def get_registry() -> DocumentRegistry:
    global _global_registry
    if _global_registry is None:
        _global_registry = DocumentRegistry()
    return _global_registry

