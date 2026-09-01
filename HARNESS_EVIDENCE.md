# RJC Research Harness Evidence

This append-only file records implementation evidence about the reusable harness
itself. It is template-level evidence and is deliberately excluded from generated
research projects. It grants no project-specific research, data-access,
external-action, or deployment authority.

## H-001 — Independent portability and succession test

**Type:** Implementation  
**Status:** Supported  
**Date:** 2026-08-29  
**Supersedes:** None

- **Question:** Can a fresh Codex agent reconstruct an instantiated repository's
  authority, evidence, maturity, permissions, and handoff semantics using only
  that repository?
- **Coverage:** One disposable repository instantiated from the pre-release RJC
  Research Harness v1 and independently reviewed by a human.
- **Method and criteria:** The fresh agent was instructed to use only the example
  repository, follow its orientation path, distinguish each authority layer, avoid
  inventing authority from the handoff, run local checks, and draft a compliant
  successor handoff.
- **Result:** Human review accepted the independent test as PASS. The agent
  reconstructed the repository state, reported no outside-repository dependency,
  respected permissions and handoff boundaries, and produced a conforming proposed
  successor handoff.
- **Negative/inconclusive retention:** The test exposed one minor portability
  defect: documentation assumed `.venv/bin/python` existed when a fresh instance
  did not contain `.venv`. The v1.0.0 remediation selects an existing project venv
  or compatible system Python and does not require environment creation for
  dependency-free checks.
- **Limitations:** One accepted example is implementation evidence, not universal
  proof of agent portability. It does not establish scientific validity,
  reproducibility, data quality, empirical value, or deployment readiness for any
  generated project.
- **Conclusion:** The tested orientation and succession design is supported for
  the reviewed example, subject to the stated scope and limitations.

## H-002 — Content-scan repository-boundary correction

**Type:** Implementation
**Status:** Supported
**Date:** 2026-08-29
**Supersedes:** None

- **Question:** Can the harness exclude ignored secret-bearing and local artifacts
  from governance content scans without weakening detection in repository files?
- **Coverage:** The reusable self-check and template verification workflow;
  synthetic ignored `.env`, credential, virtual-environment, cache, and generated
  data fixtures; tracked and generated-project source contamination. No external
  project or real secret file was accessed.
- **Method and criteria:** From baseline revision `2ffb43c` plus the dirty patch,
  reproduce the recursive-scan failure with a synthetic ignored `.env`; replace
  arbitrary filesystem recursion with Git-selected tracked and non-ignored
  untracked regular files; run selection unit tests and instantiate a disposable
  project whose self-check must pass with an ignored synthetic `.env` and fail
  after contamination of a legitimate source file. Template identity and default
  configuration were used; disposable outputs remained under temporary storage.
- **Result:** The baseline scan inspected the synthetic ignored file and failed.
  The corrected unit and disposable-project checks passed, and deliberate source
  contamination was rejected. The full final verification and release identity
  are recorded in the `v1.0.1` release commit and tag.
- **Limitations:** Selection relies on Git and the correctness of project ignore
  rules. Files explicitly force-added to the Git index remain scan candidates even
  if an ignore pattern also matches them. Symlinks are not content-scanned because
  reading them would inspect their targets rather than repository-stored link
  text. This is implementation evidence, not scientific evidence.
- **Conclusion:** The narrow repository-membership correction is supported for
  the covered harness and generated-project workflows.

## H-003 — Content-scan exclusion reproducibility correction

**Type:** Implementation
**Status:** Supported
**Date:** 2026-08-29
**Supersedes:** None

- **Question:** Can governance content-scan candidates depend only on transferable,
  repository-owned state while preserving the v1.0.1 repository boundary?
- **Coverage:** The initialized-repository and pre-`git init` temporary-index
  selection paths; synthetic global `core.excludesFile`, `.git/info/exclude`,
  project `.gitignore`, tracked ignored files, untracked legitimate files,
  forbidden content, and symlink behavior. No real user exclude file was read.
