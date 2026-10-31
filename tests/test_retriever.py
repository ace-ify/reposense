from backend.app.pipeline.retriever import HybridEvidenceRetriever
from backend.app.schemas.evidence import BoundingBox, EvidenceItem, TableItem

def test_retriever_bm25_and_context_expansion() -> None:
    retriever = HybridEvidenceRetriever()

    parent_table_ev = EvidenceItem(
        evidence_id="ev_tbl_1",
        document_id="doc1",
        pdf_page_index=2,
        printed_page_number=3,
        kind="table",
        text="Title: Table 4. Clean Energy Capacity by Source\n| Technology | 2022 | 2023 |\n| Solar PV | 142 GW | 185 GW |",
        bbox=BoundingBox(x0=0.1, y0=0.2, x1=0.9, y1=0.5),
    )

    child_cell_ev = EvidenceItem(
        evidence_id="ev_row_1",
        document_id="doc1",
        pdf_page_index=2,
        printed_page_number=3,
        kind="table_cell",
        text="Solar PV additions were 185 GW in 2023",
        parent_id="ev_tbl_1",
        bbox=BoundingBox(x0=0.1, y0=0.3, x1=0.9, y1=0.35),
    )

    narrative_ev = EvidenceItem(
        evidence_id="ev_narr_1",
        document_id="doc1",
        pdf_page_index=0,
        printed_page_number=1,
        kind="paragraph",
        text="The executive summary highlights rapid growth in zero-emission grid integration.",
        bbox=BoundingBox(x0=0.1, y0=0.1, x1=0.9, y1=0.2),
    )

    table_item = TableItem(
        table_id="tbl_1",
        document_id="doc1",
        pdf_page_index=2,
        title="Table 4. Clean Energy Capacity by Source",
        headers=[["Technology", "2022", "2023"]],
        rows=[["Solar PV", "142 GW", "185 GW"]],
    )

    retriever.index_document("doc1", [parent_table_ev, child_cell_ev, narrative_ev], [table_item])

    # Query for Solar PV in 2023
    results = retriever.retrieve("What was Solar PV additions in 2023?", ["doc1"], top_k=3)
    assert len(results) > 0
    retrieved_ids = [r.evidence_id for r in results]

    # Should retrieve the solar cell evidence
    assert "ev_row_1" in retrieved_ids or "ev_tbl_1" in retrieved_ids

    # Query narrative
    results_narrative = retriever.retrieve("grid integration zero-emission", ["doc1"], top_k=2)
    assert any(r.evidence_id == "ev_narr_1" for r in results_narrative)

