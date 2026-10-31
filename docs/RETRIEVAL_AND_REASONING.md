# Retrieval and reasoning

## Question types
`lookup`, `comparison`, `aggregation`, `trend`, `definition`, `multi_hop`, `unanswerable`, `ambiguous`.

Classification is a routing hint, not proof that evidence exists.

## Retrieval flow
1. Identify candidate entities, metrics, periods and units.
2. Search narrative and table representations using BM25 and dense retrieval.
3. Apply justified document/section/entity filters.
4. Fuse rankings with Reciprocal Rank Fusion.
5. Rerank candidates.
6. Expand evidence with parent context: table title, complete header path, units and footnotes.

## Table lookup
A cell is not meaningful without its row identity, full column-header path, unit, period and relevant footnotes.

## Numerical reasoning
Use deterministic Python operations. Record source evidence IDs, raw and normalized values, units, formula, result and rounding policy. Reject incompatible units, populations, definitions or periods unless a documented conversion exists.

## Verification
Check source, entity, metric, period, unit, table headers, footnotes, arithmetic and citation location. If a required check fails, return `ambiguous`, `conflicting` or `not_found`.

Do not treat an LLM's self-reported confidence as a calibrated probability. Calibrate thresholds against labelled evaluation data.
