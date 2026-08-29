"""Static institutional checks for an instantiated RJC Research Harness v1 repo."""

from __future__ import annotations

import re
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "AGENTS.md",
    "README.md",
    "docs/THE_BEGINNING.md",
    "docs/ROADMAP.md",
    "docs/DECISIONS.md",
    "docs/RESEARCH_LOG.md",
    "docs/IMPLEMENTATION_NOTES.md",
    "docs/HANDOFF.md",
    "research/README.md",
    "config/project.toml",
    "data/README.md",
    "pyproject.toml",
    ".gitignore",
}
FORBIDDEN_CASE_LAW = (
    "options" + "_flow",
    "poly" + "gon",
    "data" + "bento",
    "theta" + "data",
    "sch" + "wab",
    "phase " + "1a",
    "phase" + "1a",
    "phase " + "1b",
    "phase" + "1b",
    "occ " + "memo",
    "g" + "ex",
)


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    missing = sorted(path for path in REQUIRED if not (ROOT / path).is_file())
    check(not missing, f"missing required files: {missing}")

    agents = text("AGENTS.md").lower()
    ordered = [
        "docs/the_beginning.md",
        "docs/decisions.md",
        "docs/research_log.md",
        "docs/roadmap.md",
        "readme.md",
        "docs/handoff.md",
    ]
    positions = [agents.index(item) for item in ordered]
    check(positions == sorted(positions), "orientation path is missing or ambiguous")

    handoff = text("docs/HANDOFF.md").lower()
    check("non-authoritative hot context" in handoff, "handoff authority warning missing")
    for phrase in ("cannot grant experimental access", "protected-data access", "external-action authority"):
        check(phrase in handoff, f"handoff boundary missing: {phrase}")

    decisions = text("docs/DECISIONS.md").lower()
    evidence = text("docs/RESEARCH_LOG.md").lower()
    check("append-only" in decisions and "supersedes" in decisions, "decision history rule missing")
    check("append-only" in evidence and "inconclusive" in evidence and "supersedes" in evidence,
          "evidence retention/supersession rule missing")

    extensions = text("research/README.md").lower()
    check("no frozen registration" in extensions, "day-one proportionality is unclear")
    check("machinery must remain smaller than the research" in agents,
          "small-harness principle missing")

    tracked_text = []
    for path in ROOT.rglob("*"):
        if path.is_file() and ".git" not in path.parts and ".venv" not in path.parts:
            try:
                tracked_text.append((path, path.read_text(encoding="utf-8").lower()))
            except UnicodeDecodeError:
                pass
    leaks = [(str(path.relative_to(ROOT)), term) for path, body in tracked_text
             for term in FORBIDDEN_CASE_LAW if term in body]
    check(not leaks, f"forbidden originating-project dependency/case law: {leaks}")

    placeholders = text("docs/THE_BEGINNING.md") + text("config/project.toml")
    check("PROJECT-SPECIFIC PLACEHOLDER" in placeholders,
          "project-specific placeholders are not conspicuous")

    ignore = text(".gitignore")
    for secret in (".env", "*.pem", "*.key", "credentials.json", "secrets.json"):
        check(re.search(rf"(?m)^{re.escape(secret)}$", ignore) is not None,
              f"secret ignore missing: {secret}")

    environment = os.environ.copy()
    source_path = str(ROOT / "src")
    environment["PYTHONPATH"] = source_path + os.pathsep + environment.get("PYTHONPATH", "")
    completed = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=ROOT,
        check=False,
        env=environment,
    )
    check(completed.returncode == 0, "unit tests failed")
    print("RJC Research Harness v1 self-check: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
