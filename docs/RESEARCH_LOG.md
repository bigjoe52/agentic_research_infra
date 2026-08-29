# Research Evidence Log

This append-only ledger records evidence. Building software is not evidence that a
research claim is true, and an evidence entry cannot itself adopt policy.

## Operating rules

- Before judging a substantive experiment, record its question, coverage, method,
  and success criteria appropriate to its maturity.
- Preserve negative, inconclusive, failed, unstable, and superseded results.
- Label evidence as **Data quality**, **Implementation**, or **Empirical**.
- Record basic provenance: code revision or dirty state, configuration identity,
  input identity/query scope, output location, and execution time.
- Correct an entry by appending a new entry that explicitly supersedes it. Preserve
  the original text and annotate its successor.
- A finding changes a durable rule only through `DECISIONS.md`.

## Status vocabulary

- **Planned:** question defined; no valid result.
- **In progress:** collection or implementation underway.
- **Inconclusive:** evidence insufficient or compromised.
- **Supported:** predeclared criteria met; replication may still be required.
- **Rejected:** predeclared criteria not met.
- **Superseded:** corrected by a named later entry.

## R-001 — Harness initialization check

**Type:** Implementation  
**Status:** Planned  
**Date:** {{CREATED_DATE}}  
**Supersedes:** None

- **Question:** Does the generated repository pass its documented local self-checks?
- **Coverage:** Repository structure, authority language, placeholder marking,
  secret-ignore defaults, packaging, and unit tests.
- **Method and criteria:** Run the commands in `README.md`; preserve the result in
  a successor entry rather than changing this planned entry.
- **Provenance:** Not yet available.
- **Result:** Not run in this newly generated project.
- **Limitations:** This does not test scientific validity or prove agent succession.
- **Next action:** Run the supported checks from a clean checkout.

## Entry template

```markdown
## R-XXX — Short question

**Type:** Data quality | Implementation | Empirical
**Status:** Planned | In progress | Inconclusive | Supported | Rejected | Superseded
**Date:** YYYY-MM-DD
**Supersedes:** None | R-XXX
**Superseded by:** None | R-XXX

- **Question:**
- **Coverage and exclusions:**
- **Method and predeclared criteria:**
- **Provenance:** revision/dirty state; config; inputs/query; outputs; time
- **Result:**
- **Limitations:**
- **Conclusion / next action:**
```

