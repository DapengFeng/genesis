from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from guidance_system import audit_file, resolve_guidance  # noqa: E402

AI_CLI = REPO_ROOT / "ai"


class GuidanceSystemTests(unittest.TestCase):
    def run_ai(
        self, *args: str, working_directory: Path
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(AI_CLI), *args],
            cwd=working_directory,
            check=False,
            text=True,
            capture_output=True,
        )

    def test_init_scaffolds_requested_templates(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            result = self.run_ai(
                "init",
                "--template",
                "python,cpp",
                working_directory=root,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((root / ".agent" / "guidance.yaml").exists())
            self.assertTrue(
                (root / ".agent" / "guidance" / "python.yaml").exists()
            )
            self.assertTrue(
                (root / ".agent" / "guidance" / "cpp.yaml").exists()
            )

    def test_resolve_uses_language_specific_identifier_style(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self.run_ai(
                "init",
                "--template",
                "python,cpp",
                working_directory=root,
            )
            python_file = root / "python" / "module.py"
            cpp_file = root / "cpp" / "widget.cpp"
            python_file.parent.mkdir(parents=True)
            cpp_file.parent.mkdir(parents=True)
            python_file.write_text(
                "def snake_case_name() -> None:\n    pass\n", encoding="utf-8"
            )
            cpp_file.write_text("class CamelCaseName {};\n", encoding="utf-8")

            python_resolution = resolve_guidance(root, python_file)
            cpp_resolution = resolve_guidance(root, cpp_file)

            self.assertIn("snake_case", json.dumps(python_resolution))
            self.assertIn("CamelCase", json.dumps(cpp_resolution))

    def test_inline_guidance_overrides_cpp_exceptions(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self.run_ai("init", "--template", "cpp", working_directory=root)
            cpp_file = root / "cpp" / "widget.cpp"
            cpp_file.parent.mkdir(parents=True)
            cpp_file.write_text(
                'throw std::runtime_error("boom");\n', encoding="utf-8"
            )

            resolution = resolve_guidance(
                root,
                cpp_file,
                inline_guidance="[guidance: No exceptions this time]",
            )
            self.assertIn("inline-no-exceptions", json.dumps(resolution))

            audit = audit_file(
                root,
                cpp_file,
                inline_guidance="[guidance: No exceptions this time]",
            )
            self.assertIn(
                "exception handling disabled", json.dumps(audit["findings"])
            )

    def test_rust_audit_reports_missing_debug(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self.run_ai("init", "--template", "rust", working_directory=root)
            rust_file = root / "rust" / "lib.rs"
            rust_file.parent.mkdir(parents=True)
            rust_file.write_text("pub struct Widget;\n", encoding="utf-8")

            audit = audit_file(root, rust_file)
            self.assertIn(
                "Deviation: public type missing Debug impl",
                json.dumps(audit["findings"]),
            )

    def test_audit_reports_raw_new_without_modifying_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self.run_ai("init", "--template", "cpp", working_directory=root)
            cpp_file = root / "cpp" / "widget.cpp"
            cpp_file.parent.mkdir(parents=True)
            original = "auto *value = new Widget();\n"
            cpp_file.write_text(original, encoding="utf-8")

            result = self.run_ai("audit", "cpp", working_directory=root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("use of raw new", result.stdout)
            self.assertEqual(cpp_file.read_text(encoding="utf-8"), original)

    def test_invalid_yaml_warns_and_valid_rules_continue_loading(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self.run_ai(
                "init",
                "--template",
                "python,cpp",
                working_directory=root,
            )
            broken = root / ".agent" / "guidance" / "broken.yaml"
            broken.write_text("version: 1\nrules: [\n", encoding="utf-8")
            python_file = root / "python" / "module.py"
            python_file.parent.mkdir(parents=True)
            python_file.write_text(
                "def snake_case_name() -> None:\n    pass\n", encoding="utf-8"
            )

            result = self.run_ai(
                "resolve",
                "python/module.py",
                working_directory=root,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("python-snake-case", result.stdout)
            self.assertIn(
                "Warning: skipped invalid guidance file", result.stdout
            )


if __name__ == "__main__":
    unittest.main()
