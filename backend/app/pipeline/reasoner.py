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
        self.api_key = os.getenv("OPENAI_API_KEY")

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

        # 3. Direct Factual Synthesis Fallback
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

    def _synthesize_with_llm(
        self, question: str, evidence: list[EvidenceItem]
    ) -> tuple[str, list[ClaimItem]]:
        client = httpx.Client(timeout=10.0)
        context_blocks = []
        for ev in evidence:
            context_blocks.append(
                f"[Evidence ID: {ev.evidence_id} | Page: {ev.pdf_page_index} | Kind: {ev.kind}]\n{ev.text}"
            )
        context_str = "\n\n".join(context_blocks)

        system_prompt = (
            "You are an evidence-grounded Document Intelligence Engine for statistical reports.\n"
            "Rules:\n"
            "1. Answer ONLY using facts explicitly stated in the context.\n"
            "2. Cite evidence IDs in brackets e.g. [ev_...].\n"
            "3. If evidence is missing, contradictory, or does not directly answer the question, state: NOT_FOUND.\n"
            "4. NEVER invent numbers or do mental math estimations."
        )

        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Context:\n{context_str}\n\nQuestion: {question}\n\nProvide a concise, direct answer citing evidence IDs.",
                },
            ],
            "temperature": 0.0,
            "max_tokens": 400,
        }

        resp = client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json=payload,
        )

        if resp.status_code == 200:
            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()
            # Extract cited evidence IDs
            cited_ids = re.findall(r"\[(ev_[a-zA-Z0-9_]+)\]", content)
            claims = [ClaimItem(text=content, evidence_ids=list(set(cited_ids)))]
            return content, claims

        return "", []
