"""Instantiate this template without external dependencies."""

from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {"", ".md", ".py", ".toml", ".txt", ".example", ".gitignore"}
SURFACE_PATH = ROOT / "harness" / "surface-v1.json"
DESCENDANT_HANDOFF = ROOT / "harness" / "templates" / "HANDOFF.md"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


def byte_digest(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def path_matches(path: str, rule: str) -> bool:
    return path == rule or (rule.endswith("/**") and (path == rule[:-3] or path.startswith(rule[:-2])))


def disposition(surface: dict, relative: Path) -> str:
    value = relative.as_posix()
    matches = [
        kind
        for kind, rules in surface["assignments"].items()
        for rule in rules
        if path_matches(value, rule)
    ]
    for component in surface["components"]:
        if value in component["members"]:
            matches.append(component["disposition"])
    if len(matches) != 1:
        raise SystemExit(f"template path must have exactly one surface disposition: {value}")
    return matches[0]


def source_identity() -> tuple[str | None, str | None, str]:
    commit = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True
    )
    tag = subprocess.run(
        ["git", "-C", str(ROOT), "describe", "--exact-match", "--tags", "HEAD"],
        capture_output=True,
        text=True,
    )
    dirty = subprocess.run(
        ["git", "-C", str(ROOT), "status", "--porcelain=v1"], capture_output=True, text=True
    )
    commit_value = commit.stdout.strip() if commit.returncode == 0 else None
    tag_value = tag.stdout.strip() if tag.returncode == 0 else None
    status = "verified" if commit_value and not dirty.stdout else "unverified"
    return tag_value, commit_value, status


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
    surface = json.loads(SURFACE_PATH.read_text(encoding="utf-8"))

    destination.mkdir(parents=True)
    for source in sorted(ROOT.rglob("*")):
        relative = source.relative_to(ROOT)
        if any(part in {".git", ".venv", "__pycache__", "*.egg-info"} for part in relative.parts):
            continue
        if source.is_file() and disposition(surface, relative) == "template-only":
            continue
        if source.is_dir() and relative.parts[0] in {".git", ".venv", "harness"}:
            continue
        target_relative = Path(*[replacements.get(part, part) for part in relative.parts])
        target = destination / target_relative
        if source.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.suffix in TEXT_SUFFIXES or source.name in {".gitignore", ".env.example"}:
            body_source = DESCENDANT_HANDOFF if relative == Path("docs/HANDOFF.md") else source
            body = body_source.read_text(encoding="utf-8")
            for old, new in replacements.items():
                body = body.replace(old, new)
            target.write_text(body, encoding="utf-8")
        else:
            shutil.copy2(source, target)

    tag, commit, origin_status = source_identity()
    component_manifests = {}
    for component in surface["components"]:
        paths = []
        for template_path in component["members"]:
            generated_path = template_path
            for old, new in replacements.items():
                generated_path = generated_path.replace(old, new)
            target = destination / generated_path
            paths.append({
                "path": generated_path,
                "sha256": byte_digest(target.read_bytes()) if target.is_file() else None,
            })
        component_manifests[component["id"]] = {
            "base": {"kind": "origin", "result_sha256": digest(paths), "paths": paths}
        }
    lineage = {
        "schema": 1,
        "origin": {
            "status": origin_status,
            "tag": tag,
            "commit": commit,
            "surface_id": surface["surface_id"],
            "surface_sha256": digest(surface),
            "generation_inputs_sha256": digest(replacements),
        },
        "components": component_manifests,
        "events": [],
    }
    lineage_path = destination / ".rjc-harness" / "lineage.json"
    lineage_path.parent.mkdir(parents=True, exist_ok=True)
    lineage_path.write_text(json.dumps(lineage, indent=2, sort_keys=True) + "\n", encoding="utf-8")

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
