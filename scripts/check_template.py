"""Instantiate and verify a disposable project from the template."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(*args: str, cwd: Path = ROOT) -> None:
    completed = subprocess.run(args, cwd=cwd, check=False)
    if completed.returncode:
        raise SystemExit(completed.returncode)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="rjc-harness-check-") as directory:
        project = Path(directory) / "portable_example"
        run(
            sys.executable,
            "scripts/instantiate.py",
            str(project),
            "--project-name",
            "portable_example",
            "--title",
            "Portable Example",
            "--summary",
            "A generated harness verification project.",
            "--question",
            "[PROJECT-SPECIFIC: define the founding research question.]",
        )
        run(sys.executable, "scripts/check_harness.py", cwd=project)
        run(sys.executable, "-m", "compileall", "-q", "src", "tests", "scripts", cwd=project)
        if (project / "scripts/instantiate.py").exists():
            raise SystemExit("generated project contains template-generation machinery")
        if (project / "HARNESS_EVIDENCE.md").exists():
            raise SystemExit("generated project imported template-level evidence")
    print("RJC Research Harness v1 template check: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
