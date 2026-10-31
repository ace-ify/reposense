# Evaluation strategy

| Dimension | Measures |
|---|---|
| Retrieval | Recall@k, MRR, nDCG |
| Answer quality | Exact match where suitable; human review for open answers |
| Citation | Correct document, page and evidence span |
| Table understanding | Header path, row and cell accuracy |
| Numerical reasoning | Correct inputs, units, formula and result |
| Abstention | Precision/recall on unanswerable and ambiguous cases |
| OCR | Character/word error rate on scanned pages |
| Robustness | Different report families, layouts and paraphrases |
| Operations | Processing time, query latency, failures and resource use |

## Test coverage
Include direct lookups, paraphrases, comparisons, percentage changes, multi-hop questions, unseen reports, scanned pages, ambiguous entities/units/periods, unanswerable questions and conflicting values.

Keep development and held-out evaluation sets separate. Do not tune on held-out examples or allow near-duplicates across splits.

## Error taxonomy
Parsing/OCR; table structure; retrieval miss; entity mismatch; metric/header mismatch; period/unit mismatch; calculation; unsupported generation; citation/page mapping; abstention failure.

Review critical errors separately. A single aggregate score can conceal dangerous numerical or citation failures.
