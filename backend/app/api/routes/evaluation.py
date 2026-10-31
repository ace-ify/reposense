import time
from typing import Any
from fastapi import APIRouter
from backend.app.pipeline.engine import ReportIntelligenceEngine
from backend.app.pipeline.registry import get_registry
from backend.app.pipeline.sample_data import seed_sample_documents
from backend.app.schemas.question import QuestionRequest

router = APIRouter(prefix="/evaluation", tags=["evaluation"])

BENCHMARK_SUITE: list[dict[str, Any]] = [
    {
        "id": "tc_01",
        "family": "Clean Energy",
        "category": "Direct Lookup",
        "question": "What were total Solar PV investments in 2023?",
        "doc_id": "doc_sample_energy_2024",
        "expected_status": "answered",
        "expected_value_str": "260",
        "must_have_bbox": True,
    },
    {
        "id": "tc_02",
        "family": "Clean Energy",
        "category": "Deterministic Arithmetic",
        "question": "What was the percentage change in Solar PV investments between 2022 and 2023?",
        "doc_id": "doc_sample_energy_2024",
        "expected_status": "answered",
        "expected_math_op": "percentage_change",
        "expected_result": 23.81,
        "must_have_bbox": True,
    },
    {
        "id": "tc_03",
        "family": "Clean Energy",
        "category": "Multi-Entity Difference",
        "question": "What was the difference between Power Grid & Storage investment and Wind Power investment in 2023?",
        "doc_id": "doc_sample_energy_2024",
        "expected_status": "answered",
        "expected_math_op": "difference",
        "expected_result": 155.0,
        "must_have_bbox": True,
    },
    {
        "id": "tc_04",
        "family": "Clean Energy",
        "category": "Honest Abstention (Future Year)",
        "question": "What was the projected clean energy revenue in 2045?",
        "doc_id": "doc_sample_energy_2024",
        "expected_status": "not_found",
        "must_have_bbox": False,
    },
    {
        "id": "tc_05",
        "family": "Clean Energy",
        "category": "Honest Abstention (Missing Entity)",
        "question": "What was the nuclear fission subsidy in 2023?",
        "doc_id": "doc_sample_energy_2024",
        "expected_status": "not_found",
        "must_have_bbox": False,
    },
    {
        "id": "tc_06",
        "family": "Federal Fiscal",
        "category": "Direct Lookup",
        "question": "What were total Individual Income Taxes in 2023?",
        "doc_id": "doc_sample_fiscal_2023",
        "expected_status": "answered",
        "expected_value_str": "2,176",
        "must_have_bbox": True,
    },
    {
        "id": "tc_07",
        "family": "Federal Fiscal",
        "category": "Deterministic Arithmetic",
        "question": "What was the percentage change in Individual Income Taxes between 2022 and 2023?",
        "doc_id": "doc_sample_fiscal_2023",
        "expected_status": "answered",
        "expected_math_op": "percentage_change",
        "expected_result": -17.33,
        "must_have_bbox": True,
    },
    {
        "id": "tc_08",
        "family": "Federal Fiscal",
        "category": "Multi-Entity Difference",
        "question": "What was the difference between Individual Income Taxes and Corporation Income Taxes in 2023?",
        "doc_id": "doc_sample_fiscal_2023",
        "expected_status": "answered",
        "expected_math_op": "difference",
        "expected_result": 1756.0,
        "must_have_bbox": True,
    },
    {
        "id": "tc_09",
        "family": "Federal Fiscal",
        "category": "Honest Abstention (Future Year)",
        "question": "What was the international tariff revenue collected in 2030?",
        "doc_id": "doc_sample_fiscal_2023",
        "expected_status": "not_found",
        "must_have_bbox": False,
    },
]

def execute_benchmark() -> dict[str, Any]:
    registry = get_registry()
    seed_sample_documents(registry)
    engine = ReportIntelligenceEngine(registry)

    results: list[dict[str, Any]] = []
    latencies: list[float] = []
    passed_count = 0
    math_count = 0
    math_passed = 0
    abstain_count = 0
    abstain_passed = 0
    mrr_sum = 0.0

    for tc in BENCHMARK_SUITE:
        t0 = time.time()
        ans = engine.answer_question(
            QuestionRequest(question=tc["question"], document_ids=[tc["doc_id"]])
        )
        latency_ms = round((time.time() - t0) * 1000, 1)
        latencies.append(latency_ms)

        passed = True
        notes: list[str] = []

        # 1. Status Check
        if ans.status != tc["expected_status"]:
            passed = False
            notes.append(f"Status mismatch: expected {tc['expected_status']}, got {ans.status}")

        # 2. Lookup check
        if "expected_value_str" in tc:
            target_val = tc["expected_value_str"].replace(",", "")
            found_val = target_val in str(ans.answer or "").replace(",", "") or any(
                target_val in str(c.snippet or "").replace(",", "") for c in ans.citations
            )
            if not found_val:
                passed = False
                notes.append(f"Expected value '{tc['expected_value_str']}' not found in answer or citations")

        # 3. Arithmetic check
        if "expected_math_op" in tc:
            math_count += 1
            if not ans.calculation or ans.calculation.operation != tc["expected_math_op"]:
                passed = False
                notes.append(f"Math op mismatch: expected {tc['expected_math_op']}")
            elif "expected_result" in tc:
                diff = abs(float(ans.calculation.result) - tc["expected_result"])
                if diff > 0.5:
                    passed = False
                    notes.append(f"Result mismatch: expected ~{tc['expected_result']}, got {ans.calculation.result}")
                else:
                    math_passed += 1

        # 4. Abstention check
        if tc["expected_status"] == "not_found":
            abstain_count += 1
            if ans.status == "not_found":
                abstain_passed += 1

        # 5. Citation Bounding Box Check
        if tc["must_have_bbox"]:
            has_bbox = any(c.bbox is not None for c in ans.citations)
            if not has_bbox:
                passed = False
                notes.append("Citation lacks bounding box")

        if passed:
            passed_count += 1
            mrr_sum += 1.0
        elif ans.citations:
            mrr_sum += 0.5

        results.append({
            "id": tc["id"],
            "family": tc["family"],
            "category": tc["category"],
            "question": tc["question"],
            "status": ans.status,
            "passed": passed,
            "latency_ms": latency_ms,
            "calculation": ans.calculation.model_dump() if ans.calculation else None,
            "citations_count": len(ans.citations),
            "notes": notes,
        })

    total = len(BENCHMARK_SUITE)
    accuracy_pct = round((passed_count / total) * 100, 1)
    avg_latency = round(sum(latencies) / len(latencies), 1)
    math_acc = round((math_passed / max(1, math_count)) * 100, 1)
    abstain_prec = round((abstain_passed / max(1, abstain_count)) * 100, 1)
    mrr = round(mrr_sum / total, 2)

    return {
        "summary": {
            "total_cases": total,
            "passed_cases": passed_count,
            "accuracy_percentage": accuracy_pct,
            "retrieval_mrr": mrr,
            "arithmetic_accuracy": math_acc,
            "abstention_precision": abstain_prec,
            "avg_latency_ms": avg_latency,
        },
        "cases": results,
    }

@router.get("", response_model=dict[str, Any])
def get_benchmark_scorecard() -> dict[str, Any]:
    return execute_benchmark()

@router.post("/run", response_model=dict[str, Any])
def run_benchmark_suite() -> dict[str, Any]:
    return execute_benchmark()
