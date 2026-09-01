# Successor Handoff

> **NON-AUTHORITATIVE HOT CONTEXT**
>
> This file is a navigation aid only. It cannot grant experimental access,
> protected-data access, external-action authority, spending, publication,
> deployment, or a change of research scope. A successor must independently read
> `AGENTS.md` and reload authoritative repository state. If this file conflicts
> with authoritative state, authoritative state wins and the discrepancy must be
> recorded.

## Snapshot

- Updated: 2026-09-01
- Code revision / dirty state: `v1.1.0` release-candidate commit; inspect `HEAD`
  and working tree independently
- Current objective: management decision on annotated `v1.1.0` tag authorization
- Current maturity: updater implemented and release-candidate verified; tag not
  created
- Active experiment: none

## Recent work

- Reloaded the authoritative repository state and inspected the actual tagged
  `v1.0.0 -> v1.0.1 -> v1.0.2` changes.
- Confirmed that the real `v1.0.1` scanner change included the pre-Git temporary
  index and symlink exclusion, and that `v1.0.2` made project `.gitignore` the
  exclusion authority rather than user/global or `.git/info/exclude` state.
- Management accepted the architecture and resolved the MVP policy questions.
  `HARNESS_DECISIONS.md` now records HD-001 and is excluded from descendants.
- Implemented the scanner-only surface, two historical semantic migrations,
  native and legacy lineage, canonical plans, exact approval, per-component BASE,
  detached validation, guarded live rollback, and no automatic commit.
- The disposable historical acceptance fixture detected the deliberately
  incomplete scanner recreation, then reconciled the actual tagged safeguards
  while preserving project-owned state.
- Recorded supported implementation evidence in H-004. No active descendant was
  accessed or modified, and no release or tag was created.
- Release preparation updated the self-check/template identity to `v1.1.0`, made
  clean untagged candidate commits eligible for verified origin lineage, prevented
  historical migrations already included in a verified origin from being
  proposed, and separated harness-maintainer handoff state from generated-project
  handoffs.

## Exact next action

Review the reported candidate commit and verification. If accepted, authorize
creation of annotated tag `v1.1.0`; the tag remains withheld.

## Relevant authoritative entries

- Harness releases: `v1.0.0` (`2ffb43c`), `v1.0.1` (`d19adb7`), `v1.0.2`
  (`6c3eeab`)
- Harness decision: HD-001
- Harness evidence: H-002, H-003, and H-004

## Access and authority state

- Development data accessed: no
- Validation data accessed: no
- Final holdout accessed: no
- Protected data accessed: no
- Active research repositories modified: no
- External actions authorized: none
- Deployment authorized: no

## Working-tree and limitations

- Inspect `git status` independently; the release-candidate commit is expected to
  have a clean tracked working tree.
- Validation passed 11 updater tests, five generated-project tests, the generated
  self-check, template check, direct maintainer-file compilation, and
  `git diff --check`.
- No live descendant research repository was inspected or modified; the
  production history in the assignment was used only as the required conceptual
  case.
- The updater requires clean Git state and sufficient reachable history, supports
  regular text reconciliation only, performs no network fetch or tag-signature
  verification, and cannot authenticate the organizational identity asserted in
  a management-authorization record.
- A dirty source checkout instantiates truthful `unverified` origin lineage. A
  clean exact candidate commit is `verified`; its tag remains null until a tag
  actually exists.

## Successor acknowledgment template

```text
Authoritative state reloaded: yes/no
Current stage: ...
Active experiment: ...
Protected data confirmed unopened: ...
Handoff discrepancies: none | ...
```
