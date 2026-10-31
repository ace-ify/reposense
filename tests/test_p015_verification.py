import time
from pathlib import Path
from fastapi.testclient import TestClient
import pytest

from backend.app.main import app

def test_upload_report_and_verify_p015():
    with TestClient(app) as client:
        # 1. Upload public report
        t0 = time.time()
        pdf_path = Path("data/p5_benchmarks/report_A.pdf")
        with open(pdf_path, "rb") as f:
            up_res = client.post(
                "/api/v1/documents",
                files={"file": ("report_A.pdf", f, "application/pdf")},
            )

        assert up_res.status_code == 201
        doc_data = up_res.json()
        doc_id = doc_data["document_id"]
        print(f"Uploaded public report in {time.time() - t0:.2f}s with document_id={doc_id}")

        # 2. POST P015 to /api/v1/questions
        p015_question = "What was the total number of road accidents in Asansol Durgapur (million-plus city) during 2023?"
        q_res = client.post(
            "/api/v1/questions",
            json={"question": p015_question, "document_ids": [doc_id]},
        )
        assert q_res.status_code == 200
        ans = q_res.json()

        print(f"Status: {ans.get('status')}")
        print(f"Answer: {ans.get('answer')}")
        print(f"Citations count: {len(ans.get('citations', []))}")
        for i, c in enumerate(ans.get("citations", [])):
            print(f"Citation [{i+1}]: printed_page={c.get('printed_page_number')}, pdf_page_index={c.get('pdf_page_index')}, kind={c.get('kind')}")
            print(f"  bbox: {c.get('bbox')}")
            print(f"  snippet: {c.get('snippet')[:140]}")

        # 3. Assertions
        assert ans.get("status") == "answered"
        assert ans.get("answer") == "500"
        assert len(ans.get("citations", [])) > 0
        top_citation = ans["citations"][0]
        # Gold page is 101 (which is 0-indexed pdf_page_index 100)
        assert top_citation.get("printed_page_number") == 101 or top_citation.get("pdf_page_index") == 100
        assert top_citation.get("bbox") is not None
        assert "500" in top_citation.get("snippet", "")
        print("\n[VERIFIED] Answer is 500 and citation points to gold page 101 with bounding box!")

if __name__ == "__main__":
    test_upload_report_and_verify_p015()

