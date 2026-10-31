from pathlib import Path
from fastapi.testclient import TestClient
import pymupdf
import pytest

from backend.app.main import app

def test_judge_facing_api_flow():
    with TestClient(app) as test_client:
        # 1. Check OpenAPI schema
        openapi_res = test_client.get("/openapi.json")
        assert openapi_res.status_code == 200
        schema = openapi_res.json()
        paths = schema.get("paths", {})
        
        # Unversioned functional endpoints must NOT exist in Swagger
        assert "/documents" not in paths
        assert "/questions" not in paths
        assert "/samples" not in paths
        assert "/evaluation" not in paths
        
        # Versioned endpoints MUST exist
        assert "/api/v1/documents" in paths
        assert "/api/v1/questions" in paths
        assert "/api/v1/samples" in paths
        assert "/api/v1/evaluation" in paths
        assert "/api/v1/health" in paths
        assert "/health" in paths

        # 2. Evaluation endpoint transparency
        eval_res = test_client.get("/api/v1/evaluation")
        assert eval_res.status_code == 200
        eval_data = eval_res.json()
        assert eval_data.get("is_judge_evaluation") is False
        assert "demo" in eval_data.get("suite_type", "").lower()

        # 3. Non-existent document ID handling
        bad_req = {
            "question": "What was the total budget in 2023?",
            "document_ids": ["doc_nonexistent_xyz_999"]
        }
        res_404 = test_client.post("/api/v1/questions", json=bad_req)
        assert res_404.status_code == 404
        assert "not found" in res_404.json()["detail"].lower()

        # 4. Upload authentic PDF report
        pdf_doc = pymupdf.open()
        p1 = pdf_doc.new_page(width=595, height=842)
        p1.insert_text((50, 60), "STATE INFRASTRUCTURE AND LOGISTICS ANNUAL REPORT 2023", fontsize=13)
        p1.insert_text((50, 90), "Section 4. Highway Freight and Commercial Fleet Density", fontsize=11)
        
        t_rect = pymupdf.Rect(50, 110, 545, 230)
        p1.draw_rect(t_rect, color=(0, 0, 0), width=1)
        p1.draw_line((50, 140), (545, 140), color=(0, 0, 0), width=1)
        p1.draw_line((220, 110), (220, 230), color=(0, 0, 0), width=0.8)
        p1.draw_line((380, 110), (380, 230), color=(0, 0, 0), width=0.8)
        
        p1.insert_text((60, 130), "Logistics Corridor", fontsize=9)
        p1.insert_text((230, 130), "2022 Volume (MT)", fontsize=9)
        p1.insert_text((390, 130), "2023 Volume (MT)", fontsize=9)
        
        p1.insert_text((60, 160), "Western Coastal Highway", fontsize=9)
        p1.insert_text((230, 160), "48200", fontsize=9)
        p1.insert_text((390, 160), "56400", fontsize=9)
        
        p1.insert_text((60, 190), "Northern Freight Corridor", fontsize=9)
        p1.insert_text((230, 190), "31500", fontsize=9)
        p1.insert_text((390, 190), "38900", fontsize=9)
        
        pdf_bytes = pdf_doc.write()
        pdf_doc.close()

        upload_resp = test_client.post(
            "/api/v1/documents",
            files={"file": ("state_infrastructure_report_2023.pdf", pdf_bytes, "application/pdf")},
        )
        assert upload_resp.status_code == 201
        doc_data = upload_resp.json()
        doc_id = doc_data["document_id"]
        assert doc_id.startswith("doc_")
        assert "state_infrastructure_report_2023" in doc_data["filename"]
        assert doc_data["page_count"] == 1

        # 5. Ask question with explicit document_id
        q_payload = {
            "question": "What was the volume of Western Coastal Highway in 2023?",
            "document_ids": [doc_id]
        }
        q_res = test_client.post("/api/v1/questions", json=q_payload)
        assert q_res.status_code == 200
        ans = q_res.json()
        assert ans["status"] == "answered"
        assert "56400" in ans["answer"]
        assert len(ans["citations"]) > 0
        top_citation = ans["citations"][0]
        assert top_citation["document_id"] == doc_id
        assert top_citation["pdf_page_index"] == 0
        assert top_citation["bbox"] is not None
        assert "x0" in top_citation["bbox"]
        assert "56400" in top_citation["snippet"]

        # 6. Ask question with omitted document_ids (must isolate from seeded sample documents)
        q_omit_payload = {
            "question": "What was the volume of Northern Freight Corridor in 2023?",
            "document_ids": []
        }
        q_omit_res = test_client.post("/api/v1/questions", json=q_omit_payload)
        assert q_omit_res.status_code == 200
        ans_omit = q_omit_res.json()
        assert ans_omit["status"] == "answered"
        assert "38900" in ans_omit["answer"]
        assert ans_omit["citations"][0]["document_id"] == doc_id

        # 7. Ask unanswerable question
        q_abstain_payload = {
            "question": "How many submarines were commissioned in 2023?",
            "document_ids": [doc_id]
        }
        res_abstain = test_client.post("/api/v1/questions", json=q_abstain_payload)
        assert res_abstain.status_code == 200
        ans_abstain = res_abstain.json()
        assert ans_abstain["status"] == "not_found"
        assert ans_abstain["answer"] == "NOT_FOUND"
        assert len(ans_abstain["citations"]) == 0
        assert any(c["name"] == "honest_abstention" and c["passed"] for c in ans_abstain["verification_checks"])

