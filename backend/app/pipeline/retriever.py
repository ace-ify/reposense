import math
import re
from collections import Counter, defaultdict
from typing import Sequence

from backend.app.pipeline.interfaces import EvidenceRetriever
from backend.app.schemas.evidence import EvidenceItem, TableItem

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "aren't", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both",
    "but", "by", "can", "can't", "cannot", "could", "did", "do", "does", "doing", "don't", "down",
    "during", "each", "few", "for", "from", "further", "had", "has", "have", "having", "he", "her",
    "here", "hers", "herself", "him", "himself", "his", "how", "i", "if", "in", "into", "is",
    "isn't", "it", "its", "itself", "let's", "me", "more", "most", "my", "myself", "no", "nor",
    "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves",
    "out", "over", "own", "same", "she", "should", "so", "some", "such", "than", "that", "the",
    "their", "theirs", "them", "themselves", "then", "there", "these", "they", "this", "those",
    "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", "we", "were", "what",
    "when", "where", "which", "while", "who", "whom", "why", "with", "won't", "would", "you",
    "your", "yours", "yourself", "yourselves"
}

def tokenize(text: str) -> list[str]:
    cleaned = re.sub(r"[^\w\s\$\%\.]", " ", text.lower())
    tokens = [t.strip(".") for t in cleaned.split() if len(t.strip(".")) > 1]
    return [t for t in tokens if t not in STOPWORDS or t in {"what", "which", "who", "when"}]


class BM25Index:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.docs: list[EvidenceItem] = []
        self.doc_tokens: list[list[str]] = []
        self.doc_freqs: list[Counter[str]] = []
        self.df: dict[str, int] = defaultdict(int)
        self.avg_doc_len: float = 0.0

    def fit(self, docs: Sequence[EvidenceItem]) -> None:
        self.docs = list(docs)
        self.doc_tokens = []
        self.doc_freqs = []
        self.df.clear()

        total_tokens = 0
        for doc in self.docs:
            enriched_text = f"{doc.text} {doc.kind} page {doc.pdf_page_index} {doc.printed_page_number or ''}"
            tokens = tokenize(enriched_text)
            self.doc_tokens.append(tokens)
            freq = Counter(tokens)
            self.doc_freqs.append(freq)
            total_tokens += len(tokens)
            for token in set(tokens):
                self.df[token] += 1

        self.avg_doc_len = total_tokens / max(1, len(self.docs))

    def score(self, query: str) -> list[tuple[EvidenceItem, float]]:
        if not self.docs:
            return []

        q_tokens = tokenize(query)
        scores: list[float] = [0.0] * len(self.docs)
        n_docs = len(self.docs)

        for token in q_tokens:
            doc_freq = self.df.get(token, 0)
            if doc_freq == 0:
                continue
            idf = math.log((n_docs - doc_freq + 0.5) / (doc_freq + 0.5) + 1.0)
            for i, freq in enumerate(self.doc_freqs):
                tf = freq.get(token, 0)
                if tf == 0:
                    continue
                doc_len = len(self.doc_tokens[i])
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
                scores[i] += idf * (numerator / denominator)

        ranked = [(self.docs[i], scores[i]) for i in range(len(self.docs)) if scores[i] > 0]
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked


