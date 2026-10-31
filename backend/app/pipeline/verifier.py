from backend.app.schemas.evidence import EvidenceItem
from backend.app.schemas.question import (
    AnswerStatus,
    CalculationRecord,
    CitationItem,
    QuestionClassification,
    VerificationCheck,
)

class EvidenceVerifier:
    """
    Verifies that claims, citations, numbers, units, and periods are strictly grounded
    in source evidence, enforcing honest abstention when evidence is unsupported.
    """

    def verify(
        self,
        question: str,
        classification: QuestionClassification,
        retrieved_evidence: list[EvidenceItem],
        candidate_answer: str | None,
        calculation: CalculationRecord | None = None,
        citations: list[CitationItem] | None = None,
    ) -> tuple[AnswerStatus, list[VerificationCheck], list[str]]:
        checks: list[VerificationCheck] = []
        warnings: list[str] = []

        # Check 1: Evidence Existence
        if not retrieved_evidence:
            checks.append(
                VerificationCheck(
                    name="evidence_retrieval",
                    passed=False,
                    details="No relevant evidence was retrieved from the document.",
                )
            )
            return "not_found", checks, ["No supporting evidence found in document."]

        checks.append(
            VerificationCheck(
                name="evidence_retrieval",
                passed=True,
                details=f"Retrieved {len(retrieved_evidence)} candidate evidence items.",
            )
        )

        all_evidence_text = " ".join([e.text for e in retrieved_evidence]).lower()

        # Check 2: Target Period Verification
        period_passed = True
        missing_periods = []
        for period in classification.target_periods:
            if period.lower() not in all_evidence_text:
                period_passed = False
                missing_periods.append(period)

        if not period_passed:
            checks.append(
                VerificationCheck(
                    name="period_grounding",
                    passed=False,
                    details=f"Requested period(s) {missing_periods} not found in retrieved evidence.",
                )
            )
            return "not_found", checks, [f"Document does not report data for period(s): {', '.join(missing_periods)}."]
        else:
            checks.append(
                VerificationCheck(
                    name="period_grounding",
                    passed=True,
                    details="Target periods verified in source evidence.",
                )
            )

        # Check 3: Target Entity Verification
        if classification.target_entities:
            missing_entities = []
            for ent in classification.target_entities:
                # Every word in the target entity must be present in retrieved evidence (supporting plural/singular forms)
                words = [w.lower() for w in ent.split() if len(w) > 2]
                unmatched_words = []
                for w in words:
                    matched = (
                        w in all_evidence_text
                        or (w.endswith("s") and w[:-1] in all_evidence_text)
                        or (w.endswith("es") and w[:-2] in all_evidence_text)
                        or (w.endswith("ies") and (w[:-3] + "y") in all_evidence_text)
                    )
                    if not matched:
                        unmatched_words.append(w)

                if unmatched_words:
                    missing_entities.append(ent)

            if missing_entities:
                checks.append(
                    VerificationCheck(
                        name="entity_grounding",
                        passed=False,
                        details=f"Target entity term(s) {missing_entities} not found in retrieved evidence.",
                    )
                )
                return "not_found", checks, [f"Document contains no reference to: {', '.join(missing_entities)}."]
            else:
                checks.append(
                    VerificationCheck(
                        name="entity_grounding",
                        passed=True,
                        details="Target entities verified in source evidence.",
                    )
                )

        # Check 4: Deterministic Arithmetic Verification
        if classification.requires_arithmetic:
            if calculation is None:
                checks.append(
                    VerificationCheck(
                        name="deterministic_arithmetic",
                        passed=False,
                        details="Question required arithmetic, but no deterministic calculation was produced.",
                    )
                )
                warnings.append("Arithmetic was required but not performed deterministically.")
            else:
                checks.append(
                    VerificationCheck(
                        name="deterministic_arithmetic",
                        passed=True,
                        details=f"Arithmetic formula {calculation.formula} evaluated to {calculation.result} {calculation.unit or ''}.",
                    )
                )

        # Check 5: Citation & Bounding Box Provenance
        if citations:
            citations_with_valid_bbox = [c for c in citations if c.bbox is not None]
            all_valid_bbox = len(citations_with_valid_bbox) == len(citations)
            checks.append(
                VerificationCheck(
                    name="citation_provenance",
                    passed=all_valid_bbox,
                    details=f"{len(citations_with_valid_bbox)}/{len(citations)} citations have valid normalized bounding box coordinates.",
                )
            )
        else:
            checks.append(
                VerificationCheck(
                    name="citation_provenance",
                    passed=False,
                    details="No citations provided for generated answer.",
                )
            )
            warnings.append("Answer lacks explicit citations.")

        # Final Status determination
        has_critical_failure = any(not c.passed and c.name in ("evidence_retrieval", "period_grounding", "entity_grounding") for c in checks)
        status: AnswerStatus = "not_found" if has_critical_failure else "answered"

        return status, checks, warnings
