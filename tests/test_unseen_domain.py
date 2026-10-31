from pathlib import Path
import pymupdf
import pytest

from backend.app.pipeline.engine import ReportIntelligenceEngine
from backend.app.pipeline.registry import DocumentRegistry
from backend.app.schemas.question import QuestionRequest

def test_unseen_healthcare_domain_report(tmp_path: Path) -> None:
    """
    Validates that the Report Intelligence Assistant generalizes 100% to completely
    unseen document families (e.g. Oncology Clinical Trial Report) with zero hardcoded assumptions.
    """
    pdf_path = tmp_path / "global_oncology_clinical_trials_2023.pdf"
    doc = pymupdf.open()

    # Page 1: Clinical Narrative
    p1 = doc.new_page(width=600, height=800)
    p1.insert_text((50, 50), "GLOBAL ONCOLOGY PHASE-3 CLINICAL TRIAL OUTCOMES", fontsize=14)
    p1.insert_text(
        (50, 90),
        "This multi-center randomized clinical study evaluated patient progression-free survival "
        "and therapeutic response rates across advanced melanoma cohorts between 2021 and 2023.",
        fontsize=10,
    )

    # Page 2: Structured Clinical Table
    p2 = doc.new_page(width=600, height=800)
    p2.insert_text((50, 50), "Table 1. Progression-Free Survival Rates by Therapeutic Agent (Percent)", fontsize=11)

    t_rect = pymupdf.Rect(50, 70, 550, 200)
    p2.draw_rect(t_rect, color=(0, 0, 0), width=1)
    p2.draw_line((50, 100), (550, 100), color=(0, 0, 0), width=1)
    p2.draw_line((250, 70), (250, 200), color=(0, 0, 0), width=0.8)
    p2.draw_line((350, 70), (350, 200), color=(0, 0, 0), width=0.8)
    p2.draw_line((450, 70), (450, 200), color=(0, 0, 0), width=0.8)

    for y in [130, 160]:
        p2.draw_line((50, y), (550, y), color=(0.7, 0.7, 0.7), width=0.5)

    p2.insert_text((60, 90), "Therapeutic Agent", fontsize=9)
    p2.insert_text((260, 90), "2021 (%)", fontsize=9)
    p2.insert_text((360, 90), "2022 (%)", fontsize=9)
    p2.insert_text((460, 90), "2023 (%)", fontsize=9)

    # Row 1
    p2.insert_text((60, 120), "Pembrolizumab", fontsize=9)
    p2.insert_text((260, 120), "45", fontsize=9)
    p2.insert_text((360, 120), "54", fontsize=9)
    p2.insert_text((460, 120), "62", fontsize=9)

    # Row 2
    p2.insert_text((60, 150), "Nivolumab", fontsize=9)
    p2.insert_text((260, 150), "40", fontsize=9)
    p2.insert_text((360, 150), "48", fontsize=9)
    p2.insert_text((460, 150), "52", fontsize=9)

    # Footnote
    p2.insert_text((50, 220), "* Note: Survival rates measured at 24-month patient follow-up. Source: ASCO.", fontsize=8)

    doc.save(pdf_path)
    doc.close()

    # Ingest into registry
    reg = DocumentRegistry(upload_dir=tmp_path / "uploads")
    reg.register_file(pdf_path, "oncology_report.pdf", doc_id="doc_oncology_unseen")
    engine = ReportIntelligenceEngine(reg)

    # 1. Lookup Question on unseen domain
    ans_lookup = engine.answer_question(
        QuestionRequest(
            question="What was the survival rate of Pembrolizumab in 2023?",
            document_ids=["doc_oncology_unseen"],
        )
    )
    assert ans_lookup.status == "answered"
    assert len(ans_lookup.citations) > 0
    assert any("62" in str(c.snippet or "") for c in ans_lookup.citations) or "62" in str(ans_lookup.answer or "")
    assert ans_lookup.citations[0].bbox is not None

    # 2. Deterministic Arithmetic (Percentage change from 2022 to 2023 for Pembrolizumab)
    # (62 - 54) / 54 * 100 = 14.81%
    ans_calc = engine.answer_question(
        QuestionRequest(
            question="What was the percentage change in Pembrolizumab survival rate between 2022 and 2023?",
            document_ids=["doc_oncology_unseen"],
        )
    )
    assert ans_calc.status == "answered"
    assert ans_calc.calculation is not None
    assert ans_calc.calculation.operation == "percentage_change"
    assert round(ans_calc.calculation.result, 1) == 14.8

    # 3. Multi-Entity Difference (Pembrolizumab vs Nivolumab in 2023: 62 - 52 = 10)
    ans_diff = engine.answer_question(
        QuestionRequest(
            question="What was the difference between Pembrolizumab and Nivolumab in 2023?",
            document_ids=["doc_oncology_unseen"],
        )
    )
    assert ans_diff.status == "answered"
    assert ans_diff.calculation is not None
    assert ans_diff.calculation.operation == "difference"
    assert round(ans_diff.calculation.result, 1) == 10.0

    # 4. Honest Abstention on missing drug
    ans_abstain = engine.answer_question(
        QuestionRequest(
            question="What was the survival rate of Aspirin in 2023?",
            document_ids=["doc_oncology_unseen"],
        )
    )
    assert ans_abstain.status == "not_found"

