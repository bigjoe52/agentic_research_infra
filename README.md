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

Requires Python 3.10 or newer and no runtime dependencies. The supported day-one
commands require no package download or editable installation.

```bash
python -m venv .venv
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
PYTHONPATH=src .venv/bin/python -m {{PACKAGE_NAME}}
```

Run the repository self-check:

```bash
.venv/bin/python scripts/check_harness.py
```

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
