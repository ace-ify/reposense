from pathlib import Path
import pymupdf
import pytest
from backend.app.pipeline.parser import PyMuPDFDocumentParser

def test_parser_extracts_text_and_tables(tmp_path: Path) -> None:
    # Create a synthetic PDF with text and a table
    pdf_path = tmp_path / "sample_report.pdf"
    doc = pymupdf.open()
    page = doc.new_page(width=600, height=800)

    # Insert heading
    page.insert_text((50, 60), "EXECUTIVE SUMMARY", fontsize=16)

    # Insert narrative paragraph
    page.insert_text(
        (50, 100),
        "Global renewable energy investments reached 450 billion USD in 2023, representing an increase of 15 percent.",
        fontsize=11,
    )

    # Insert a table using lines and text
    table_rect = pymupdf.Rect(50, 150, 550, 250)
    page.draw_rect(table_rect, color=(0, 0, 0), width=1)
    # Header line
    page.draw_line((50, 180), (550, 180), color=(0, 0, 0), width=1)
    # Col line
    page.draw_line((250, 150), (250, 250), color=(0, 0, 0), width=1)
    page.draw_line((400, 150), (400, 250), color=(0, 0, 0), width=1)

    page.insert_text((60, 170), "Sector", fontsize=10)
    page.insert_text((260, 170), "2022 (USD B)", fontsize=10)
    page.insert_text((410, 170), "2023 (USD B)", fontsize=10)

    page.insert_text((60, 210), "Solar Power", fontsize=10)
    page.insert_text((260, 210), "200", fontsize=10)
    page.insert_text((410, 210), "250", fontsize=10)

    # Add footnote
    page.insert_text((50, 750), "* Source: Global Energy Transition Outlook 2024.", fontsize=9)

    doc.save(pdf_path)
    doc.close()

    parser = PyMuPDFDocumentParser()
    doc_item, provenances, evidence, tables = parser.parse_document(pdf_path, "doc_test_1")

    assert doc_item.document_id == "doc_test_1"
    assert doc_item.page_count == 1
    assert len(provenances) == 1
    assert provenances[0].pdf_page_index == 0
    assert len(evidence) > 0

    # Ensure bounding boxes are strictly normalized between 0 and 1
    for ev in evidence:
        if ev.bbox:
            assert 0.0 <= ev.bbox.x0 <= 1.0
            assert 0.0 <= ev.bbox.y0 <= 1.0
            assert 0.0 <= ev.bbox.x1 <= 1.0
            assert 0.0 <= ev.bbox.y1 <= 1.0
            assert ev.bbox.x0 <= ev.bbox.x1
            assert ev.bbox.y0 <= ev.bbox.y1

    # Check for presence of narrative content
    narrative_texts = [ev.text for ev in evidence if ev.kind in ("paragraph", "heading", "footnote")]
    assert any("Global renewable energy investments" in t for t in narrative_texts)

