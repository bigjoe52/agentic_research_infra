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


def expect_scan_failure(project: Path) -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/check_harness.py"],
        cwd=project,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode == 0:
        raise SystemExit("contaminated legitimate project file passed the content scan")
    if "forbidden originating-project dependency/case law" not in completed.stderr:
        raise SystemExit("contaminated project failed for an unexpected reason")


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
        forbidden_marker = "options" + "_flow"
        (project / ".env").write_text(
            f"synthetic_secret={forbidden_marker}\n", encoding="utf-8"
        )
        run(sys.executable, "scripts/check_harness.py", cwd=project)
        legitimate_source = project / "src" / "portable_example" / "project.py"
        original_source = legitimate_source.read_text(encoding="utf-8")
        legitimate_source.write_text(
            original_source + f"\nFORBIDDEN_DEPENDENCY = {forbidden_marker!r}\n",
            encoding="utf-8",
        )
        expect_scan_failure(project)
        legitimate_source.write_text(original_source, encoding="utf-8")
        run(sys.executable, "-m", "compileall", "-q", "src", "tests", "scripts", cwd=project)
        if (project / "scripts/instantiate.py").exists():
            raise SystemExit("generated project contains template-generation machinery")
        if (project / "HARNESS_EVIDENCE.md").exists():
            raise SystemExit("generated project imported template-level evidence")
    print("RJC Research Harness v1.0.1 template check: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
