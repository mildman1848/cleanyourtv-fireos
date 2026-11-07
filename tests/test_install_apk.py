"""tools/install_apk.py: local preflight, quoted unique staging, cleanup only after Success, no extra grants."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import install_apk  # noqa: E402


def make_apk(directory, name="app.apk", entries=("AndroidManifest.xml", "classes.dex")):
    path = Path(directory) / name
    with zipfile.ZipFile(path, "w") as z:
        for entry in entries:
            z.writestr(entry, b"x")
    return str(path)


class Recorder:
    """A fake process runner: records every argv, answers push/install/rm from `answers`."""

    def __init__(self, install_out="Success", push_code=0):
        self.calls, self.install_out, self.push_code = [], install_out, push_code

    def __call__(self, argv, env):
        self.calls.append(argv)
        script = os.path.basename(argv[2])
        if script == "b64push.py":
            return subprocess.CompletedProcess(argv, self.push_code, "", "no route" if self.push_code else "")
        if argv[3].startswith("pm install"):
            return subprocess.CompletedProcess(argv, 0, self.install_out, "")
        return subprocess.CompletedProcess(argv, 0, "", "")

    def tv_commands(self):
        return [c[3] for c in self.calls if os.path.basename(c[2]) == "tv.py"]


class InstallApkTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.env = {"TV_HOST": "192.168.1.50"}

    def test_validate_refuses_missing_empty_corrupt_and_non_apk(self):
        d = Path(self.tmp.name)
        (d / "empty.apk").write_bytes(b"")
        (d / "junk.apk").write_bytes(b"not a zip")
        for path in (str(d / "nope.apk"), str(d / "empty.apk"), str(d / "junk.apk"),
                     make_apk(d, "nomanifest.apk", ("classes.dex",)), make_apk(d, "nodex.apk", ("AndroidManifest.xml",))):
            with self.assertRaises(install_apk.InstallError, msg=path) as caught:
                install_apk.validate_apk(path)
            self.assertEqual(2, caught.exception.exit_code)
        install_apk.validate_apk(make_apk(d))

    def test_remote_path_is_unique_and_shell_safe(self):
        a, b = install_apk.remote_path("/x/My App; rm -rf.apk"), install_apk.remote_path("/x/My App; rm -rf.apk")
        self.assertNotEqual(a, b)
        for p in (a, b):
            self.assertRegex(p, r"^/data/local/tmp/cytv-[0-9a-f]{12}-[A-Za-z0-9._-]+\.apk$")

    def test_quote_survives_a_single_quote(self):
        self.assertEqual("'a'\\''b'", install_apk.quote("a'b"))

    def test_success_installs_then_removes_the_staging_file(self):
        run = Recorder()
        remote = install_apk.install(make_apk(self.tmp.name), run=run, env=self.env)
        cmds = run.tv_commands()
        self.assertEqual([f"pm install -r '{remote}'", f"rm -f '{remote}'"], cmds)
        self.assertEqual(remote, run.calls[0][-1])

    def test_failed_install_keeps_the_staging_file_and_says_where(self):
        run = Recorder(install_out="Failure [INSTALL_FAILED_VERIFICATION_FAILURE]")
        with self.assertRaises(install_apk.InstallError) as caught:
            install_apk.install(make_apk(self.tmp.name), run=run, env=self.env)
        self.assertEqual(1, caught.exception.exit_code)
        self.assertIn("INSTALL_FAILED_VERIFICATION_FAILURE", str(caught.exception))
        self.assertIn("/data/local/tmp/cytv-", str(caught.exception))
        self.assertFalse([c for c in run.tv_commands() if c.startswith("rm ")])

    def test_failed_push_never_runs_pm(self):
        run = Recorder(push_code=2)
        with self.assertRaises(install_apk.InstallError) as caught:
            install_apk.install(make_apk(self.tmp.name), run=run, env=self.env)
        self.assertEqual(2, caught.exception.exit_code)
        self.assertEqual([], run.tv_commands())

    def test_no_tv_host_is_refused_before_any_call(self):
        run = Recorder()
        with self.assertRaises(install_apk.InstallError):
            install_apk.install(make_apk(self.tmp.name), run=run, env={})
        self.assertEqual([], run.calls)

    def test_grants_are_an_allowlist_and_need_a_package(self):
        apk = make_apk(self.tmp.name)
        for grants, package in ((["android.permission.WRITE_SECURE_SETTINGS"], "com.example.app"),
                                (["android.permission.BIND_ACCESSIBILITY_SERVICE"], "com.example.app"),
                                (["android.permission.ACCESS_FINE_LOCATION"], None),
                                (["android.permission.ACCESS_FINE_LOCATION"], "com.example.app; reboot")):
            run = Recorder()
            with self.assertRaises(install_apk.InstallError):
                install_apk.install(apk, package, grants, run=run, env=self.env)
            self.assertEqual([], run.calls, "the TV must not be touched on a refused grant")

    def test_the_one_allowed_grant_runs_after_the_install(self):
        run = Recorder()
        remote = install_apk.install(make_apk(self.tmp.name), "com.example.app",
                                     ["android.permission.ACCESS_FINE_LOCATION"], run=run, env=self.env)
        self.assertEqual([f"pm install -r '{remote}'",
                          "pm grant 'com.example.app' 'android.permission.ACCESS_FINE_LOCATION'",
                          f"rm -f '{remote}'"], run.tv_commands())

    def test_install_never_touches_home_or_accessibility(self):
        run = Recorder()
        install_apk.install(make_apk(self.tmp.name), run=run, env=self.env)
        joined = " ".join(run.tv_commands())
        for word in ("settings", "accessibility", "set-home-activity", "disable", "WRITE_SECURE"):
            self.assertNotIn(word, joined)

    def test_cli_exit_codes(self):
        self.assertEqual(2, install_apk.main([str(Path(self.tmp.name) / "missing.apk")]))


if __name__ == "__main__":
    unittest.main()
