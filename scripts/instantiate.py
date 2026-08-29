"""Instantiate this template without external dependencies."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import re
import shutil


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {"", ".md", ".py", ".toml", ".txt", ".example", ".gitignore"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument(
        "--question",
        default="[PROJECT-SPECIFIC: state the founding research question.]",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not re.fullmatch(r"[a-z][a-z0-9_]*", args.project_name):
        raise SystemExit("--project-name must be a valid lowercase Python package name")
    destination = args.destination.resolve()
    if destination.exists():
        raise SystemExit(f"destination already exists: {destination}")
    if ROOT == destination or ROOT in destination.parents:
        raise SystemExit("destination must be outside the template repository")

    replacements = {
        "{{PROJECT_NAME}}": args.project_name,
        "{{PACKAGE_NAME}}": args.project_name,
        "{{PROJECT_TITLE}}": args.title,
        "{{PROJECT_SUMMARY}}": args.summary,
        "{{PROJECT_QUESTION}}": args.question,
        "{{CREATED_DATE}}": date.today().isoformat(),
    }

    destination.mkdir(parents=True)
    for source in sorted(ROOT.rglob("*")):
        relative = source.relative_to(ROOT)
        if relative in {Path("scripts/instantiate.py"), Path("HARNESS_EVIDENCE.md")}:
            continue
        if any(part in {".git", ".venv", "__pycache__", "*.egg-info"} for part in relative.parts):
            continue
        target_relative = Path(*[replacements.get(part, part) for part in relative.parts])
        target = destination / target_relative
        if source.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.suffix in TEXT_SUFFIXES or source.name in {".gitignore", ".env.example"}:
            body = source.read_text(encoding="utf-8")
            for old, new in replacements.items():
                body = body.replace(old, new)
            target.write_text(body, encoding="utf-8")
        else:
            shutil.copy2(source, target)

    unresolved = []
    for path in destination.rglob("*"):
        if path.is_file():
            try:
                if "{{" in path.read_text(encoding="utf-8"):
                    unresolved.append(str(path.relative_to(destination)))
            except UnicodeDecodeError:
                pass
    if unresolved:
        shutil.rmtree(destination)
        raise SystemExit(f"unresolved template tokens: {unresolved}")
    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
