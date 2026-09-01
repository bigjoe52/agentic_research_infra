# {{PROJECT_TITLE}}

{{PROJECT_SUMMARY}}

This repository uses **RJC Research Harness v1**, a lightweight framework for
independent quantitative research. Its controls grow with research maturity; a
new exploratory project does not begin with validation-stage bureaucracy.

## Orientation

New contributors and agents start with `AGENTS.md`, then follow its authoritative
orientation path. In brief:

1. `docs/THE_BEGINNING.md` — founding intent and scope
2. `docs/DECISIONS.md` — adopted constraints
3. `docs/RESEARCH_LOG.md` — evidence
4. `docs/ROADMAP.md` — current state
5. this README — supported workflows
6. `docs/HANDOFF.md` — non-authoritative navigation aid only

## Quick start

Requires Python 3.10 or newer, Git, and no Python runtime dependencies. The
supported day-one commands require no package download or editable installation.

```bash
if [ -x .venv/bin/python ]; then
  PROJECT_PYTHON=.venv/bin/python
else
  PROJECT_PYTHON=python
fi

PYTHONPATH=src "$PROJECT_PYTHON" -m unittest discover -s tests -v
PYTHONPATH=src "$PROJECT_PYTHON" -m {{PACKAGE_NAME}}
```

Run the repository self-check:

```bash
"$PROJECT_PYTHON" scripts/check_harness.py
```

Repository-wide content checks inspect regular, non-symlink files selected by
Git: tracked files plus untracked files not excluded by repository-owned
`.gitignore` rules. Before a generated project has Git metadata, the check applies
the same selection with a temporary Git index. User/global Git excludes and
`.git/info/exclude` do not affect governance scan results. Ignored secrets,
environments, caches, and generated artifacts are therefore outside the scan
boundary when recorded in the transferable project ignore rules.

This selection does not create or modify an environment. Use the project virtual
environment when it already exists; otherwise a compatible system Python is valid
for these dependency-free, read-only checks. Create a virtual environment and
install dependencies only when repository modification is authorized and the
project actually requires dependencies. A handoff cannot authorize that setup.

## Research workflow

Day-one exploration requires a stated question, scoped data, an honest evidence
entry, basic result provenance, and tests proportional to the code. Candidate
promotion adds an experiment registration. Protected validation adds explicit
access boundaries and a pre-access review. Deployment controls appear only if the
project actually approaches consequential use. See `research/README.md`.

## Creating a project from the template

From the template repository:

```bash
python scripts/instantiate.py ../my_research \
  --project-name my_research \
  --title "My Research Project" \
  --summary "A concise, neutral research objective."
```

The destination must not already exist. The generated repository contains no
adopted scientific conclusion; all `PROJECT-SPECIFIC` fields require review.
Instantiation also writes `.rjc-harness/lineage.json`, recording the exact local
harness source identity when it can be verified. Harness-maintainer decisions,
evidence, release metadata, migration catalogs, and updater code are not copied
into the descendant.

## Reconciling downstream harness maintenance

Updates never propagate automatically. Run the updater from an exact local
harness checkout against a clean, committed descendant. Planning is read-only and
names semantic migrations explicitly:

```bash
python3 /path/to/rjc_harness/scripts/harness_update.py plan \
  --project /path/to/descendant \
  --upstream /path/to/rjc_harness \
  --target v1.0.2 \
  --migration governance-scan/2026-001-git-file-selection \
  --migration governance-scan/2026-002-project-owned-exclusions \
  --output /safe/local/plan.json
```

Review the complete plan, including exclusions, conflicts, validation, and
lineage. Apply only the exact approved digest:

```bash
python3 /path/to/rjc_harness/scripts/harness_update.py apply \
  --project /path/to/descendant \
  --upstream /path/to/rjc_harness \
  --plan /safe/local/plan.json \
  --approve sha256:<exact-plan-digest>
```

Application validates first in a detached temporary worktree and then in the live
tree. Successful content and lineage remain uncommitted for maintainer inspection;
the updater never creates the final commit. A failed live validation is reversed
only when the updater can prove that its exact mutation remains untouched.

Older descendants without lineage start with `bootstrap-plan` and
`bootstrap-apply`. Bootstrap uses reachable Git evidence and records `verified`,
`partially-verified`, or `unverified`; it never manufactures an origin tag.
Implementation migrations cannot change project-owned or template-only material.
Governance migrations are separate and require an exact human-management
authorization record.
