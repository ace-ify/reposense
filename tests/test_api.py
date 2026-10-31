from pathlib import Path
from fastapi.testclient import TestClient
import pymupdf
import pytest

from backend.app.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_samples():
    # Calling client context triggers lifespan
    with TestClient(app) as c:
        yield c

def test_health_endpoints() -> None:
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}

    res_v1 = client.get("/api/v1/health")
    assert res_v1.status_code == 200
    assert res_v1.json() == {"status": "ok"}

def test_samples_endpoint() -> None:
    res = client.get("/api/v1/samples")
    assert res.status_code == 200
    samples = res.json()
    assert len(samples) >= 2
    sample = samples[0]
    assert sample["document_id"] == "doc_sample_energy_2024"
    assert len(sample["sample_questions"]) >= 4

def test_evaluation_endpoint() -> None:
    res = client.get("/api/v1/evaluation")
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data
    assert "cases" in data
    assert data["summary"]["total_cases"] >= 8
    assert data["summary"]["accuracy_percentage"] >= 80.0

def test_documents_and_questions_flow() -> None:
    # 1. Ask lookup question on sample document
    lookup_payload = {
        "question": "What were total Solar PV investments in 2023?",
        "document_ids": ["doc_sample_energy_2024"],
    }
    res = client.post("/api/v1/questions", json=lookup_payload)
    assert res.status_code == 200
    ans = res.json()
    assert ans["status"] == "answered"
    assert len(ans["citations"]) > 0
    assert ans["citations"][0]["bbox"] is not None
    assert any(c["pdf_page_index"] == 1 for c in ans["citations"]) or any("260" in str(c.get("snippet")) for c in ans["citations"])

    # 2. Ask arithmetic percentage change question
    calc_payload = {
        "question": "What was the percentage change in Solar PV investments between 2022 and 2023?",
        "document_ids": ["doc_sample_energy_2024"],
    }
    res_calc = client.post("/api/v1/questions", json=calc_payload)
    assert res_calc.status_code == 200
    ans_calc = res_calc.json()
    assert ans_calc["status"] == "answered"
    assert ans_calc["calculation"] is not None
    assert ans_calc["calculation"]["operation"] == "percentage_change"
    assert round(ans_calc["calculation"]["result"], 1) == 23.8

    # 3. Ask unanswerable question to test honest abstention
    abstain_payload = {
        "question": "What was the clean energy investment projection for 2045?",
        "document_ids": ["doc_sample_energy_2024"],
    }
    res_abstain = client.post("/api/v1/questions", json=abstain_payload)
    assert res_abstain.status_code == 200
    ans_abstain = res_abstain.json()
    assert ans_abstain["status"] == "not_found"
    assert any("2045" in w for w in ans_abstain["warnings"])
