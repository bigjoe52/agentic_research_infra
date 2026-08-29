import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest


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
            subprocess.run(["git", "init", "--quiet", str(root)], check=True)
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


if __name__ == "__main__":
    unittest.main()
