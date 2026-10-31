from abc import ABC, abstractmethod
from pathlib import Path
from typing import Sequence
from backend.app.schemas.evidence import EvidenceItem

class DocumentParser(ABC):
    @abstractmethod
    def parse(self, file_path: Path, document_id: str) -> Sequence[EvidenceItem]:
        """Extract evidence while preserving page and coordinate provenance."""
        raise NotImplementedError

class EvidenceRetriever(ABC):
    @abstractmethod
    def retrieve(self, question: str, document_ids: list[str]) -> Sequence[EvidenceItem]:
        """Return ranked evidence candidates with provenance."""
        raise NotImplementedError
