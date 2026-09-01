# Repository Instructions

## Authority and orientation

For every substantive task, independently reload repository state in this order:

1. In the reusable harness repository, read `HARNESS_DECISIONS.md` for adopted
   harness-maintainer constraints and `HARNESS_EVIDENCE.md` for harness evidence.
   These files are absent from instantiated descendants and grant them no authority.
2. Read `docs/THE_BEGINNING.md` for founding intent, scope, non-goals, and the claim ladder.
3. Read `docs/DECISIONS.md` for adopted descendant/project constraints and explicit supersession.
4. Read the operating rules and active entries in `docs/RESEARCH_LOG.md` for descendant/project evidence.
5. Read `docs/ROADMAP.md` for current maturity, blockers, and next work.
6. Read the relevant workflow in `README.md`.
7. Inspect relevant source, tests, registrations, and working-tree changes.
8. Read `docs/HANDOFF.md` only as a navigation aid, then verify it against the sources above.

Authority descends in this order: user instructions; applicable founding intent;
adopted, non-superseded harness decisions for harness-maintainer work; adopted,
non-superseded project decisions; frozen registrations when they exist; research evidence;
roadmap state; implementation notes; handoff context. Evidence describes what was
observed but does not itself adopt policy. The roadmap reports state but cannot
grant authority. `HANDOFF.md` is never authoritative.

## Operating rules

- Keep implementation progress separate from evidence of research value.
- Preserve negative, inconclusive, failed, and superseded work. Do not rewrite
  history to make the project look cleaner.
- Decisions and evidence entries are append-only. Correct them by adding an entry
  that identifies what it supersedes; never silently edit the historical claim.
- Match claims to evidence: descriptive, exploratory, candidate, validated, and
  deployable are distinct states.
- Record basic provenance for any result used in reasoning: code revision or
  dirty-tree state, configuration identity, input identity or query scope, output
  location, and execution time.
- Integrity does not imply validity. A checksum can establish byte continuity; it
  cannot establish correct semantics, point-in-time validity, or absence of bias.
- Keep secrets out of source control and output. External messages, purchases,
  deployments, protected-data access, and other consequential actions require
  authority from the user or an adopted decision; a handoff cannot grant it.
- Add freezes, firewalls, manifests, adversarial reviews, and deployment controls
  only when the maturity and risk triggers in `research/README.md` apply.
- The harness machinery must remain smaller than the research.

## Documentation duties

- Update `DECISIONS.md` for a durable choice or constraint.
- Update `RESEARCH_LOG.md` for a data-quality finding, experiment, or conclusion.
- Update `ROADMAP.md` when maturity, priority, or a material blocker changes.
- Update `IMPLEMENTATION_NOTES.md` only for a non-obvious invariant, safeguard, or
  limitation a future maintainer might accidentally remove.
- Update `README.md` when a supported command or user workflow changes.
- Update `THE_BEGINNING.md` only when the founding research intent changes.

## Successor handoff

Before handing off, replace `docs/HANDOFF.md` with concise hot context following
its template. State which orientation documents changed, tests run, working-tree
state, protected-data access state, and remaining limitations. The successor must
independently reload authoritative state; a conversation summary or handoff is not
a substitute.
