import re
from backend.app.schemas.question import QuestionClassification, QuestionIntent

class QuestionClassifier:
    """
    Classifies user questions into intent categories and extracts structured targets
    such as periods, metrics, entities, and calculation requirements.
    """

    PERIOD_REGEX = re.compile(
        r"\b(20\d\d|19\d\d|fy\s*20\d\d|fy\s*\d{2}|q[1-4]\s*20\d\d|q[1-4])\b",
        re.IGNORECASE,
    )

    COMPARISON_WORDS = {
        "increase", "decrease", "growth", "change", "difference", "compare",
        "versus", "vs", "higher", "lower", "more", "less", "delta", "pct",
        "percentage increase", "percentage change", "growth rate"
    }

    AGGREGATION_WORDS = {
        "total", "sum", "average", "mean", "combined", "overall", "aggregate"
    }

    TREND_WORDS = {
        "trend", "trajectory", "historical", "over time", "evolution", "cagr", "projection"
    }

    DEFINITION_WORDS = {
        "define", "definition", "meaning", "what is meant by", "how is defined"
    }

    ARITHMETIC_TRIGGERS = {
        "percent", "percentage", "increase", "decrease", "growth", "difference",
        "delta", "total", "sum", "average", "mean", "ratio", "portion", "share",
        "rate of change"
    }

    def classify(self, question: str) -> QuestionClassification:
        q_lower = question.lower().strip()

        # Extract periods
        periods = [m.group(0).upper() for m in self.PERIOD_REGEX.finditer(q_lower)]

        # Check for multi-hop patterns
        is_multi_hop = bool(
            re.search(r"\b(which|what)\s+(country|sector|company|region|item|category)\s+had\s+(the\s+)?(highest|lowest|most|least)\b.*?\band\b", q_lower)
            or re.search(r"\bfind\s+the\s+(top|highest|lowest)\b.*?\band\s+(what|how)\b", q_lower)
        )

        # Check for arithmetic
        requires_arithmetic = any(trigger in q_lower for trigger in self.ARITHMETIC_TRIGGERS)

        # Determine Intent
        intent: QuestionIntent = "lookup"
        rationale = "Direct factual lookup question."

        if is_multi_hop:
            intent = "multi_hop"
            rationale = "Question requires finding an entity matching a condition and retrieving its metric."
        elif any(word in q_lower for word in self.DEFINITION_WORDS):
            intent = "definition"
            rationale = "Question seeks a conceptual or metric definition."
        elif any(word in q_lower for word in self.AGGREGATION_WORDS):
            intent = "aggregation"
            rationale = "Question asks for a combined sum, total, or average across categories."
        elif any(word in q_lower for word in self.COMPARISON_WORDS):
            intent = "comparison"
            rationale = "Question asks for comparison or percentage change between periods or entities."
        elif any(word in q_lower for word in self.TREND_WORDS):
            intent = "trend"
            rationale = "Question asks for historical or directional trajectory."
        elif "?" not in question and len(question.split()) < 3:
            intent = "ambiguous"
            rationale = "Question is too brief or ambiguous."

        # Extract candidate target metrics and entities
        target_entities: list[str] = []
        target_metrics: list[str] = []

        # Check for 'between X and Y'
        between_match = re.search(r"between\s+(.+?)\s+(?:and|vs)\s+(.+?)(?:\s+in|\?|$)", question, re.IGNORECASE)
        if between_match:
            ent1 = between_match.group(1).strip()
            ent2 = between_match.group(2).strip()
            # Clean trailing words like 'investment', 'capacity'
            clean1 = re.sub(r"\b(investment|capacity|expenditure|revenue|subsidies|subsidy)\b", "", ent1, flags=re.IGNORECASE).strip()
            clean2 = re.sub(r"\b(investment|capacity|expenditure|revenue|subsidies|subsidy)\b", "", ent2, flags=re.IGNORECASE).strip()
            if clean1:
                target_entities.append(clean1.title())
            if clean2:
                target_entities.append(clean2.title())

        # Extract subject phrases by filtering out stop words, question words, and periods
        ignored_tokens = {
            "what", "were", "was", "is", "are", "how", "why", "when", "which",
            "the", "a", "an", "in", "of", "for", "between", "and", "or", "to", "from",
            "total", "combined", "overall", "difference", "change", "percentage",
            "percent", "growth", "rate", "projected", "projection"
        }
        tokens = [t for t in re.findall(r"\b[a-zA-Z]{3,}\b", q_lower) if t not in ignored_tokens]
        if not target_entities and tokens:
            target_entities.append(" ".join(tokens).title())

        for met in ["revenue", "receipts", "expenditure", "capacity", "investment", "growth", "gdp", "emissions", "subsidy", "subsidies"]:
            if met in q_lower:
                target_metrics.append(met.title())

        return QuestionClassification(
            intent=intent,
            target_entities=target_entities,
            target_metrics=target_metrics,
            target_periods=periods,
            requires_arithmetic=requires_arithmetic,
            confidence=0.92,
            rationale=rationale,
        )
