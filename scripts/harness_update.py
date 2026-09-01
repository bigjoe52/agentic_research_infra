"""Explicit local reconciliation for RJC Research Harness descendants."""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from typing import Any


SCHEMA = 1
LINEAGE = Path(".rjc-harness/lineage.json")
SURFACE = Path("harness/surface-v1.json")


class UpdaterError(RuntimeError):
    pass


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


def byte_digest(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UpdaterError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict) or value.get("schema") != SCHEMA:
        raise UpdaterError(f"unsupported schema in {path}")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run(args: list[str], *, cwd: Path, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    completed = subprocess.run(args, cwd=cwd, capture_output=True)
    if check and completed.returncode:
        detail = completed.stderr.decode(errors="replace").strip()
        raise UpdaterError(f"command failed ({' '.join(args)}): {detail}")
    return completed


def git(root: Path, *args: str, check: bool = True) -> bytes:
    return run(["git", *args], cwd=root, check=check).stdout


def git_text(root: Path, *args: str) -> str:
    return git(root, *args).decode(errors="surrogateescape").strip()


def clean_state(project: Path) -> dict[str, str]:
    top = Path(git_text(project, "rev-parse", "--show-toplevel")).resolve()
    if top != project.resolve():
        raise UpdaterError("project must be the root of its Git working tree")
    status = git(project, "--no-optional-locks", "status", "--porcelain=v1", "-z")
    if status:
        raise UpdaterError("project working tree and index must be clean")
    head = git_text(project, "rev-parse", "HEAD")
    tree = git_text(project, "rev-parse", "HEAD^{tree}")
    lineage_blob = git_text(project, "rev-parse", f"HEAD:{LINEAGE}") if (project / LINEAGE).exists() else ""
    return {"head": head, "index_tree": tree, "lineage_blob": lineage_blob}


def blob_at(repo: Path, commit: str, path: str) -> bytes | None:
    completed = run(["git", "show", f"{commit}:{path}"], cwd=repo, check=False)
    return completed.stdout if completed.returncode == 0 else None


def worktree_blob(project: Path, path: str) -> bytes | None:
    target = project / path
    if not target.exists() or target.is_symlink() or not target.is_file():
        return None
    return target.read_bytes()


def status_bytes(project: Path) -> bytes:
    return git(project, "--no-optional-locks", "status", "--porcelain=v1", "-z")


def encoded(value: bytes | None) -> str | None:
    return None if value is None else base64.b64encode(value).decode("ascii")


def decoded(value: str | None) -> bytes | None:
    return None if value is None else base64.b64decode(value)


def path_matches(path: str, rule: str) -> bool:
    return path == rule or (rule.endswith("/**") and (path == rule[:-3] or path.startswith(rule[:-2])))


def load_surface(upstream: Path) -> dict[str, Any]:
    surface = read_json(upstream / SURFACE)
    if set(surface) != {"schema", "surface_id", "components", "assignments"}:
        raise UpdaterError("surface manifest contains unknown or missing fields")
    return surface


def component(surface: dict[str, Any], component_id: str) -> dict[str, Any]:
    matches = [item for item in surface["components"] if item["id"] == component_id]
    if len(matches) != 1 or matches[0].get("disposition") != "maintainable":
        raise UpdaterError(f"component is not maintainable: {component_id}")
    return matches[0]


def ensure_component_path(item: dict[str, Any], path: str) -> None:
    if path not in item["members"]:
        raise UpdaterError(f"migration path is outside maintainable component: {path}")


def migration_path(upstream: Path, migration_id: str) -> Path:
    slug = migration_id.replace("/", "--")
    return upstream / "harness" / "migrations" / slug / "migration.json"


def load_migration(upstream: Path, migration_id: str, surface: dict[str, Any]) -> dict[str, Any]:
    path = migration_path(upstream, migration_id)
    migration = read_json(path)
    required = {
        "schema", "id", "authority_class", "component", "title", "depends_on",
        "upstream", "changes", "validation",
    }
    if set(migration) != required or migration["id"] != migration_id:
        raise UpdaterError(f"invalid migration descriptor: {path}")
    if migration["authority_class"] not in {"implementation", "adoption-required"}:
        raise UpdaterError("invalid migration authority class")
    item = component(surface, migration["component"])
    for change in migration["changes"]:
        if set(change) != {"path", "operation", "base_sha256", "target_sha256"}:
            raise UpdaterError("invalid migration change")
        ensure_component_path(item, change["path"])
    base = migration["upstream"]["base_commit"]
    target = migration["upstream"]["target_commit"]
    for change in migration["changes"]:
        before = blob_at(upstream, base, change["path"])
        after = blob_at(upstream, target, change["path"])
        if (byte_digest(before) if before is not None else None) != change["base_sha256"]:
            raise UpdaterError(f"base content mismatch for {change['path']}")
        if (byte_digest(after) if after is not None else None) != change["target_sha256"]:
            raise UpdaterError(f"target content mismatch for {change['path']}")
    actual = git(upstream, "diff", "--binary", "--full-index", base, target, "--", *[c["path"] for c in migration["changes"]])
    if byte_digest(actual) != migration["upstream"]["full_diff_sha256"]:
        raise UpdaterError(f"authoritative upstream diff mismatch for {migration_id}")
    return migration


def three_way(base: bytes, local: bytes, upstream: bytes) -> tuple[str, bytes | None]:
    with tempfile.TemporaryDirectory(prefix="rjc-merge-") as directory:
        root = Path(directory)
        local_path, base_path, upstream_path = root / "local", root / "base", root / "upstream"
        local_path.write_bytes(local)
        base_path.write_bytes(base)
        upstream_path.write_bytes(upstream)
        completed = subprocess.run(
            ["git", "merge-file", "-p", str(local_path), str(base_path), str(upstream_path)],
            capture_output=True,
        )
        if completed.returncode == 0:
            return "clean-merge", completed.stdout
        return "conflict", None


def reconcile(base: bytes | None, local: bytes | None, upstream: bytes | None, force_upstream: bool) -> tuple[str, bytes | None]:
    if local == upstream:
        return "already-identical", local
    if local == base:
        return "cleanly-applicable", upstream
    if upstream == base:
        return "local-only", local
    if force_upstream:
        return "resolved-upstream", upstream
    if base is not None and local is not None and upstream is not None:
        return three_way(base, local, upstream)
    return "conflict", None


def lineage(project: Path) -> dict[str, Any]:
    path = project / LINEAGE
    if not path.is_file():
        raise UpdaterError("committed lineage is required; run bootstrap-plan first")
    return read_json(path)


def recorded_component_base(
    project: Path, current_lineage: dict[str, Any], component_id: str, path: str
) -> bytes | None:
    state = current_lineage.get("components", {}).get(component_id, {})
    event_id = state.get("base_event")
    if event_id:
        commits = git_text(project, "rev-list", "--reverse", "HEAD", "--", str(LINEAGE)).splitlines()
        for commit in commits:
            raw = blob_at(project, commit, str(LINEAGE))
            if raw is None:
                continue
            candidate = json.loads(raw)
            event = next((item for item in candidate.get("events", []) if item.get("event_id") == event_id), None)
            if event is None:
                continue
            expected = next((item["sha256"] for item in event["paths"] if item["path"] == path), None)
            value = blob_at(project, commit, path)
            actual = byte_digest(value) if value is not None else None
            if actual != expected:
                raise UpdaterError(f"base-integrity-failed for {component_id}:{path}")
            return value
        raise UpdaterError(f"base-unavailable for {component_id}:{path}")
    origin_base = state.get("base")
    if origin_base:
        expected = next((item["sha256"] for item in origin_base.get("paths", []) if item["path"] == path), None)
        roots = root_commits(project)
        matches = [blob_at(project, commit, path) for commit in roots]
        matches = [value for value in matches if (byte_digest(value) if value is not None else None) == expected]
        if len(matches) == 1:
            return matches[0]
        raise UpdaterError(f"base-unavailable for {component_id}:{path}")
    return None


def plan_payload(args: argparse.Namespace) -> dict[str, Any]:
    project, upstream = args.project.resolve(), args.upstream.resolve()
    state = clean_state(project)
    current_lineage = lineage(project)
    surface = load_surface(upstream)
    target_commit = git_text(upstream, "rev-parse", f"{args.target}^{{}}")
    force = set(args.resolve_upstream or [])
    equivalent: dict[str, dict[str, Any]] = {}
    for specification in args.local_equivalent or []:
        migration_id, separator, filename = specification.partition("=")
        if not separator:
            raise UpdaterError("--local-equivalent must be MIGRATION_ID=ATTESTATION.json")
        attestation = read_json(Path(filename).resolve())
        if set(attestation) != {"schema", "reviewer", "basis"} or not attestation["reviewer"] or not attestation["basis"]:
            raise UpdaterError("invalid local-equivalence attestation")
        equivalent[migration_id] = attestation
    adopted = {event["migration_id"] for event in current_lineage.get("events", []) if event["kind"] == "migration-adopted"}
    origin = current_lineage.get("origin", {})
    origin_commit = origin.get("commit") if origin.get("status") == "verified" else None
    virtual: dict[str, bytes | None] = {}
    actions: list[dict[str, Any]] = []
    migrations: list[dict[str, Any]] = []
    blocked = False
    prior_targets: dict[str, bytes | None] = {}
    validation: list[list[str]] = []
    initialized_components: set[str] = set()
    for migration_id in args.migration:
        migration = load_migration(upstream, migration_id, surface)
        if migration_id in adopted:
            raise UpdaterError(f"migration already adopted: {migration_id}")
        missing = [dep for dep in migration["depends_on"] if dep not in adopted and dep not in [m["id"] for m in migrations]]
        if missing:
            raise UpdaterError(f"missing migration dependencies: {missing}")
        if run(["git", "merge-base", "--is-ancestor", migration["upstream"]["target_commit"], target_commit], cwd=upstream, check=False).returncode:
            raise UpdaterError(f"migration is not contained in target {args.target}")
        if origin_commit and run(
            ["git", "merge-base", "--is-ancestor", migration["upstream"]["target_commit"], origin_commit],
            cwd=upstream,
            check=False,
        ).returncode == 0:
            item = component(surface, migration["component"])
            for member in item["members"]:
                recorded_component_base(project, current_lineage, migration["component"], member)
            migrations.append({
                "id": migration_id,
                "component": migration["component"],
                "authority_class": migration["authority_class"],
                "descriptor_sha256": digest(migration),
                "target_commit": migration["upstream"]["target_commit"],
                "classifications": ["included-in-origin"],
                "local_equivalence_attestation": None,
            })
            continue
        migration_actions = []
        for change in migration["changes"]:
            path = change["path"]
            if path in prior_targets:
                base = prior_targets[path]
            elif migration["component"] not in initialized_components:
                recorded = recorded_component_base(project, current_lineage, migration["component"], path)
                base = recorded if recorded is not None else blob_at(upstream, migration["upstream"]["base_commit"], path)
            else:
                base = blob_at(upstream, migration["upstream"]["base_commit"], path)
            local = virtual.get(path, worktree_blob(project, path))
            target = blob_at(upstream, migration["upstream"]["target_commit"], path)
            classification, result = reconcile(base, local, target, migration_id in force)
            if result is None and migration_id in equivalent:
                classification, result = "local-equivalent", local
            if result is None:
                blocked = True
            action = {
                "migration_id": migration_id,
                "component": migration["component"],
                "path": path,
                "classification": classification,
                "before_sha256": byte_digest(local) if local is not None else None,
                "after_sha256": byte_digest(result) if result is not None else None,
                "before": encoded(local),
                "after": encoded(result),
            }
            actions.append(action)
            migration_actions.append(action)
            if result is not None:
                virtual[path] = result
            prior_targets[path] = target
        initialized_components.add(migration["component"])
        migrations.append({
            "id": migration_id,
            "component": migration["component"],
            "authority_class": migration["authority_class"],
            "descriptor_sha256": digest(migration),
            "target_commit": migration["upstream"]["target_commit"],
            "classifications": [item["classification"] for item in migration_actions],
            "local_equivalence_attestation": equivalent.get(migration_id),
        })
        validation.extend(migration["validation"])
    payload = {
        "project": {**state, "root": str(project), "lineage_sha256": digest(current_lineage)},
        "upstream": {"root": str(upstream), "target_tag": args.target, "target_commit": target_commit, "surface_sha256": digest(surface)},
        "migrations": migrations,
        "actions": actions,
        "validation": validation,
        "blocked": blocked,
    }
    return payload


def command_plan(args: argparse.Namespace) -> int:
    payload = plan_payload(args)
    document = {"schema": SCHEMA, "kind": "migration-plan", "payload": payload}
    document["plan_id"] = digest(payload)
    write_json(args.output.resolve(), document)
    print(json.dumps({"plan_id": document["plan_id"], "blocked": payload["blocked"], "actions": [{k: a[k] for k in ("path", "classification")} for a in payload["actions"]]}, indent=2))
    return 2 if payload["blocked"] else 0


def root_commits(project: Path) -> list[str]:
    return git_text(project, "rev-list", "--max-parents=0", "HEAD").splitlines()


def inferred_instantiation_inputs(project: Path, root_commit: str) -> dict[str, str] | None:
    required = {
        "config": blob_at(project, root_commit, "config/project.toml"),
        "readme": blob_at(project, root_commit, "README.md"),
        "beginning": blob_at(project, root_commit, "docs/THE_BEGINNING.md"),
    }
    if any(value is None for value in required.values()):
        return None
    config = required["config"].decode(errors="replace")
    readme = required["readme"].decode(errors="replace")
    beginning = required["beginning"].decode(errors="replace")
    name = re.search(r'(?m)^(?:name|project_name) = "([a-z][a-z0-9_]*)"$', config)
    readme_lines = readme.splitlines()
    title = readme_lines[0][2:] if readme_lines and readme_lines[0].startswith("# ") else ""
    summary = next((line for line in readme_lines[1:] if line.strip()), "")
    question_match = re.search(r"(?m)^## Research question\n\n(.+)$", beginning)
    if not name or not title or not summary or not question_match:
        return None
    return {"project_name": name.group(1), "title": title, "summary": summary, "question": question_match.group(1)}


def reconstructed_candidate(upstream: Path, tag: str, inputs: dict[str, str], root: Path) -> Path | None:
    archive = run(["git", "archive", "--format=tar", tag], cwd=upstream, check=False)
    if archive.returncode:
        return None
    source = root / "source"
    destination = root / "generated"
    source.mkdir()
    with tarfile.open(fileobj=io.BytesIO(archive.stdout), mode="r:") as bundle:
        members = bundle.getmembers()
        if any(member.name.startswith("/") or ".." in Path(member.name).parts for member in members):
            raise UpdaterError("unsafe path in local upstream archive")
        bundle.extractall(source)
    completed = run(
        [
            sys.executable, "scripts/instantiate.py", str(destination),
            "--project-name", inputs["project_name"], "--title", inputs["title"],
            "--summary", inputs["summary"], "--question", inputs["question"],
        ],
        cwd=source,
        check=False,
    )
    return destination if completed.returncode == 0 else None


def compare_reconstruction(project: Path, root_commit: str, generated: Path) -> tuple[int, int, bool]:
    generated_files = {
        path.relative_to(generated).as_posix(): path.read_bytes()
        for path in generated.rglob("*")
        if path.is_file() and not path.is_symlink() and ".rjc-harness" not in path.parts
    }
    root_paths = set(git_text(project, "ls-tree", "-r", "--name-only", root_commit).splitlines())
    considered_root = {path for path in root_paths if not path.startswith(".rjc-harness/")}
    matches = sum(blob_at(project, root_commit, path) == value for path, value in generated_files.items())
    exact = set(generated_files) == considered_root and matches == len(generated_files)
    return matches, len(generated_files), exact


def bootstrap_payload(args: argparse.Namespace) -> dict[str, Any]:
    project, upstream = args.project.resolve(), args.upstream.resolve()
    state = clean_state(project)
    if (project / LINEAGE).exists():
        raise UpdaterError("lineage already exists")
    surface = load_surface(upstream)
    candidates = args.candidate or ["v1.0.0", "v1.0.1", "v1.0.2"]
    roots = root_commits(project)
    evidence = []
    for tag in candidates:
        completed = run(["git", "rev-parse", f"{tag}^{{}}"], cwd=upstream, check=False)
        if completed.returncode:
            continue
        commit = completed.stdout.decode().strip()
        best = {"matches": 0, "total": 0, "exact": False}
        for root_commit in roots:
            inputs = inferred_instantiation_inputs(project, root_commit)
            if inputs is None:
                continue
            with tempfile.TemporaryDirectory(prefix="rjc-bootstrap-reconstruct-") as directory:
                generated = reconstructed_candidate(upstream, tag, inputs, Path(directory))
                if generated is None:
                    continue
                matches, total, exact_match = compare_reconstruction(project, root_commit, generated)
                if exact_match or matches > best["matches"]:
                    best = {"matches": matches, "total": total, "exact": exact_match}
        evidence.append({"tag": tag, "commit": commit, **best})
    exact = [item for item in evidence if item["exact"]]
    status = "verified" if len(exact) == 1 else ("partially-verified" if evidence else "unverified")
    chosen = exact[0] if len(exact) == 1 else None
    proposed = {
        "schema": SCHEMA,
        "origin": {
            "status": status,
            "tag": chosen["tag"] if chosen else None,
            "commit": chosen["commit"] if chosen else None,
            "surface_id": surface["surface_id"],
            "surface_sha256": digest(surface),
            "bootstrap_evidence": evidence,
        },
        "components": {},
        "events": [],
    }
    if chosen:
        for item in surface["components"]:
            paths = []
            for path in item["members"]:
                values = [(root, blob_at(project, root, path)) for root in roots]
                matched = next(((root, value) for root, value in values if value == blob_at(upstream, chosen["commit"], path)), None)
                paths.append({
                    "path": path,
                    "sha256": byte_digest(matched[1]) if matched and matched[1] is not None else None,
                })
            proposed["components"][item["id"]] = {
                "base": {"kind": "origin", "result_sha256": digest(paths), "paths": paths}
            }
    return {"project": {**state, "root": str(project)}, "upstream": str(upstream), "proposed_lineage": proposed}


def command_bootstrap_plan(args: argparse.Namespace) -> int:
    payload = bootstrap_payload(args)
    document = {"schema": SCHEMA, "kind": "bootstrap-plan", "payload": payload}
    document["plan_id"] = digest(payload)
    write_json(args.output.resolve(), document)
    print(json.dumps({"plan_id": document["plan_id"], "origin": payload["proposed_lineage"]["origin"]}, indent=2))
    return 0


def verify_plan(plan: dict[str, Any], approve: str) -> dict[str, Any]:
    if plan.get("plan_id") != digest(plan["payload"]) or approve != plan["plan_id"]:
        raise UpdaterError("exact plan approval digest does not match")
    return plan["payload"]


def verify_management_authorization(path: Path | None, plan_id: str, migrations: list[dict[str, Any]]) -> None:
    required = sorted(item["id"] for item in migrations if item["authority_class"] == "adoption-required")
    if not required:
        return
    if path is None:
        raise UpdaterError("adoption-required migrations need human-management authorization")
    authorization = read_json(path.resolve())
    expected_fields = {"schema", "kind", "plan_id", "migration_ids", "management_identity", "decision_reference", "authorized_at"}
    if set(authorization) != expected_fields or authorization["kind"] != "human-management-authorization":
        raise UpdaterError("invalid management authorization")
    if authorization["plan_id"] != plan_id or sorted(authorization["migration_ids"]) != required:
        raise UpdaterError("management authorization does not match the exact plan")
    if not authorization["management_identity"] or not authorization["decision_reference"]:
        raise UpdaterError("management authorization identity and decision reference are required")


def command_bootstrap_apply(args: argparse.Namespace) -> int:
    plan = read_json(args.plan.resolve())
    if plan.get("kind") != "bootstrap-plan":
        raise UpdaterError("not a bootstrap plan")
    payload = verify_plan(plan, args.approve)
    project = args.project.resolve()
    state = clean_state(project)
    expected = payload["project"]
    if any(state[key] != expected[key] for key in ("head", "index_tree", "lineage_blob")):
        raise UpdaterError("approved project inputs changed")
    write_json(project / LINEAGE, payload["proposed_lineage"])
    print("BOOTSTRAP RECORDED; COMMIT REQUIRED")
    return 0


def apply_actions(root: Path, actions: list[dict[str, Any]], which: str) -> None:
    for action in actions:
        content = decoded(action[which])
        path = root / action["path"]
        if content is None:
            if path.exists() or path.is_symlink():
                path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)


