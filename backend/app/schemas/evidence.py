from typing import Any, Literal
from pydantic import BaseModel, Field

EvidenceKind = Literal["paragraph", "heading", "table", "table_cell", "chart", "caption", "footnote"]
ExtractionMethod = Literal["native_text", "ocr", "mixed"]
DocumentStatus = Literal["pending", "processing", "ready", "failed"]

class BoundingBox(BaseModel):
    x0: float
    y0: float
    x1: float
    y1: float
    coordinate_system: str = "normalized_0_1"

class PageProvenance(BaseModel):
    document_id: str
    pdf_page_index: int = Field(ge=0)
    printed_page_number: int | str | None = None
    page_width: float = 0.0
    page_height: float = 0.0
    rotation: int = 0
    extraction_method: ExtractionMethod = "native_text"
    warnings: list[str] = Field(default_factory=list)

class EvidenceItem(BaseModel):
    evidence_id: str
    document_id: str
    pdf_page_index: int = Field(ge=0)
    printed_page_number: int | str | None = None
    kind: EvidenceKind
    text: str
    normalized_text: str | None = None
    bbox: BoundingBox | None = None
    parent_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    extraction_confidence: float | None = Field(default=None, ge=0, le=1)
    warnings: list[str] = Field(default_factory=list)

class TableItem(BaseModel):
    table_id: str
    document_id: str
    pdf_page_index: int = Field(ge=0)
    printed_page_number: int | str | None = None
    title: str | None = None
    headers: list[list[str]] = Field(default_factory=list)
    rows: list[list[Any]] = Field(default_factory=list)
    units: dict[str, str] = Field(default_factory=dict)
    footnotes: list[str] = Field(default_factory=list)
    bbox: BoundingBox | None = None
    extraction_confidence: float | None = Field(default=None, ge=0, le=1)
    warnings: list[str] = Field(default_factory=list)

class DocumentItem(BaseModel):
    document_id: str
    filename: str
    content_hash: str
    page_count: int = 0
    processing_status: DocumentStatus = "pending"
    metadata: dict[str, Any] = Field(default_factory=dict)
