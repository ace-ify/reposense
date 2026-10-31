from typing import Any
from fastapi import APIRouter
from backend.app.pipeline.registry import get_registry
from backend.app.pipeline.sample_data import seed_sample_documents

router = APIRouter(prefix="/samples", tags=["samples"])

@router.get("", response_model=list[dict[str, Any]])
def get_sample_reports() -> list[dict[str, Any]]:
    registry = get_registry()
    seed_sample_documents(registry)

    return [
        {
            "document_id": "doc_sample_energy_2024",
            "title": "Global Clean Energy & Investment Outlook 2024",
            "filename": "global_energy_outlook_2024.pdf",
            "description": "Comprehensive statistical report on global transition capital expenditure, technology breakdown, and grid investments.",
            "pages": 2,
            "sample_questions": [
                {
                    "category": "Table Lookup",
                    "label": "🎯 Table Lookup: Solar PV 2023",
                    "question": "What were total Solar PV investments in 2023?",
                    "intent": "lookup",
                    "expected_answer": "260 billion USD",
                },
                {
                    "category": "Deterministic Arithmetic",
                    "label": "🔢 Deterministic Math: Solar Growth 2022-2023",
                    "question": "What was the percentage change in Solar PV investments between 2022 and 2023?",
                    "intent": "comparison",
                    "expected_answer": "+23.81% (Deterministic Python calculation)",
                },
                {
                    "category": "Multi-Entity Difference",
                    "label": "⚖️ Comparison: Grid vs Wind in 2023",
                    "question": "What was the difference between Power Grid & Storage investment and Wind Power investment in 2023?",
                    "intent": "comparison",
                    "expected_answer": "Difference: 155.0 billion USD",
                },
                {
                    "category": "Honest Abstention",
                    "label": "🛡️ Abstention: Future Projection for 2045",
                    "question": "What was the projected clean energy revenue in 2045?",
                    "intent": "unanswerable",
                    "expected_answer": "Abstains: Report notes projections only extend through 2025.",
                },
            ],
        },
        {
            "document_id": "doc_sample_fiscal_2023",
            "title": "Federal Fiscal & Economic Performance Report FY2023",
            "filename": "federal_fiscal_report_fy2023.pdf",
            "description": "Annual US Treasury statistical report on federal revenue sources, outlays, public debt interest, and fiscal deficit.",
            "pages": 2,
            "sample_questions": [
                {
                    "category": "Table Lookup",
                    "label": "🎯 Table Lookup: Individual Income Taxes 2023",
                    "question": "What were total Individual Income Taxes in 2023?",
                    "intent": "lookup",
                    "expected_answer": "2,176 billion USD",
                },
                {
                    "category": "Deterministic Arithmetic",
                    "label": "🔢 Deterministic Math: Income Tax Change 2022-2023",
                    "question": "What was the percentage change in Individual Income Taxes between 2022 and 2023?",
                    "intent": "comparison",
                    "expected_answer": "-17.33% (Deterministic Python calculation)",
                },
                {
                    "category": "Multi-Entity Difference",
                    "label": "⚖️ Comparison: Income vs Corporate Taxes in 2023",
                    "question": "What was the difference between Individual Income Taxes and Corporation Income Taxes in 2023?",
                    "intent": "comparison",
                    "expected_answer": "Difference: 1,756 billion USD",
                },
                {
                    "category": "Honest Abstention",
                    "label": "🛡️ Abstention: Missing Tariff Receipts for 2030",
                    "question": "What was the international tariff revenue collected in 2030?",
                    "intent": "unanswerable",
                    "expected_answer": "Abstains: No data reported for 2030.",
                },
            ],
        },
    ]
