import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tarfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "harness_update.py"
SPEC = importlib.util.spec_from_file_location("harness_update", SCRIPT)
assert SPEC and SPEC.loader
UPDATER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(UPDATER)
M1 = "governance-scan/2026-001-git-file-selection"
M2 = "governance-scan/2026-002-project-owned-exclusions"


def run(args, cwd, check=True):
    completed = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if check and completed.returncode:
        raise AssertionError(f"command failed: {args}\n{completed.stdout}\n{completed.stderr}")
    return completed


def git(root, *args):
    return run(["git", *args], root).stdout.strip()


def commit_all(root, message):
    git(root, "add", "-A")
    git(root, "commit", "-m", message)


class UpdaterTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="rjc-updater-test-")
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def cli(self, *args, check=True):
        return run([sys.executable, str(SCRIPT), *map(str, args)], ROOT, check=check)

    def historical_project(self):
        source = self.root / "source-v100"
        project = self.root / "descendant"
        archive = subprocess.run(
            ["git", "archive", "--format=tar", "v1.0.0"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        ).stdout
        source.mkdir()
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as bundle:
            bundle.extractall(source)
        run(
            [
                sys.executable,
                "scripts/instantiate.py",
                str(project),
                "--project-name",
                "synthetic_descendant",
                "--title",
                "Synthetic Descendant",
                "--summary",
                "Disposable updater fixture.",
            ],
            source,
        )
        git(project, "init", "--quiet")
        git(project, "config", "user.email", "fixture@example.invalid")
        git(project, "config", "user.name", "Updater Fixture")
        commit_all(project, "Instantiate from v1.0.0")
        return project

    def bootstrap(self, project):
        plan = self.root / "bootstrap.json"
        self.cli(
            "bootstrap-plan", "--project", project, "--upstream", ROOT,
            "--candidate", "v1.0.0", "--output", plan,
        )
        document = json.loads(plan.read_text())
        self.assertEqual(document["payload"]["proposed_lineage"]["origin"]["status"], "verified")
        self.cli(
            "bootstrap-apply", "--project", project, "--plan", plan,
            "--approve", document["plan_id"],
        )
        commit_all(project, "Record verified harness origin")
        return document

    def migration_plan(self, project, output, resolve=False):
        args = [
            "plan", "--project", project, "--upstream", ROOT, "--target", "v1.0.2",
            "--migration", M1, "--migration", M2, "--output", output,
        ]
        if resolve:
            args.extend(["--resolve-upstream", M1, "--resolve-upstream", M2])
        return self.cli(*args, check=False)

    def install_incomplete_port(self, project):
        script = project / "scripts/check_harness.py"
        body = script.read_text()
        body = body.replace("import re\n", "import re\nimport subprocess\n")
        marker = "\ndef main() -> int:\n"
        partial = '''
def repository_files(root: Path = ROOT) -> list[Path]:
    # Specification-derived port: assumes Git metadata and follows symlinks.
    completed = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        check=True, capture_output=True,
    )
    return [root / path for path in completed.stdout.decode().split("\\0") if path]

'''
        body = body.replace(marker, "\n" + partial + "def main() -> int:\n")
        old = '''    tracked_text = []
    for path in ROOT.rglob("*"):
        if path.is_file() and ".git" not in path.parts and ".venv" not in path.parts:
            try:
                tracked_text.append((path, path.read_text(encoding="utf-8").lower()))
            except UnicodeDecodeError:
                pass
    leaks = [(str(path.relative_to(ROOT)), term) for path, body in tracked_text
             for term in FORBIDDEN_CASE_LAW if term in body]
'''
        new = '''    tracked_text = []
    for path in repository_files():
        try:
            tracked_text.append((path, path.read_text(encoding="utf-8").lower()))
        except UnicodeDecodeError:
            pass
    leaks = [(str(path.relative_to(ROOT)), term) for path, body in tracked_text
             for term in FORBIDDEN_CASE_LAW if term in body]
'''
        self.assertIn(old, body)
        script.write_text(body.replace(old, new))
        beginning = project / "docs/THE_BEGINNING.md"
        beginning.write_text(beginning.read_text() + "\nSynthetic independent scientific state.\n")
        commit_all(project, "Add incomplete specification-derived scanner port")

    def test_canonical_json_is_stable(self):
        self.assertEqual(UPDATER.canonical({"b": 1, "a": 2}), b'{"a":2,"b":1}')
        self.assertEqual(UPDATER.digest({"a": 2, "b": 1}), UPDATER.digest({"b": 1, "a": 2}))

    def test_native_instantiation_has_lineage_and_excludes_maintainer_files(self):
        project = self.root / "native"
        run(
            [
                sys.executable, "scripts/instantiate.py", str(project),
                "--project-name", "native_fixture", "--title", "Native Fixture",
                "--summary", "Disposable native-lineage fixture.",
            ],
            ROOT,
        )
        lineage = json.loads((project / ".rjc-harness/lineage.json").read_text())
        self.assertIn(lineage["origin"]["status"], {"verified", "unverified"})
        self.assertIn("governance-scan", lineage["components"])
        self.assertFalse((project / "HARNESS_DECISIONS.md").exists())
        self.assertFalse((project / "HARNESS_EVIDENCE.md").exists())
        self.assertFalse((project / "scripts/harness_update.py").exists())
        self.assertFalse((project / "harness").exists())

    def test_historical_scanner_acceptance(self):
        project = self.historical_project()
        self.bootstrap(project)
        self.install_incomplete_port(project)
        institutional = (project / "docs/THE_BEGINNING.md").read_bytes()

        blocked_plan = self.root / "blocked.json"
        blocked = self.migration_plan(project, blocked_plan)
        self.assertEqual(blocked.returncode, 2, blocked.stderr)
        blocked_doc = json.loads(blocked_plan.read_text())
        self.assertTrue(blocked_doc["payload"]["blocked"])
        self.assertIn("conflict", {a["classification"] for a in blocked_doc["payload"]["actions"]})

        plan = self.root / "approved.json"
        planned = self.migration_plan(project, plan, resolve=True)
        self.assertEqual(planned.returncode, 0, planned.stderr)
        document = json.loads(plan.read_text())
        head_before_apply = git(project, "rev-parse", "HEAD")
        applied = self.cli(
            "apply", "--project", project, "--upstream", ROOT,
            "--plan", plan, "--approve", document["plan_id"],
        )
        self.assertIn("COMMIT REQUIRED", applied.stdout)
        scanner = (project / "scripts/check_harness.py").read_text()
        self.assertIn("TemporaryDirectory", scanner)
        self.assertIn("is_symlink", scanner)
        self.assertIn("--exclude-per-directory=.gitignore", scanner)
        self.assertEqual((project / "docs/THE_BEGINNING.md").read_bytes(), institutional)
        lineage = json.loads((project / ".rjc-harness/lineage.json").read_text())
        self.assertEqual([event["migration_id"] for event in lineage["events"]], [M1, M2])
        self.assertEqual(git(project, "rev-parse", "HEAD"), head_before_apply)
        self.assertNotEqual(git(project, "status", "--porcelain=v1"), "")

    def test_local_equivalence_requires_explicit_attestation(self):
        project = self.historical_project()
        self.bootstrap(project)
        self.install_incomplete_port(project)
        blocked_plan = self.root / "equivalence-blocked.json"
        self.assertEqual(self.migration_plan(project, blocked_plan).returncode, 2)
        attestation = self.root / "attestation.json"
        attestation.write_text(json.dumps({
            "schema": 1,
            "reviewer": "Synthetic human reviewer",
            "basis": "Explicit disposable-fixture review; tests alone are insufficient."
        }))
        plan = self.root / "equivalence.json"
        result = self.cli(
            "plan", "--project", project, "--upstream", ROOT, "--target", "v1.0.1",
            "--migration", M1, "--local-equivalent", f"{M1}={attestation}",
            "--output", plan, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        document = json.loads(plan.read_text())
        self.assertIn("local-equivalent", document["payload"]["migrations"][0]["classifications"])

    def test_plan_invalidates_after_project_change(self):
        project = self.historical_project()
        self.bootstrap(project)
        plan = self.root / "plan.json"
        self.assertEqual(self.migration_plan(project, plan, resolve=True).returncode, 0)
        document = json.loads(plan.read_text())
        (project / "local-change.txt").write_text("changed\n")
        applied = self.cli(
            "apply", "--project", project, "--upstream", ROOT,
            "--plan", plan, "--approve", document["plan_id"], check=False,
        )
        self.assertNotEqual(applied.returncode, 0)
        self.assertIn("must be clean", applied.stderr)

    def test_legacy_bootstrap_preserves_partial_and_unverified_states(self):
        partial = self.historical_project()
        scanner = partial / "scripts/check_harness.py"
        scanner.write_text(scanner.read_text() + "\n# pre-lineage local variation\n")
        git(partial, "add", "scripts/check_harness.py")
        git(partial, "commit", "--amend", "-m", "Legacy snapshot with uncertain origin")
        partial_plan = self.root / "partial.json"
        self.cli(
            "bootstrap-plan", "--project", partial, "--upstream", ROOT,
            "--candidate", "v1.0.0", "--output", partial_plan,
        )
        partial_doc = json.loads(partial_plan.read_text())
        self.assertEqual(partial_doc["payload"]["proposed_lineage"]["origin"]["status"], "partially-verified")

        unknown = self.root / "unknown"
        unknown.mkdir()
        git(unknown, "init", "--quiet")
        git(unknown, "config", "user.email", "fixture@example.invalid")
        git(unknown, "config", "user.name", "Updater Fixture")
        (unknown / "README.md").write_text("independent legacy repository\n")
        commit_all(unknown, "Unknown legacy origin")
        unknown_plan = self.root / "unknown.json"
        self.cli(
            "bootstrap-plan", "--project", unknown, "--upstream", ROOT,
            "--candidate", "missing-tag", "--output", unknown_plan,
        )
        unknown_doc = json.loads(unknown_plan.read_text())
        self.assertEqual(unknown_doc["payload"]["proposed_lineage"]["origin"]["status"], "unverified")

    def test_isolated_failure_leaves_live_tree_untouched(self):
        project = self.historical_project()
        self.bootstrap(project)
        before = git(project, "status", "--porcelain=v1")
        plan_path = self.root / "isolated-fail.json"
        self.assertEqual(self.migration_plan(project, plan_path, resolve=True).returncode, 0)
        plan = json.loads(plan_path.read_text())
        plan["payload"]["validation"] = [[sys.executable, "-c", "raise SystemExit(7)"]]
        plan["plan_id"] = UPDATER.digest(plan["payload"])
        plan_path.write_text(json.dumps(plan))
        result = self.cli(
            "apply", "--project", project, "--upstream", ROOT,
            "--plan", plan_path, "--approve", plan["plan_id"], check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(git(project, "status", "--porcelain=v1"), before)

    def test_live_failure_reverses_exact_mutation(self):
        project = self.historical_project()
        self.bootstrap(project)
        original = (project / "scripts/check_harness.py").read_bytes()
        plan_path = self.root / "live-fail.json"
        self.assertEqual(self.migration_plan(project, plan_path, resolve=True).returncode, 0)
        plan = json.loads(plan_path.read_text())
        code = "import os,sys; sys.exit(0 if 'rjc-updater-worktree-' in os.getcwd() else 9)"
        plan["payload"]["validation"] = [[sys.executable, "-c", code]]
        plan["plan_id"] = UPDATER.digest(plan["payload"])
        plan_path.write_text(json.dumps(plan))
        result = self.cli(
            "apply", "--project", project, "--upstream", ROOT,
            "--plan", plan_path, "--approve", plan["plan_id"], check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("REVERSED", result.stderr)
        self.assertEqual((project / "scripts/check_harness.py").read_bytes(), original)
        self.assertEqual(git(project, "status", "--porcelain=v1"), "")

    def test_live_failure_does_not_reverse_after_unrelated_mutation(self):
        project = self.historical_project()
        self.bootstrap(project)
        plan_path = self.root / "unsafe-live-fail.json"
        self.assertEqual(self.migration_plan(project, plan_path, resolve=True).returncode, 0)
        plan = json.loads(plan_path.read_text())
        code = (
            "import os,pathlib,sys; "
            "isolated='rjc-updater-worktree-' in os.getcwd(); "
            "pathlib.Path('intervening.txt').write_text('unexpected\\n') if not isolated else None; "
            "sys.exit(0 if isolated else 9)"
        )
        plan["payload"]["validation"] = [[sys.executable, "-c", code]]
        plan["plan_id"] = UPDATER.digest(plan["payload"])
        plan_path.write_text(json.dumps(plan))
        result = self.cli(
            "apply", "--project", project, "--upstream", ROOT,
            "--plan", plan_path, "--approve", plan["plan_id"], check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SAFE REVERSAL NOT ESTABLISHED", result.stderr)
        self.assertTrue((project / "intervening.txt").exists())
        self.assertIn("M scripts/check_harness.py", git(project, "status", "--short"))

    def test_surface_rejects_project_owned_and_template_only_paths(self):
        surface = UPDATER.load_surface(ROOT)
        item = UPDATER.component(surface, "governance-scan")
        with self.assertRaises(UPDATER.UpdaterError):
            UPDATER.ensure_component_path(item, "docs/DECISIONS.md")
        with self.assertRaises(UPDATER.UpdaterError):
            UPDATER.ensure_component_path(item, "scripts/instantiate.py")

    def test_adoption_required_plan_is_blocked_without_authorization(self):
        project = self.historical_project()
        self.bootstrap(project)
        plan = self.root / "plan.json"
        self.assertEqual(self.migration_plan(project, plan, resolve=True).returncode, 0)
        document = json.loads(plan.read_text())
        document["payload"]["migrations"][0]["authority_class"] = "adoption-required"
        document["payload"]["blocked"] = False
        document["plan_id"] = UPDATER.digest(document["payload"])
        plan.write_text(json.dumps(document))
        result = self.cli(
            "apply", "--project", project, "--upstream", ROOT,
            "--plan", plan, "--approve", document["plan_id"], check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("human-management authorization", result.stderr)


if __name__ == "__main__":
    unittest.main()
