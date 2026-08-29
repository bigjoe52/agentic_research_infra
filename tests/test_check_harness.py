import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_harness", ROOT / "scripts" / "check_harness.py"
)
assert SPEC and SPEC.loader
CHECK_HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK_HARNESS)
FORBIDDEN_MARKER = "options" + "_flow"


class ContentScanSelectionTests(unittest.TestCase):
    def write(self, root: Path, relative: str, body: str) -> Path:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        return path

    def initialize(self, root: Path) -> None:
        subprocess.run(["git", "init", "--quiet", str(root)], check=True)

    def candidates_with_global_excludes(
        self, root: Path, excludes_file: Path
    ) -> list[Path]:
        configuration = {
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "core.excludesFile",
            "GIT_CONFIG_VALUE_0": str(excludes_file),
        }
        with mock.patch.dict(os.environ, configuration, clear=False):
            return CHECK_HARNESS.repository_files(root)

    def test_ignored_local_artifacts_are_not_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(
                root,
                ".gitignore",
                ".env\ncredentials.json\n.venv/\n__pycache__/\ndata/generated/\n",
            )
            self.write(root, ".env", f"synthetic_secret={FORBIDDEN_MARKER}\n")
            self.write(root, "credentials.json", f'"synthetic": "{FORBIDDEN_MARKER}"\n')
            self.write(root, ".venv/provider.txt", f"{FORBIDDEN_MARKER}\n")
            self.write(root, "__pycache__/provider.txt", f"{FORBIDDEN_MARKER}\n")
            self.write(root, "data/generated/provider.txt", f"{FORBIDDEN_MARKER}\n")
            legitimate = self.write(root, "src/example.py", "VALUE = 'neutral'\n")

            candidates = CHECK_HARNESS.repository_files(root)

            self.assertEqual(candidates, [root / ".gitignore", legitimate])
            self.assertEqual(CHECK_HARNESS.forbidden_case_law(candidates, root), [])

    def test_forbidden_text_in_tracked_file_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root, ".gitignore", ".env\n")
            source = self.write(root, "src/example.py", f"DEPENDENCY = '{FORBIDDEN_MARKER}'\n")
            self.initialize(root)
            subprocess.run(
                ["git", "-C", str(root), "add", ".gitignore", "src/example.py"],
                check=True,
            )

            candidates = CHECK_HARNESS.repository_files(root)

            self.assertIn(source, candidates)
            self.assertEqual(
                CHECK_HARNESS.forbidden_case_law(candidates, root),
                [("src/example.py", FORBIDDEN_MARKER)],
            )

    def test_project_owned_selection_in_initialized_repository(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root, ".gitignore", "ignored.txt\ntracked-ignored.txt\n")
            ignored = self.write(root, "ignored.txt", "ignored by project\n")
            tracked_ignored = self.write(
                root, "tracked-ignored.txt", "tracked project content\n"
            )
            untracked = self.write(
                root, "src/new.py", f"DEPENDENCY = '{FORBIDDEN_MARKER}'\n"
            )
            global_only = self.write(root, "global-only.txt", "project content\n")
            info_only = self.write(root, "info-only.txt", "project content\n")
            symlink = root / "source-link.py"
            symlink.symlink_to(untracked)
            global_excludes = self.write(
                root, "machine-global-ignore", "global-only.txt\n"
            )
            neutral_excludes = self.write(root, "neutral-global-ignore", "")
            self.initialize(root)
            subprocess.run(
                ["git", "-C", str(root), "add", ".gitignore"], check=True
            )
            subprocess.run(
                ["git", "-C", str(root), "add", "-f", "tracked-ignored.txt"],
                check=True,
            )

            baseline = self.candidates_with_global_excludes(root, neutral_excludes)
            self.write(root, ".git/info/exclude", "info-only.txt\n")
            influenced = self.candidates_with_global_excludes(root, global_excludes)

            self.assertEqual(baseline, influenced)
            self.assertNotIn(ignored, influenced)
            self.assertIn(tracked_ignored, influenced)
            self.assertIn(untracked, influenced)
            self.assertIn(global_only, influenced)
            self.assertIn(info_only, influenced)
            self.assertNotIn(symlink, influenced)
            self.assertIn(
                ("src/new.py", FORBIDDEN_MARKER),
                CHECK_HARNESS.forbidden_case_law(influenced, root),
            )

    def test_project_owned_selection_before_git_init(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root, ".gitignore", "ignored.txt\n")
            ignored = self.write(root, "ignored.txt", "ignored by project\n")
            untracked = self.write(
                root, "src/new.py", f"DEPENDENCY = '{FORBIDDEN_MARKER}'\n"
            )
            global_only = self.write(root, "global-only.txt", "project content\n")
            info_only = self.write(root, "info-only.txt", "project content\n")
            symlink = root / "source-link.py"
            symlink.symlink_to(untracked)
            global_excludes = self.write(
                root, "machine-global-ignore", "global-only.txt\n"
            )
            neutral_excludes = self.write(root, "neutral-global-ignore", "")

            baseline = self.candidates_with_global_excludes(root, neutral_excludes)
            self.write(root, ".git/info/exclude", "info-only.txt\n")
            influenced = self.candidates_with_global_excludes(root, global_excludes)

            self.assertEqual(baseline, influenced)
            self.assertNotIn(ignored, influenced)
            self.assertIn(untracked, influenced)
            self.assertIn(global_only, influenced)
            self.assertIn(info_only, influenced)
            self.assertNotIn(symlink, influenced)
            self.assertIn(
                ("src/new.py", FORBIDDEN_MARKER),
                CHECK_HARNESS.forbidden_case_law(influenced, root),
            )


if __name__ == "__main__":
    unittest.main()
