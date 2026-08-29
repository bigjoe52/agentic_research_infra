# Implementation Notes

Record only non-obvious safeguards, invariants, and limitations that a future
maintainer might accidentally remove. Ordinary module documentation belongs near
the code. Empirical results belong in `RESEARCH_LOG.md`.

## Current invariants

- The package exposes only a neutral repository identity check. It contains no
  research model or adopted project-specific behavior.
- The self-check validates institutional structure, not scientific correctness or
  successful agent succession.
- Repository-wide content scans operate only on regular, non-symlink files
  selected by `git ls-files --cached --others --exclude-standard`. For a project
  without root Git metadata, a temporary empty Git index supplies the same ignore
  semantics without modifying the project. This prevents ignored secrets and
  local/generated artifacts from becoming admissible merely by existing on disk,
  while retaining tracked and non-ignored project files.

## Entry template

```markdown
## Component or invariant

Behavior, reason, failure mode prevented, known limitation, and relevant tests.
```
