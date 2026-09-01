# RJC Research Harness Durable Decisions

This append-only ledger contains decisions governing the reusable harness itself.
It is template-maintainer authority and is deliberately excluded from instantiated
research projects. It grants no authority over a descendant's research scope,
scientific state, institutional decisions, data access, external actions, or
deployment.

Corrections append a new stable entry that names what it supersedes. Historical
entries are never silently rewritten.

## HD-001 — Adopt explicit downstream reconciliation

**Status:** Adopted
**Date:** 2026-09-01
**Supersedes:** None

Adopt a local, Git-based downstream updater with an explicit four-way surface
model (`maintainable`, `project-owned`, `template-only`, and
`adoption-required`), semantic migration identities tied to actual upstream Git
state, per-component BASE, truthful descendant lineage, read-only
content-addressed planning, approval of the exact plan, isolated validation
before live mutation, guarded rollback, and no automatic final commit.

The initial maintainable surface is limited to the generic governance/content
scanner and its focused regression coverage. Policy migrations require separate
human-management authorization. Missing or uncertain ancestry must remain
explicit. A later harness release acquires no automatic jurisdiction over an
existing descendant.

This decision authorizes implementation and disposable verification only. It does
not authorize a release or tag, mutation of an active descendant, network update
services, background updates, package management, plugins, generalized Git
workflow management, automatic commits, or unrelated governance work.

## Entry template

```markdown
## HD-XXX — Short title

**Status:** Adopted | Provisional | Deferred | Superseded
**Date:** YYYY-MM-DD
**Supersedes:** None | HD-XXX
**Superseded by:** None | HD-XXX

Decision, rationale, consequences, limitations, and actions not authorized.
```
