import hashlib
import re
from pathlib import Path
from typing import Sequence
import pymupdf

from backend.app.pipeline.interfaces import DocumentParser
from backend.app.schemas.evidence import (
    BoundingBox,
    DocumentItem,
    EvidenceItem,
    EvidenceKind,
    PageProvenance,
    TableItem,
)

class PyMuPDFDocumentParser(DocumentParser):
    """
    Extracts narrative evidence and structured tables from PDF documents
    while preserving page numbers, printed page labels, and coordinate provenance.
    """

    UNIT_PATTERNS = [
        re.compile(r"\b(in\s+billions|in\s+millions|in\s+thousands)\b", re.IGNORECASE),
        re.compile(r"\b(usd|\$|eur|€|gbp|£)\b", re.IGNORECASE),
        re.compile(r"\b(percent|%|percentage|basis points|bps)\b", re.IGNORECASE),
        re.compile(r"\b(gwh|mwh|kwh|mw|gw|tw)\b", re.IGNORECASE),
        re.compile(r"\b(metric tons|tonnes|mt|mmt)\b", re.IGNORECASE),
        re.compile(r"\b(per capita|units|index points)\b", re.IGNORECASE),
    ]

    def __init__(self) -> None:
        pass

    def _normalize_text(self, text: str) -> str:
        # Collapse multiple spaces and cleanup common PDF artifacts
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _extract_units(self, text: str) -> str | None:
        for pattern in self.UNIT_PATTERNS:
            match = pattern.search(text)
            if match:
                return match.group(0).lower()
        return None

    def _detect_footnotes(self, text: str) -> list[str]:
        footnotes = []
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
            if re.match(r"^(\*|\†|\‡|\d+[/)]|note:|source:|sources:)", line, re.IGNORECASE):
                footnotes.append(line)
        return footnotes

    def parse(self, file_path: Path, document_id: str) -> Sequence[EvidenceItem]:
        """Implements abstract method from DocumentParser interface."""
        _, _, evidence_items, _ = self.parse_document(file_path, document_id)
        return evidence_items

    def parse_document(
        self, file_path: Path, document_id: str
    ) -> tuple[DocumentItem, list[PageProvenance], list[EvidenceItem], list[TableItem]]:
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {path}")

        file_bytes = path.read_bytes()
        content_hash = f"sha256:{hashlib.sha256(file_bytes).hexdigest()}"

        doc = pymupdf.open(stream=file_bytes, filetype="pdf")
        page_count = len(doc)

        provenances: list[PageProvenance] = []
        evidence_items: list[EvidenceItem] = []
        table_items: list[TableItem] = []

        # Extract page labels if provided by the PDF
        try:
            page_labels = doc.get_page_labels()
        except Exception:
            page_labels = []

        for p_idx in range(page_count):
            page = doc[p_idx]
            rect = page.rect
            width = float(rect.width) if rect.width > 0 else 1.0
            height = float(rect.height) if rect.height > 0 else 1.0
            rotation = int(page.rotation)

            printed_label = None
            if page_labels and p_idx < len(page_labels) and page_labels[p_idx]:
                printed_label = page_labels[p_idx]
            else:
                printed_label = str(p_idx + 1)

            page_warnings: list[str] = []
            tables_on_page: list[pymupdf.Table] = []
            table_rects: list[pymupdf.Rect] = []

            # 1. Extract structured tables using page.find_tables()
            try:
                table_tab = page.find_tables()
                if table_tab and table_tab.tables:
                    tables_on_page = table_tab.tables
            except Exception as e:
                page_warnings.append(f"Table extraction error on page {p_idx}: {e}")

            page_table_count = 0
            for tbl in tables_on_page:
                page_table_count += 1
                tbl_id = f"tbl_{document_id}_p{p_idx}_{page_table_count}"
                table_rects.append(tbl.bbox)

                # Normalized bounding box
                t_bbox = BoundingBox(
                    x0=max(0.0, min(1.0, float(tbl.bbox[0]) / width)),
                    y0=max(0.0, min(1.0, float(tbl.bbox[1]) / height)),
                    x1=max(0.0, min(1.0, float(tbl.bbox[2]) / width)),
                    y1=max(0.0, min(1.0, float(tbl.bbox[3]) / height)),
                )

                extracted_data = tbl.extract()
                if not extracted_data or len(extracted_data) == 0:
                    continue

                headers: list[list[str]] = []
                rows: list[list[Any]] = []

                # Assume first row is primary header
                raw_header = [self._normalize_text(str(cell or "")) for cell in extracted_data[0]]
                headers.append(raw_header)

                for r_idx in range(1, len(extracted_data)):
                    row_data = [self._normalize_text(str(cell or "")) for cell in extracted_data[r_idx]]
                    # Check if entire row is empty
                    if any(c for c in row_data):
                        rows.append(row_data)

                # Build readable Markdown representation
                md_lines = []
                if raw_header:
                    md_lines.append("| " + " | ".join(raw_header) + " |")
                    md_lines.append("| " + " | ".join(["---"] * len(raw_header)) + " |")
                for r in rows:
                    md_lines.append("| " + " | ".join(str(c) for c in r) + " |")
                table_md = "\n".join(md_lines)

                # Detect units from header
                detected_units: dict[str, str] = {}
                for h in raw_header:
                    unit = self._extract_units(h)
                    if unit:
                        detected_units[h] = unit

                # Detect table title and footnotes
                table_title = f"Table on Page {printed_label}"
                table_footnotes: list[str] = []

                # Look for potential title right above table bbox
                title_rect = pymupdf.Rect(tbl.bbox[0], max(0, tbl.bbox[1] - 30), tbl.bbox[2], tbl.bbox[1])
                candidate_title = page.get_text("text", clip=title_rect).strip()
                if candidate_title:
                    table_title = self._normalize_text(candidate_title)

                # Look for footnotes right below table bbox
                fn_rect = pymupdf.Rect(tbl.bbox[0], tbl.bbox[3], tbl.bbox[2], min(height, tbl.bbox[3] + 40))
                candidate_fn = page.get_text("text", clip=fn_rect).strip()
                if candidate_fn:
                    table_footnotes.extend(self._detect_footnotes(candidate_fn))

                table_item = TableItem(
                    table_id=tbl_id,
                    document_id=document_id,
                    pdf_page_index=p_idx,
                    printed_page_number=printed_label,
                    title=table_title,
                    headers=headers,
                    rows=rows,
                    units=detected_units,
                    footnotes=table_footnotes,
                    bbox=t_bbox,
                    extraction_confidence=0.95,
                    warnings=[],
                )
                table_items.append(table_item)

                # Create top-level EvidenceItem for the table
                tbl_ev_id = f"ev_tbl_{document_id}_p{p_idx}_{page_table_count}"
                table_evidence_text = f"Title: {table_title}\n{table_md}"
                if table_footnotes:
                    table_evidence_text += "\nFootnotes:\n" + "\n".join(table_footnotes)

                evidence_items.append(
                    EvidenceItem(
                        evidence_id=tbl_ev_id,
                        document_id=document_id,
                        pdf_page_index=p_idx,
                        printed_page_number=printed_label,
                        kind="table",
                        text=table_evidence_text,
                        normalized_text=self._normalize_text(table_evidence_text),
                        bbox=t_bbox,
                        parent_id=None,
                        metadata={
                            "table_id": tbl_id,
                            "title": table_title,
                            "headers": raw_header,
                            "row_count": len(rows),
                            "col_count": len(raw_header),
                            "units": detected_units,
                            "footnotes": table_footnotes,
                        },
                        extraction_confidence=0.95,
                        warnings=[],
                    )
                )

                # Create structured row evidence items for surgical citations
                for r_idx, row in enumerate(rows):
                    row_desc = []
                    for c_idx, cell_val in enumerate(row):
                        header_name = raw_header[c_idx] if c_idx < len(raw_header) else f"Col {c_idx+1}"
                        if cell_val:
                            row_desc.append(f"{header_name}: {cell_val}")
                    row_text = f"{table_title} | " + " | ".join(row_desc)

                    row_ev_id = f"ev_row_{document_id}_p{p_idx}_{page_table_count}_r{r_idx}"
                    # Approximate row bbox vertically inside table bbox
                    num_rows = max(1, len(rows) + 1)
                    r_y0 = t_bbox.y0 + (t_bbox.y1 - t_bbox.y0) * ((r_idx + 1) / num_rows)
                    r_y1 = t_bbox.y0 + (t_bbox.y1 - t_bbox.y0) * ((r_idx + 2) / num_rows)
                    row_bbox = BoundingBox(
                        x0=t_bbox.x0,
                        y0=r_y0,
                        x1=t_bbox.x1,
                        y1=min(t_bbox.y1, r_y1),
                    )

                    evidence_items.append(
                        EvidenceItem(
                            evidence_id=row_ev_id,
                            document_id=document_id,
                            pdf_page_index=p_idx,
                            printed_page_number=printed_label,
                            kind="table_cell",
                            text=row_text,
                            normalized_text=self._normalize_text(row_text),
                            bbox=row_bbox,
                            parent_id=tbl_ev_id,
                            metadata={
                                "table_id": tbl_id,
                                "row_index": r_idx,
                                "headers": raw_header,
                                "row_values": row,
                                "units": detected_units,
                            },
                            extraction_confidence=0.95,
                        )
                    )

            # 2. Extract narrative text blocks (paragraphs, headings, footnotes)
            raw_blocks = page.get_text("blocks")
            narrative_count = 0
            has_text = False

            # Merge vertically adjacent line fragments into full paragraphs
            merged_blocks: list[list[Any]] = []
            for b in raw_blocks:
                b_rect = pymupdf.Rect(b[0], b[1], b[2], b[3])
                raw_b_text = str(b[4]).strip()
                if not raw_b_text:
                    continue

                has_text = True

                # Check if block overlaps significantly with any table
                overlaps_table = False
                for tbl_bbox in table_rects:
                    intersect = b_rect & pymupdf.Rect(tbl_bbox)
                    if intersect.get_area() > 0.4 * b_rect.get_area():
                        overlaps_table = True
                        break
                if overlaps_table:
                    continue

                # Try merging with previous block if vertically adjacent (< 12pt gap) and similar left margin
                if merged_blocks:
                    prev = merged_blocks[-1]
                    prev_rect = pymupdf.Rect(prev[0], prev[1], prev[2], prev[3])
                    v_gap = b_rect.y0 - prev_rect.y1
                    h_diff = abs(b_rect.x0 - prev_rect.x0)

                    # Only merge if gap is small and not starting a new section/heading
                    if 0 <= v_gap < 12 and h_diff < 20 and not b_rect.y0 > 0.85:
                        merged_blocks[-1] = [
                            min(prev[0], b[0]),
                            min(prev[1], b[1]),
                            max(prev[2], b[2]),
                            max(prev[3], b[3]),
                            prev[4].rstrip() + " " + raw_b_text,
                            prev[5],
                        ]
                        continue

                merged_blocks.append(list(b))

            for b in merged_blocks:
                b_rect = pymupdf.Rect(b[0], b[1], b[2], b[3])
                raw_b_text = str(b[4]).strip()

                narrative_count += 1
                ev_id = f"ev_narr_{document_id}_p{p_idx}_{narrative_count}"

                b_bbox = BoundingBox(
                    x0=max(0.0, min(1.0, float(b[0]) / width)),
                    y0=max(0.0, min(1.0, float(b[1]) / height)),
                    x1=max(0.0, min(1.0, float(b[2]) / width)),
                    y1=max(0.0, min(1.0, float(b[3]) / height)),
                )

                # Classify kind: heading vs paragraph vs footnote vs caption
                kind: EvidenceKind = "paragraph"
                normalized = self._normalize_text(raw_b_text)

                if len(normalized) < 80 and (
                    re.match(r"^(section|\d+\.|\d+\.\d+|chapter|executive summary|overview|key findings|introduction|table of contents|appendix)", normalized, re.IGNORECASE)
                    or normalized.isupper()
                ):
                    kind = "heading"
                elif b_bbox.y0 > 0.85 and (
                    re.match(r"^(\*|\†|\‡|\d+[/)]|note:|source:|sources:)", normalized, re.IGNORECASE)
                ):
                    kind = "footnote"
                elif re.match(r"^(figure\s+\d+|chart\s+\d+|exhibit\s+\d+|table\s+\d+):", normalized, re.IGNORECASE):
                    kind = "caption"

                evidence_items.append(
                    EvidenceItem(
                        evidence_id=ev_id,
                        document_id=document_id,
                        pdf_page_index=p_idx,
                        printed_page_number=printed_label,
                        kind=kind,
                        text=raw_b_text,
                        normalized_text=normalized,
                        bbox=b_bbox,
                        parent_id=None,
                        metadata={
                            "block_number": b[5],
                            "line_count": len(raw_b_text.splitlines()),
                        },
                        extraction_confidence=0.98,
                        warnings=[],
                    )
                )

            extraction_method = "native_text"
            if not has_text:
                extraction_method = "ocr"
                ocr_succeeded = False
                try:
                    tp = page.get_textpage_ocr(dpi=150)
                    ocr_blocks = tp.extractBLOCKS()
                    if ocr_blocks:
                        for b in ocr_blocks:
                            raw_b = str(b[4]).strip()
                            if not raw_b:
                                continue
                            narrative_count += 1
                            ev_id = f"ev_ocr_{document_id}_p{p_idx}_{narrative_count}"
                            b_bbox = BoundingBox(
                                x0=max(0.0, min(1.0, float(b[0]) / width)),
                                y0=max(0.0, min(1.0, float(b[1]) / height)),
                                x1=max(0.0, min(1.0, float(b[2]) / width)),
                                y1=max(0.0, min(1.0, float(b[3]) / height)),
                            )
                            evidence_items.append(
                                EvidenceItem(
                                    evidence_id=ev_id,
                                    document_id=document_id,
                                    pdf_page_index=p_idx,
                                    printed_page_number=printed_label,
                                    kind="paragraph",
                                    text=raw_b,
                                    normalized_text=self._normalize_text(raw_b),
                                    bbox=b_bbox,
                                    metadata={"source": "ocr", "line_count": len(raw_b.splitlines())},
                                    extraction_confidence=0.88,
                                    warnings=["Extracted via selective OCR."],
                                )
                            )
                        ocr_succeeded = True
                except Exception as e:
                    page_warnings.append(f"Page requires OCR; local OCR fallback attempted: {e}")

                if not ocr_succeeded and not page_warnings:
                    page_warnings.append("No native text found on page; page requires OCR inspection.")

            provenances.append(
                PageProvenance(
                    document_id=document_id,
                    pdf_page_index=p_idx,
                    printed_page_number=printed_label,
                    page_width=width,
                    page_height=height,
                    rotation=rotation,
                    extraction_method=extraction_method,
                    warnings=page_warnings,
                )
            )

        doc_item = DocumentItem(
            document_id=document_id,
            filename=path.name,
            content_hash=content_hash,
            page_count=page_count,
            processing_status="ready",
            metadata={
                "evidence_count": len(evidence_items),
                "table_count": len(table_items),
            },
        )

        return doc_item, provenances, evidence_items, table_items

