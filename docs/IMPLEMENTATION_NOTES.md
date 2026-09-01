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
  selected by `git ls-files --cached --others
  --exclude-per-directory=.gitignore`. For a project without root Git metadata, a
  temporary empty Git index supplies the same project-owned ignore semantics
  without modifying the project. User/global Git excludes and `.git/info/exclude`
  cannot change governance scan results. This prevents project-ignored secrets and
  local/generated artifacts from becoming admissible merely by existing on disk,
  while retaining tracked and non-ignored project files.
- Downstream reconciliation is driven by `harness/surface-v1.json`. Only the
  governance scanner and its focused test are initially maintainable. Surface
  membership makes a path eligible for a semantic migration; it never authorizes
  whole-file replacement or policy adoption.
- Updater plans bind descendant `HEAD`, index tree, committed lineage, exact
  upstream tag/commit, surface, migration descriptors, proposed bytes, and
  validation to a canonical SHA-256 identity. Application revalidates those
  inputs and refuses drift.
- Per-component BASE comes from the descendant commit that first recorded the
  latest component lineage event. Missing or hash-inconsistent history stops
  planning. Upstream release prose and version strings are not ancestry evidence.
- Application validates in a disposable detached worktree before touching the
  live descendant. Live rollback is limited to exact updater mutations whose
  expected post-application hashes remain intact. Successful lineage is written
  only after live validation, and the updater never commits.

## Entry template

```markdown
## Component or invariant

Behavior, reason, failure mode prevented, known limitation, and relevant tests.
```
