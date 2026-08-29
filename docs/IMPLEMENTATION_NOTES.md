# Implementation Notes

Record only non-obvious safeguards, invariants, and limitations that a future
maintainer might accidentally remove. Ordinary module documentation belongs near
the code. Empirical results belong in `RESEARCH_LOG.md`.

## Current invariants

- The package exposes only a neutral repository identity check. It contains no
  research model or adopted project-specific behavior.
- The self-check validates institutional structure, not scientific correctness or
  successful agent succession.

## Entry template

```markdown
## Component or invariant

Behavior, reason, failure mode prevented, known limitation, and relevant tests.
```