class HybridEvidenceRetriever(EvidenceRetriever):
    """
    Hybrid retriever combining Okapi BM25 and semantic character/subword matching
    with Reciprocal Rank Fusion (RRF) and parent-table context expansion.
    """

    def __init__(self, rrf_k: int = 60):
        self.rrf_k = rrf_k
        self.evidence_by_doc: dict[str, list[EvidenceItem]] = defaultdict(list)
        self.tables_by_doc: dict[str, dict[str, TableItem]] = defaultdict(dict)
        self.bm25_by_doc: dict[str, BM25Index] = {}

    def index_document(
        self,
        document_id: str,
        evidence_items: Sequence[EvidenceItem],
        table_items: Sequence[TableItem] | None = None,
    ) -> None:
        self.evidence_by_doc[document_id] = list(evidence_items)
        if table_items:
            for tbl in table_items:
                self.tables_by_doc[document_id][tbl.table_id] = tbl

        bm25 = BM25Index()
        bm25.fit(evidence_items)
        self.bm25_by_doc[document_id] = bm25

    def _semantic_overlap_score(self, query: str, item: EvidenceItem) -> float:
        """Subword / token character-level cosine-like similarity score."""
        q_tokens = set(tokenize(query))
        e_tokens = set(tokenize(item.text))
        if not q_tokens or not e_tokens:
            return 0.0

        overlap = len(q_tokens.intersection(e_tokens))
        jaccard = overlap / float(len(q_tokens.union(e_tokens)))

        # Boost numbers and year tokens if they match
        q_nums = set(re.findall(r"\b\d{4}\b|\b\d+(?:\.\d+)?%?\b", query))
        e_nums = set(re.findall(r"\b\d{4}\b|\b\d+(?:\.\d+)?%?\b", item.text))
        num_bonus = 0.0
        if q_nums and e_nums:
            matched_nums = len(q_nums.intersection(e_nums))
            num_bonus = 0.3 * (matched_nums / len(q_nums))

        return jaccard + num_bonus

    def retrieve(
        self,
        question: str,
        document_ids: list[str],
        top_k: int = 8,
        min_score: float = 0.0,
    ) -> Sequence[EvidenceItem]:
        all_candidates: list[EvidenceItem] = []
        for doc_id in document_ids:
            if doc_id in self.evidence_by_doc:
                all_candidates.extend(self.evidence_by_doc[doc_id])

        if not all_candidates:
            return []

        # 1. Lexical retrieval (BM25)
        bm25_ranks: dict[str, int] = {}
        bm25_ranked_items: list[tuple[EvidenceItem, float]] = []

        for doc_id in document_ids:
            if doc_id in self.bm25_by_doc:
                bm25_ranked_items.extend(self.bm25_by_doc[doc_id].score(question))

        bm25_ranked_items.sort(key=lambda x: x[1], reverse=True)
        for rank, (item, _) in enumerate(bm25_ranked_items):
            bm25_ranks[item.evidence_id] = rank

        # 2. Semantic matching ranking
        semantic_scores = [
            (item, self._semantic_overlap_score(question, item))
            for item in all_candidates
        ]
        semantic_scores.sort(key=lambda x: x[1], reverse=True)
        semantic_ranks = {
            item.evidence_id: rank
            for rank, (item, score) in enumerate(semantic_scores)
            if score > 0
        }

        # 3. Reciprocal Rank Fusion (RRF)
        fused_scores: dict[str, float] = defaultdict(float)
        item_map: dict[str, EvidenceItem] = {item.evidence_id: item for item in all_candidates}

        for ev_id, rank in bm25_ranks.items():
            fused_scores[ev_id] += 1.0 / (self.rrf_k + rank)

        for ev_id, rank in semantic_ranks.items():
            fused_scores[ev_id] += 1.0 / (self.rrf_k + rank)

        # 4. Context Expansion for tables
        # If a table_cell or row was retrieved, ensure its parent table context is included
        # and attach metadata if not already attached
        ranked_ev_ids = sorted(fused_scores.keys(), key=lambda eid: fused_scores[eid], reverse=True)

        result_items: list[EvidenceItem] = []
        seen_ids: set[str] = set()

        for eid in ranked_ev_ids:
            if len(result_items) >= top_k:
                break
            if eid in seen_ids:
                continue

            item = item_map[eid]
            seen_ids.add(eid)

            # Enrich table item context if applicable
            if item.kind in ("table_cell", "table") and item.parent_id:
                parent = item_map.get(item.parent_id)
                if parent and parent.evidence_id not in seen_ids:
                    # Provide enriched table context
                    result_items.append(item)
                    if len(result_items) < top_k:
                        result_items.append(parent)
                        seen_ids.add(parent.evidence_id)
                    continue

            result_items.append(item)

        # Fallback if no lexical/semantic matches: return top page headings/tables
        if not result_items:
            result_items = [
                item for item in all_candidates
                if item.kind in ("heading", "table", "paragraph")
            ][:top_k]

        return result_items

