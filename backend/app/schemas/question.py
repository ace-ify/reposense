from typing import Any, Literal
from pydantic import BaseModel, Field
from backend.app.schemas.evidence import BoundingBox

AnswerStatus = Literal["answered", "not_found", "ambiguous", "conflicting"]
QuestionIntent = Literal[
    "lookup",
    "comparison",
    "aggregation",
    "trend",
    "definition",
    "multi_hop",
    "unanswerable",
    "ambiguous"
]

class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    document_ids: list[str] = Field(min_length=1)

class CalculationRecord(BaseModel):
    operation: str
    formula: str
    raw_values: dict[str, Any] = Field(default_factory=dict)
    normalized_values: dict[str, Any] = Field(default_factory=dict)
    result: float | int | str
    unit: str | None = None
    audit_trail: str | None = None

class ClaimItem(BaseModel):
    text: str
    evidence_ids: list[str] = Field(default_factory=list)
    calculation: CalculationRecord | None = None

class CitationItem(BaseModel):
    document_id: str
    pdf_page_index: int = Field(ge=0)
    printed_page_number: int | str | None = None
    evidence_id: str
    bbox: BoundingBox | None = None
    snippet: str | None = None
    kind: str | None = None

class VerificationCheck(BaseModel):
    name: str
    passed: bool
    details: str

class PipelineTraceStep(BaseModel):
    stage: str
    description: str
    timestamp_ms: float = 0.0
    data: dict[str, Any] = Field(default_factory=dict)

class QuestionClassification(BaseModel):
    intent: QuestionIntent
    target_entities: list[str] = Field(default_factory=list)
    target_metrics: list[str] = Field(default_factory=list)
    target_periods: list[str] = Field(default_factory=list)
    requires_arithmetic: bool = False
    confidence: float = 1.0
    rationale: str | None = None

class AnswerResponse(BaseModel):
    status: AnswerStatus
    answer: str | None = None
    claims: list[ClaimItem] = Field(default_factory=list)
    citations: list[CitationItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    classification: QuestionClassification | None = None
    calculation: CalculationRecord | None = None
    verification_checks: list[VerificationCheck] = Field(default_factory=list)
    pipeline_trace: list[PipelineTraceStep] = Field(default_factory=list)