def net_actions(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collapse sequential migration actions to one live mutation per path."""
    combined: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for action in actions:
        path = action["path"]
        if path not in combined:
            combined[path] = dict(action)
            order.append(path)
        else:
            combined[path]["after"] = action["after"]
            combined[path]["after_sha256"] = action["after_sha256"]
    return [combined[path] for path in order]


def expand_command(command: list[str], root: Path) -> list[str]:
    python = root / ".venv/bin/python"
    executable = str(python) if python.is_file() else sys.executable
    return [executable if value == "{project_python}" else value for value in command]


def validate(root: Path, commands: list[list[str]]) -> list[dict[str, Any]]:
    results = []
    for command in commands:
        expanded = expand_command(command, root)
        completed = run(expanded, cwd=root, check=False)
        results.append({"argv": expanded, "returncode": completed.returncode, "stdout_sha256": byte_digest(completed.stdout), "stderr_sha256": byte_digest(completed.stderr)})
        if completed.returncode:
            raise UpdaterError(f"validation failed: {' '.join(expanded)}")
    return results


def proposed_lineage(current: dict[str, Any], payload: dict[str, Any], isolated: list[dict[str, Any]], live: list[dict[str, Any]]) -> dict[str, Any]:
    updated = json.loads(json.dumps(current))
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    for migration in payload["migrations"]:
        paths = [{"path": action["path"], "sha256": action["after_sha256"]} for action in payload["actions"] if action["migration_id"] == migration["id"]]
        event_payload = {
            "kind": "migration-adopted",
            "migration_id": migration["id"],
            "component": migration["component"],
            "upstream_target": migration["target_commit"],
            "descriptor_sha256": migration["descriptor_sha256"],
            "resolution": (
                "local-equivalent" if "local-equivalent" in migration["classifications"] else
                "upstream-exact" if set(migration["classifications"]) <= {"cleanly-applicable", "already-identical", "resolved-upstream"} else
                "merged"
            ),
            "paths": paths,
            "plan_id": digest(payload),
            "validation": {"isolated": digest(isolated), "live": digest(live)},
            "recorded_at": now,
        }
        if migration.get("local_equivalence_attestation"):
            event_payload["attestation"] = migration["local_equivalence_attestation"]
        event = {**event_payload, "event_id": digest(event_payload)}
        updated.setdefault("events", []).append(event)
        updated.setdefault("components", {})[migration["component"]] = {"base_event": event["event_id"], "result_sha256": digest(paths)}
    return updated


def command_apply(args: argparse.Namespace) -> int:
    plan = read_json(args.plan.resolve())
    if plan.get("kind") != "migration-plan":
        raise UpdaterError("not a migration plan")
    payload = verify_plan(plan, args.approve)
    if payload["blocked"]:
        raise UpdaterError("blocked plans cannot be applied")
    if not payload["actions"]:
        raise UpdaterError("plan contains no applicable migration actions")
    project = args.project.resolve()
    upstream = args.upstream.resolve()
    verify_management_authorization(args.management_authorization, plan["plan_id"], payload["migrations"])
    state = clean_state(project)
    expected = payload["project"]
    if any(state[key] != expected[key] for key in ("head", "index_tree", "lineage_blob")):
        raise UpdaterError("approved project inputs changed")
    if git_text(upstream, "rev-parse", f"{payload['upstream']['target_tag']}^{{}}") != payload["upstream"]["target_commit"]:
        raise UpdaterError("approved upstream target changed")
    surface = load_surface(upstream)
    if digest(surface) != payload["upstream"]["surface_sha256"]:
        raise UpdaterError("approved surface manifest changed")
    for recorded in payload["migrations"]:
        actual = load_migration(upstream, recorded["id"], surface)
        if digest(actual) != recorded["descriptor_sha256"]:
            raise UpdaterError(f"approved migration descriptor changed: {recorded['id']}")
        if actual["authority_class"] != recorded["authority_class"] or actual["component"] != recorded["component"] or actual["upstream"]["target_commit"] != recorded["target_commit"]:
            raise UpdaterError(f"approved migration semantics changed: {recorded['id']}")
    current = lineage(project)
    mutations = net_actions(payload["actions"])
    with tempfile.TemporaryDirectory(prefix="rjc-updater-worktree-") as directory:
        isolated_root = Path(directory) / "project"
        git(project, "worktree", "add", "--detach", str(isolated_root), state["head"])
        try:
            apply_actions(isolated_root, mutations, "after")
            expected_isolated_status = status_bytes(isolated_root)
            isolated_results = validate(isolated_root, payload["validation"])
            if status_bytes(isolated_root) != expected_isolated_status:
                raise UpdaterError("isolated validation changed unplanned files")
        finally:
            git(project, "worktree", "remove", "--force", str(isolated_root), check=False)
    apply_actions(project, mutations, "after")
    expected_live_status = status_bytes(project)
    try:
        live_results = validate(project, payload["validation"])
        if status_bytes(project) != expected_live_status:
            raise UpdaterError("live validation changed unplanned files")
    except UpdaterError:
        safe = status_bytes(project) == expected_live_status and all((byte_digest(worktree_blob(project, action["path"])) if worktree_blob(project, action["path"]) is not None else None) == action["after_sha256"] for action in mutations)
        if safe:
            apply_actions(project, mutations, "before")
            print("LIVE VALIDATION FAILED; EXACT UPDATER MUTATION REVERSED", file=sys.stderr)
        else:
            print("LIVE VALIDATION FAILED; SAFE REVERSAL NOT ESTABLISHED", file=sys.stderr)
        raise
    updated = proposed_lineage(current, payload, isolated_results, live_results)
    write_json(project / LINEAGE, updated)
    print("APPLICATION VALIDATED; COMMIT REQUIRED")
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    commands = result.add_subparsers(dest="command", required=True)
    bootstrap_plan = commands.add_parser("bootstrap-plan")
    bootstrap_plan.add_argument("--project", type=Path, required=True)
    bootstrap_plan.add_argument("--upstream", type=Path, required=True)
    bootstrap_plan.add_argument("--candidate", action="append")
    bootstrap_plan.add_argument("--output", type=Path, required=True)
    bootstrap_plan.set_defaults(handler=command_bootstrap_plan)
    bootstrap_apply = commands.add_parser("bootstrap-apply")
    bootstrap_apply.add_argument("--project", type=Path, required=True)
    bootstrap_apply.add_argument("--plan", type=Path, required=True)
    bootstrap_apply.add_argument("--approve", required=True)
    bootstrap_apply.set_defaults(handler=command_bootstrap_apply)
    plan = commands.add_parser("plan")
    plan.add_argument("--project", type=Path, required=True)
    plan.add_argument("--upstream", type=Path, required=True)
    plan.add_argument("--target", required=True)
    plan.add_argument("--migration", action="append", required=True)
    plan.add_argument("--resolve-upstream", action="append")
    plan.add_argument("--local-equivalent", action="append")
    plan.add_argument("--output", type=Path, required=True)
    plan.set_defaults(handler=command_plan)
    apply = commands.add_parser("apply")
    apply.add_argument("--project", type=Path, required=True)
    apply.add_argument("--upstream", type=Path, required=True)
    apply.add_argument("--plan", type=Path, required=True)
    apply.add_argument("--approve", required=True)
    apply.add_argument("--management-authorization", type=Path)
    apply.set_defaults(handler=command_apply)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        return args.handler(args)
    except UpdaterError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
