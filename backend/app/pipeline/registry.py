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

        # Parse document
        doc_item, page_provs, evidence_items, table_items = self.parser.parse_document(
            destination, document_id
        )

        # Store in registry
        self.documents[document_id] = doc_item
        self.provenances[document_id] = page_provs
        self.evidence[document_id] = evidence_items
        self.tables[document_id] = table_items

        # Index in hybrid retriever
        self.retriever.index_document(document_id, evidence_items, table_items)

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

