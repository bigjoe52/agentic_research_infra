"""Static institutional checks for an instantiated RJC Research Harness v1 repo."""

from __future__ import annotations

import re
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HARNESS_VERSION = "1.0.1"
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


def repository_files(root: Path = ROOT) -> list[Path]:
    """Return tracked and non-ignored untracked files belonging to ``root``."""
    git_root = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
    )
    if git_root.returncode == 0 and Path(git_root.stdout.strip()).resolve() == root.resolve():
        command = ["git", "-C", str(root), "ls-files", "--cached", "--others",
                   "--exclude-standard", "-z"]
        completed = subprocess.run(command, check=True, capture_output=True)
    else:
        # A generated project may be checked before `git init`. A temporary empty
        # index gives it the same Git-ignore selection semantics without writing
        # repository metadata into the project.
        with tempfile.TemporaryDirectory(prefix="rjc-harness-index-") as directory:
            git_dir = Path(directory) / "repo.git"
            subprocess.run(
                ["git", "init", "--quiet", "--bare", str(git_dir)],
                check=True,
                capture_output=True,
            )
            completed = subprocess.run(
                ["git", f"--git-dir={git_dir}", f"--work-tree={root}", "ls-files",
                 "--others", "--exclude-standard", "-z"],
                check=True,
                capture_output=True,
            )
    relative_paths = completed.stdout.decode("utf-8", errors="surrogateescape").split("\0")
    return [
        root / path
        for path in relative_paths
        if path and (root / path).is_file() and not (root / path).is_symlink()
    ]


def forbidden_case_law(paths: list[Path], root: Path = ROOT) -> list[tuple[str, str]]:
    leaks = []
    for path in paths:
        try:
            body = path.read_text(encoding="utf-8").lower()
        except UnicodeDecodeError:
            continue
        leaks.extend(
            (str(path.relative_to(root)), term)
            for term in FORBIDDEN_CASE_LAW
            if term in body
        )
    return leaks


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

    readme = text("README.md")
    check('if [ -x .venv/bin/python ]; then' in readme,
          "existing-project-venv selection is missing")
    check("PROJECT_PYTHON=python" in readme,
          "compatible system-Python fallback is missing")
    check("only when repository modification is authorized" in readme,
          "environment-creation authority boundary is missing")

    leaks = forbidden_case_law(repository_files())
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
    print(f"RJC Research Harness v{HARNESS_VERSION} self-check: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
