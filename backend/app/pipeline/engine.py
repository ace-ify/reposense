import time
from backend.app.pipeline.classifier import QuestionClassifier
from backend.app.pipeline.reasoner import AnswerReasoner
from backend.app.pipeline.registry import DocumentRegistry, get_registry
from backend.app.pipeline.verifier import EvidenceVerifier
from backend.app.schemas.question import (
    AnswerResponse,
    PipelineTraceStep,
    QuestionRequest,
)

class ReportIntelligenceEngine:
    """
    Coordinates end-to-end question answering pipeline:
    Routing -> Hybrid Retrieval -> Deterministic Reasoning -> Verification -> Verified Response.
    """

    def __init__(self, registry: DocumentRegistry | None = None):
        self.registry = registry or get_registry()
        self.classifier = QuestionClassifier()
        self.reasoner = AnswerReasoner()
        self.verifier = EvidenceVerifier()

    def answer_question(self, request: QuestionRequest) -> AnswerResponse:
        start_time = time.time()
        trace: list[PipelineTraceStep] = []

        def record_step(stage: str, desc: str, data: dict | None = None):
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            trace.append(
                PipelineTraceStep(
                    stage=stage,
                    description=desc,
                    timestamp_ms=elapsed_ms,
                    data=data or {},
                )
            )

        # Step 1: Question Routing & Classification
        classification = self.classifier.classify(request.question)
        record_step(
            stage="classification",
            desc=f"Intent: {classification.intent.upper()} | Arithmetic required: {classification.requires_arithmetic}",
            data={
                "intent": classification.intent,
                "entities": classification.target_entities,
                "metrics": classification.target_metrics,
                "periods": classification.target_periods,
                "requires_arithmetic": classification.requires_arithmetic,
            },
        )

        # Step 2: Hybrid Retrieval (BM25 + Semantic + Table Expansion)
        retrieved_evidence = list(
            self.registry.retriever.retrieve(
                question=request.question,
                document_ids=request.document_ids,
                top_k=8,
            )
        )
        record_step(
            stage="retrieval",
            desc=f"Retrieved {len(retrieved_evidence)} candidate evidence items across {len(request.document_ids)} document(s)",
            data={
                "candidate_count": len(retrieved_evidence),
                "evidence_ids": [e.evidence_id for e in retrieved_evidence],
            },
        )

        # Step 3: Reasoning and Deterministic Calculation
        answer_text, claims, citations, calculation = self.reasoner.reason_and_synthesize(
            question=request.question,
            classification=classification,
            evidence=retrieved_evidence,
        )
        record_step(
            stage="reasoning",
            desc=f"Synthesized candidate answer with {len(claims)} claim(s) and {len(citations)} citation(s)",
            data={
                "calculation": calculation.model_dump() if calculation else None,
                "citation_count": len(citations),
            },
        )

        # Step 4: Strict Evidence Verification and Abstention
        status, checks, warnings = self.verifier.verify(
            question=request.question,
            classification=classification,
            retrieved_evidence=retrieved_evidence,
            candidate_answer=answer_text,
            calculation=calculation,
            citations=citations,
        )
        record_step(
            stage="verification",
            desc=f"Verification status: {status.upper()} ({sum(1 for c in checks if c.passed)}/{len(checks)} checks passed)",
            data={
                "status": status,
                "passed_checks": [c.name for c in checks if c.passed],
                "failed_checks": [c.name for c in checks if not c.passed],
            },
        )

        # If abstaining, adjust answer text transparently
        final_answer = answer_text
        if status == "not_found":
            reasons = "; ".join(warnings) if warnings else "Evidence missing from document."
            final_answer = f"UNANSWERED (Evidence Not Found): {reasons}"
        elif status == "ambiguous":
            final_answer = f"AMBIGUOUS: Multiple conflicting definitions or insufficient specificity in query."

        return AnswerResponse(
            status=status,
            answer=final_answer,
            claims=claims,
            citations=citations,
            warnings=warnings,
            classification=classification,
            calculation=calculation,
            verification_checks=checks,
            pipeline_trace=trace,
        )

