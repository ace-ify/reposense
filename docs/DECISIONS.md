# Architecture decision records

Record consequential choices with context, alternatives, decision, trade-offs and revisit conditions.

## ADR-001: Preserve provenance
**Status:** Accepted  
Every extracted object retains document ID, zero-based PDF page index, optional printed page label and source coordinates. Citations cannot be reliable if provenance is reconstructed after retrieval.

## ADR-002: Separate narrative and structured evidence
**Status:** Accepted  
Store narrative chunks and structured table evidence as distinct types, while allowing unified retrieval. Flattening tables loses row/column relationships, units and multi-level headers.

## ADR-003: Deterministic calculations
**Status:** Accepted  
Use code for arithmetic and preserve source values and calculation steps. LLM output alone is not a dependable calculator or audit trail.

## ADR-004: Abstention is valid
**Status:** Accepted  
Support `not_found`, `ambiguous` and `conflicting` outcomes. A plausible unsupported answer is worse than a transparent limitation.
