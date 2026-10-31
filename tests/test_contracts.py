import pytest
from pydantic import ValidationError
from backend.app.schemas.evidence import EvidenceItem

def test_pdf_page_index_must_be_nonnegative() -> None:
    with pytest.raises(ValidationError):
        EvidenceItem(evidence_id="ev1", document_id="doc1", pdf_page_index=-1,
                     kind="paragraph", text="Example")

def test_printed_page_is_separate_from_pdf_index() -> None:
    item = EvidenceItem(evidence_id="ev1", document_id="doc1", pdf_page_index=100,
                        printed_page_number=77, kind="table", text="Example")
    assert item.pdf_page_index == 100
    assert item.printed_page_number == 77
