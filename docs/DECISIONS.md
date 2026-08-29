# Durable Decisions

This append-only log contains adopted project constraints and choices. Research
findings do not become authority until a decision explicitly adopts their
consequence.

## Status vocabulary

- **Adopted:** currently binding.
- **Provisional:** usable for bounded research but not established as optimal.
- **Deferred:** intentionally not decided.
- **Superseded:** replaced by a later identified entry.

## Entry rules

- Add new entries with stable IDs (`D-001`, `D-002`, ...).
- Never silently rewrite the substance of a historical decision.
- A correction names `Supersedes: D-...`; the prior entry is annotated
  `Superseded by: D-...` without deleting its original text.
- Each entry states consequences and what it does **not** authorize.

## D-001 — Adopt the lightweight research harness

**Status:** Adopted  
**Date:** {{CREATED_DATE}}  
**Supersedes:** None

Use the repository authority hierarchy, append-only decision/evidence logs, basic
provenance, and proportional maturity controls defined by RJC Research Harness v1.

This adopts research-process rules only. It does not adopt a scientific
hypothesis, data source, empirical conclusion, protected-data access, external
action, or deployment decision.

## Open decisions

- The project-specific question, data sources, observation contract, and first
  baseline remain undecided.

## Entry template

```markdown
## D-XXX — Short title

**Status:** Adopted | Provisional | Deferred | Superseded
**Date:** YYYY-MM-DD
**Supersedes:** None | D-XXX
**Superseded by:** None | D-XXX

Decision, rationale, consequences, limitations, and actions not authorized.
```

