import json
import os
import re
from typing import Any
import httpx

from backend.app.pipeline.calculator import DeterministicCalculator
from backend.app.schemas.evidence import EvidenceItem
from backend.app.schemas.question import (
    CalculationRecord,
    CitationItem,
    ClaimItem,
    QuestionClassification,
)

class AnswerReasoner:
    """
    Synthesizes factual answers grounded strictly in retrieved evidence,
    executes deterministic calculations for numerical queries, and preserves citations.
    """

    def __init__(self, calculator: DeterministicCalculator | None = None):
        self.calculator = calculator or DeterministicCalculator()
        self.groq_api_key = os.getenv("GROQ_API_KEY") or os.getenv("GROQ_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.api_key = self.groq_api_key or self.openai_api_key
        self.provider = "groq" if self.groq_api_key else ("openai" if self.openai_api_key else None)

    def _extract_numbers_from_evidence(self, evidence: list[EvidenceItem]) -> list[tuple[str, float, str, EvidenceItem]]:
        """
        Extracts (label/header, value, unit, item) from evidence metadata or text.
        Prioritizes structured table cells over narrative text.
        """
        numbers: list[tuple[str, float, str, EvidenceItem]] = []

        # 1. First priority: structured table cells
        for ev in evidence:
            if ev.kind == "table_cell" and "row_values" in ev.metadata and "headers" in ev.metadata:
                headers = ev.metadata.get("headers", [])
                row_vals = ev.metadata.get("row_values", [])
                for idx, cell in enumerate(row_vals):
                    hdr = headers[idx] if idx < len(headers) else f"col_{idx}"
                    num = self.calculator.parse_number(cell)
                    if num is not None:
                        unit = ev.metadata.get("units", {}).get(hdr, "")
                        numbers.append((hdr, num, unit, ev))

        # 2. Second priority: narrative text patterns (e.g. 'from 210 billion USD in 2022 to 260 billion USD in 2023')
        for ev in evidence:
            if ev.kind != "table_cell":
                # Match patterns like: "X [scale] in YEAR" or "YEAR[:\s]+X"
                pattern = re.compile(
                    r"([\$€£]?\s*[\d,]+(?:\.\d+)?%?(?:\s*(?:billion|million|thousand|gw|mw|kwh|mt))?)\s*(?:USD|in)?\s*(?:in|\(|of)?\s*(20\d\d|19\d\d)",
                    re.IGNORECASE,
                )
                for m in pattern.finditer(ev.text):
                    raw_val = m.group(1).strip()
                    year = m.group(2).strip()
                    val = self.calculator.parse_number(raw_val)
                    if val is not None and not (1900 <= val <= 2099 and "." not in raw_val):
                        numbers.append((year, val, "", ev))

                # Reverse pattern: "in YEAR, ... X [scale]"
                rev_pattern = re.compile(
                    r"(20\d\d|19\d\d)[^.\n]*?([\$€£]?\s*[\d,]+(?:\.\d+)?%?(?:\s*(?:billion|million|thousand|gw|mw|kwh|mt))?)",
                    re.IGNORECASE,
                )
                for m in rev_pattern.finditer(ev.text):
                    year = m.group(1).strip()
                    raw_val = m.group(2).strip()
                    val = self.calculator.parse_number(raw_val)
                    if val is not None and not (1900 <= val <= 2099 and "." not in raw_val):
                        numbers.append((year, val, "", ev))

        return numbers

    def reason_and_synthesize(
        self,
        question: str,
        classification: QuestionClassification,
        evidence: list[EvidenceItem],
    ) -> tuple[str, list[ClaimItem], list[CitationItem], CalculationRecord | None]:
        if not evidence:
            return "No supporting evidence found in the document.", [], [], None

        calculation: CalculationRecord | None = None
        claims: list[ClaimItem] = []
        citations: list[CitationItem] = []

        # Build citations for top evidence items
        top_evidence = evidence[:4]
        for ev in top_evidence:
            citations.append(
                CitationItem(
                    document_id=ev.document_id,
                    pdf_page_index=ev.pdf_page_index,
                    printed_page_number=ev.printed_page_number,
                    evidence_id=ev.evidence_id,
                    bbox=ev.bbox,
                    snippet=ev.text[:180] + ("..." if len(ev.text) > 180 else ""),
                    kind=ev.kind,
                )
            )

        # 1. Deterministic Numerical / Comparison workflow
        if classification.requires_arithmetic or classification.intent in ("comparison", "aggregation", "trend"):
            extracted_nums = self._extract_numbers_from_evidence(evidence)

            # Match target periods if available (e.g. 2022 and 2023)
            matched_by_period: dict[str, tuple[float, EvidenceItem]] = {}
            for period in classification.target_periods:
                for label, val, _, ev in extracted_nums:
                    # Match period in column header / label first
                    if period in label:
                        matched_by_period[period] = (val, ev)
                        break

            # Fallback if label didn't match: check label + text proximity
            if len(matched_by_period) < len(classification.target_periods):
                for period in classification.target_periods:
                    if period not in matched_by_period:
                        for label, val, _, ev in extracted_nums:
                            if period in label:
                                matched_by_period[period] = (val, ev)
                                break

            # If we have two periods and asked for percentage change or growth
            if len(matched_by_period) >= 2:
                periods = sorted(list(matched_by_period.keys()))
                p1, p2 = periods[0], periods[1]
                v1, ev1 = matched_by_period[p1]
                v2, ev2 = matched_by_period[p2]

                try:
                    if any(w in question.lower() for w in ["percent", "percentage", "increase", "growth", "change"]):
                        calculation = self.calculator.percentage_change(v1, v2, p1, p2)
                        ans_text = (
                            f"Between {p1} and {p2}, the value changed from {v1:g} to {v2:g}, "
                            f"representing a deterministic percentage change of {calculation.result:g}%. "
                            f"Calculated using formula: {calculation.formula}."
                        )
                    else:
                        calculation = self.calculator.difference(v2, v1, p2, p1)
                        ans_text = (
                            f"The difference between {p2} ({v2:g}) and {p1} ({v1:g}) is {calculation.result:g}. "
                            f"Calculated using formula: {calculation.formula}."
                        )

                    claims.append(
                        ClaimItem(
                            text=ans_text,
                            evidence_ids=[ev1.evidence_id, ev2.evidence_id],
                            calculation=calculation,
                        )
                    )
                    return ans_text, claims, citations, calculation
                except Exception:
                    pass

            # If we have two entities in the same period (e.g. Entity A vs Entity B in 2023)
            if len(classification.target_entities) >= 2 and classification.target_periods:
                target_period = classification.target_periods[0]
                matched_by_entity: dict[str, tuple[float, EvidenceItem]] = {}
                # Universal domain-agnostic table stopwords
                domain_agnostic_stopwords = {
                    "the", "a", "an", "and", "or", "in", "of", "for", "to", "total",
                    "subtotal", "average", "rate", "category", "source", "item",
                    "indicator", "value", "amount", "change", "growth", "difference",
                    "sector", "technology", "department", "company", "group", "division"
                }

                for ent in classification.target_entities:
                    ent_clean = ent.lower()
                    distinguishing = [w for w in ent_clean.split() if w not in domain_agnostic_stopwords and len(w) > 2]
                    if not distinguishing:
                        distinguishing = [w for w in ent_clean.split() if len(w) > 2]

                    # Find best matching row by token overlap
                    best_match: tuple[float, float, EvidenceItem] | None = None
                    for label, val, _, ev in extracted_nums:
                        if target_period in label:
                            ev_lower = ev.text.lower()
                            matched_tokens = sum(1 for w in distinguishing if w in ev_lower)
                            if matched_tokens > 0:
                                score = matched_tokens / len(distinguishing)
                                if best_match is None or score > best_match[0]:
                                    best_match = (score, val, ev)

                    if best_match and best_match[0] >= 0.5:
                        matched_by_entity[ent] = (best_match[1], best_match[2])

                if len(matched_by_entity) >= 2:
                    ent_keys = list(matched_by_entity.keys())
                    e1, e2 = ent_keys[0], ent_keys[1]
                    v1, ev1 = matched_by_entity[e1]
                    v2, ev2 = matched_by_entity[e2]

                    try:
                        calculation = self.calculator.difference(v1, v2, e1, e2)
                        ans_text = (
                            f"In {target_period}, {e1} was {v1:g} and {e2} was {v2:g}. "
                            f"The deterministic difference is {calculation.result:g}. "
                            f"Calculated using formula: {calculation.formula}."
                        )
                        claims.append(
                            ClaimItem(
                                text=ans_text,
                                evidence_ids=[ev1.evidence_id, ev2.evidence_id],
                                calculation=calculation,
                            )
                        )
                        return ans_text, claims, citations, calculation
                    except Exception:
                        pass

        # 2. LLM Synthesis (if API key available)
        if self.api_key:
            try:
                llm_answer, llm_claims = self._synthesize_with_llm(question, top_evidence)
                if llm_answer:
                    return llm_answer, llm_claims, citations, calculation
            except Exception:
                # Graceful fallback to deterministic synthesis
                pass

        # 3. Deterministic Tabular & Factual Synthesis
        tabular_answer, tab_claims = self._synthesize_tabular_factual(question, classification, evidence)
        if tabular_answer:
            return tabular_answer, tab_claims, citations, calculation

        # 4. Direct Factual Narrative Fallback
        primary = evidence[0]
        summary_clean = primary.text.strip().replace("\n", " ")
        if len(summary_clean) > 300:
            summary_clean = summary_clean[:300] + "..."

        answer_text = (
            f"Based on {primary.kind} evidence on page {primary.printed_page_number or primary.pdf_page_index + 1}: "
            f"{summary_clean}"
        )
        claims.append(
            ClaimItem(
                text=answer_text,
                evidence_ids=[primary.evidence_id],
                calculation=None,
            )
        )

        return answer_text, claims, citations, calculation

    def _synthesize_tabular_factual(
        self,
        question: str,
        classification: QuestionClassification,
        evidence: list[EvidenceItem],
    ) -> tuple[str | None, list[ClaimItem]]:
        """
        Extracts structured factual figures from tables (e.g. Total rows, specific entity rows, breakdown numbers)
        without relying on external LLM APIs.
        """
        table_ev = next((ev for ev in evidence if ev.kind == "table" or "|" in ev.text), None)
        if not table_ev:
            return None, []

        lines = [line.strip() for line in table_ev.text.split("\n") if line.strip()]
        # Extract markdown table rows
        table_rows = [line for line in lines if line.startswith("|") and line.endswith("|")]
        if len(table_rows) < 2:
            return None, []

        def clean_cells(row_str: str) -> list[str]:
            return [re.sub(r"\s+", " ", c.strip()) for c in row_str.strip("|").split("|")]

        # First line is header
        headers = clean_cells(table_rows[0])
        # Clean headers of newlines/numbers e.g. "1\n.\nBicycles" -> "Bicycles"
        clean_headers = [re.sub(r"^\d+\s*[\.\)]\s*", "", h).strip() for h in headers]

        data_rows = []
        for r_str in table_rows[1:]:
            if "---" in r_str:
                continue
            cells = clean_cells(r_str)
            # Skip numbering row e.g. | 1 | 2 | 3 |
            if all(c.isdigit() or not c for c in cells):
                continue
            data_rows.append(cells)

        if not data_rows:
            return None, []

        # Check if question specifies a row entity (e.g. "Assam", "Pembrolizumab", "Solar PV")
        target_row = None
        target_row_name = ""

        # Check classification entities first
        for ent in classification.target_entities:
            ent_lower = ent.lower()
            for r in data_rows:
                r_text = " ".join(r).lower()
                if ent_lower in r_text:
                    target_row = r
                    target_row_name = ent
                    break
            if target_row:
                break

        # Check individual words in question for entity names in the rows
        if not target_row:
            q_words = [w.lower() for w in re.findall(r"\b[A-Za-z]{3,}\b", question)]
            for r in data_rows:
                row_label = r[1] if len(r) > 1 and r[1] else r[0]
                if any(w == row_label.lower() for w in q_words if w not in ("total", "report", "table")):
                    target_row = r
                    target_row_name = row_label
                    break

        # If no specific entity requested, look for "Total" row
        if not target_row:
            for r in data_rows:
                if any("total" == c.lower() for c in r[:3]):
                    target_row = r
                    target_row_name = "Total"
                    break

        # If still no total row, take first substantive row
        if not target_row and data_rows:
            target_row = data_rows[0]
            target_row_name = target_row[1] if len(target_row) > 1 and target_row[1] else target_row[0]

        if target_row:
            # Pair headers with non-empty cell values
            pairs = []
            total_val = None
            for idx, cell_val in enumerate(target_row):
                if not cell_val:
                    continue
                header_name = clean_headers[idx] if idx < len(clean_headers) and clean_headers[idx] else f"Col {idx+1}"
                if header_name.lower() in ("s.no.", "s .no.", "s. no.", "sl. no.", "state/uts", "state", "description"):
                    continue
                
                # Clean up formatting commas e.g. "1200 ," -> "1,200"
                formatted_val = cell_val.replace(" ,", ",").replace(" ", "").replace("\n", "")
                if header_name.lower() == "total":
                    total_val = formatted_val
                else:
                    pairs.append(f"{header_name}: {formatted_val}")

            page_num = table_ev.printed_page_number or str(table_ev.pdf_page_index + 1)
            title = table_ev.metadata.get("title") or ""
            if not title or "Table on Page" in title:
                # Check narrative evidence on the same page for annexure / table title
                for ev in evidence:
                    if ev.pdf_page_index == table_ev.pdf_page_index and ev.kind in ("paragraph", "heading"):
                        candidate = ev.text.split("\n")[0].strip()
                        if any(w in candidate.lower() for w in ["table", "annexure", "section", "overview", "breakdown", "classified", "accidents", "report", "outcome"]):
                            title = candidate
                            break
            if not title or "Table on Page" in title:
                title = f"Table on Page {page_num}"

            # Format total value nicely (e.g. "4560," -> "4,560")
            if total_val:
                clean_tot = total_val.rstrip(",").strip()
                try:
                    num_tot = float(clean_tot.replace(",", ""))
                    formatted_total = f"{num_tot:,.0f}" if num_tot.is_integer() else f"{num_tot:,.2f}"
                except Exception:
                    formatted_total = clean_tot
            else:
                formatted_total = None

            ans_parts = [f"According to {title} on page {page_num},"]
            if target_row_name and target_row_name.lower() != "total":
                ans_parts.append(f"for {target_row_name},")
            
            if formatted_total:
                ans_parts.append(f"the recorded total is {formatted_total}.")
            else:
                ans_parts.append("the recorded figures are:")

            if pairs:
                # Clean up pairs values
                clean_pairs = []
                for p in pairs[:8]:
                    k, v = p.split(":", 1)
                    k = re.sub(r"^\d+\s*[\.\)]\s*", "", k).strip()
                    v = v.rstrip(",").strip()
                    clean_pairs.append(f"{k}: {v}")
                ans_parts.append(f"Breakdown: {'; '.join(clean_pairs)}.")

            full_ans = " ".join(ans_parts)
            claims = [ClaimItem(text=full_ans, evidence_ids=[table_ev.evidence_id], calculation=None)]
            return full_ans, claims

        return None, []

    def _synthesize_with_llm(
        self, question: str, evidence: list[EvidenceItem]
    ) -> tuple[str, list[ClaimItem]]:
        client = httpx.Client(timeout=12.0)
        context_blocks = []
        for ev in evidence:
            context_blocks.append(
                f"[Evidence ID: {ev.evidence_id} | Page: {ev.printed_page_number or ev.pdf_page_index + 1} | Kind: {ev.kind}]\n{ev.text}"
            )
        context_str = "\n\n".join(context_blocks)

        system_prompt = (
            "You are Report Navigator, an evidence-grounded Document Intelligence Engine for government statistics reports.\n"
            "Rules:\n"
            "1. Answer ONLY using numbers and facts explicitly present in the context.\n"
            "2. Cite evidence IDs in brackets e.g. [ev_...].\n"
            "3. If evidence is missing, contradictory, or does not directly answer the question, state: NOT_FOUND.\n"
            "4. NEVER invent numbers or do mental math estimations."
        )

        # Configure provider endpoint & model
        if self.groq_api_key:
            endpoint = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {self.groq_api_key}", "Content-Type": "application/json"}
            model = "llama-3.3-70b-versatile"
        else:
            endpoint = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {self.openai_api_key}", "Content-Type": "application/json"}
            model = "gpt-4o-mini"

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Context:\n{context_str}\n\nQuestion: {question}\n\nProvide a concise, direct, and verifiable answer citing evidence IDs.",
                },
            ],
            "temperature": 0.0,
            "max_tokens": 400,
        }

        try:
            resp = client.post(endpoint, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"].strip()
                # Extract cited evidence IDs
                cited_ids = re.findall(r"\[(ev_[a-zA-Z0-9_]+)\]", content)
                if not cited_ids:
                    cited_ids = [ev.evidence_id for ev in evidence[:2]]
                claims = [ClaimItem(text=content, evidence_ids=list(set(cited_ids)))]
                return content, claims
        except Exception:
            pass

        return "", []