- **Method and criteria:** After releasing `v1.0.1` at revision `d19adb7`, compare
  identical synthetic working trees under neutral and file-excluding global Git
  configurations. Confirm whether `--exclude-standard` changes candidates, then
  replace it with project-owned per-directory `.gitignore` selection. Both paths
  must become invariant to global and repository-local excludes while retaining
  all previously intended project-owned selection and content-detection behavior.
- **Result:** The post-release audit confirmed that `v1.0.1` produced different
  candidate sets under different global Git excludes in both paths and could also
  be influenced by `.git/info/exclude` in initialized repositories. The corrected
  regression and disposable-project verification passed. Final release identity
  is recorded in the `v1.0.2` release commit and tag.
- **Limitations:** Selection still relies on Git and on complete project-owned
  `.gitignore` rules. Machine-local exclusions intentionally do not protect files
  from governance scans; local secret/artifact patterns must be transferred into
  the project `.gitignore`. Tracked files remain candidates even when a project
  ignore rule matches. Symlinks remain excluded from content reading.
- **Conclusion:** Project-owned exclusion selection is supported as reproducible
  harness implementation behavior, not as scientific evidence.

## H-004 — Explicit downstream reconciliation verification

**Type:** Implementation
**Status:** Supported
**Date:** 2026-09-01
**Supersedes:** None

- **Question:** Can the harness plan, approve, isolate, apply, validate, and record
  selective downstream infrastructure migrations without acquiring authority over
  descendant institutional state or claiming unsupported ancestry?
- **Coverage:** Canonical plan identity; declarative surface enforcement; native
  lineage; verified, partially verified, and unverified legacy bootstrap;
  per-component BASE; exact-input invalidation; explicit local-equivalence
  attestation; policy-authorization refusal; detached validation; safe and unsafe
  live rollback; and the synthetic historical `v1.0.0 -> v1.0.1 -> v1.0.2`
  scanner case. All descendants and outputs were disposable under temporary
  storage. No active research repository or protected data was accessed.
- **Method and criteria:** From revision `6c3eeab` plus the dirty implementation,
  use surface manifest SHA-256
  `e7d55ef536f730b97e2ae5c7ed6017c763d1db17ba62442acec2d480db869393`
  and the two historical migration descriptors; run
  `python3 -m unittest tests/test_harness_update.py -v`,
  `python3 scripts/check_template.py`, direct maintainer-file byte compilation,
  and `git diff --check`. The historical fixture must preserve independent
  project state, detect a deliberately incomplete specification-derived scanner
  port, restore the actual pre-Git and symlink safeguards, adopt repository-owned
  exclusion authority, record two semantic migrations, and leave descendant
  `HEAD` unchanged. Failure tests must leave the live tree untouched after
  isolated failure, reverse only an exact live mutation, and refuse cleanup after
  an intervening mutation.
- **Result:** Eleven updater tests passed. The generated-project suite passed five
  tests, its self-check passed, and the template check passed. The historical
  fixture was blocked before explicit conflict resolution, then incorporated the
  actual tagged scanner states including the temporary-index pre-Git path,
  non-symlink selection, and `.gitignore`-only exclusion authority. Project-owned
  founding state was byte-preserved, template-only material was absent, two exact
  migration identities were recorded, and no automatic commit occurred. Both
  guarded rollback branches and all three bootstrap truth states behaved as
  declared. Direct compilation and diff whitespace checks passed at
  `2026-09-01T11:14:23-04:00`.
- **Limitations:** The MVP requires clean Git repositories and sufficient
  reachable history, supports regular text-file reconciliation only, uses local
  repositories and tags without signature verification, and syntactically checks
  management authorization without authenticating organizational identity. The
  initial maintainable surface contains only the scanner and focused regression
  test. A dirty or untagged harness checkout produces unverified native origin
  lineage. Plans and failed reports are local/ephemeral unless separately promoted
  as material evidence.
- **Conclusion:** The approved narrow updater architecture is supported for the
  covered disposable workflows and is ready for separate release review. This
  evidence does not authorize a release, tag, active-descendant mutation, policy
  adoption, scientific claim, protected-data access, or deployment.
