"""Static contracts for CI and security workflow triggers/permissions."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent.parent


class WorkflowSecurityTest(unittest.TestCase):
    def test_ci_push_is_not_limited_to_the_old_main_branch(self):
        text = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertRegex(text, r"(?m)^on:\n  push:\n  pull_request:")
        self.assertNotRegex(text, r"(?m)^\s+branches:\s*\[main\]")

    def test_addon_build_runs_for_pushes_to_any_branch(self):
        text = (ROOT / ".github/workflows/addons.yml").read_text(encoding="utf-8")
        self.assertRegex(text, r"(?m)^  push:\n    paths: \[\"addons/\*\*\"\]")
        self.assertNotRegex(text, r"(?m)^\s+branches:\s*\[main\]")

    def test_codeql_scans_python_actions_and_android(self):
        text = (ROOT / ".github/workflows/codeql.yml").read_text(encoding="utf-8")
        for required in (
            "  push:",
            "  pull_request:",
            "language: [actions, python]",
            "languages: java-kotlin",
            "security-events: write",
            "workflow_dispatch:",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)
        self.assertNotIn("pull_request_target:", text)

    def test_codeql_actions_are_pinned_to_full_commit_shas(self):
        text = (ROOT / ".github/workflows/codeql.yml").read_text(encoding="utf-8")
        refs = re.findall(r"uses:\s*[^\s]+@([^\s#]+)", text)
        self.assertGreaterEqual(len(refs), 5)
        for ref in refs:
            with self.subTest(ref=ref):
                self.assertRegex(ref, r"^[0-9a-f]{40}$")

    def test_tables_job_only_runs_on_the_default_branch_push(self):
        text = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertIn("github.ref_name == github.event.repository.default_branch", text)


if __name__ == "__main__":
    unittest.main()
