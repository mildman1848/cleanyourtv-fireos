#!/usr/bin/env python3
"""Install a local APK on the TV as an ordinary app: a safe helper shared by the launcher and add-ons.

Usage: install_apk.py <apk> [--package <name>] [--grant <permission>] [--keep-remote]

What it does, in order:
  1. checks the local file (a readable zip with AndroidManifest.xml and a dex file, under 150 MB);
  2. pushes it with tools/b64push.py to a unique /data/local/tmp/cytv-<random>-<name>.apk, so two
     installs never share a staging file;
  3. runs `pm install -r '<staging path>'` through tools/tv.py and requires pm's "Success";
  4. only then removes the staging file. After a failure the file stays on the TV and its path is in
     the message, so the cause can be looked at (`pm install` prints it) and nothing is lost.

What it never does: change Home, the accessibility list or secure settings, enable a service, or
disable anything. The one permission it can grant is on the allowlist GRANTABLE below, and only when
asked for with --grant (and --package). Anything else, WRITE_SECURE_SETTINGS and the accessibility
permissions included, is refused before the TV is touched.

Exit status: 0 installed, 1 the TV refused or the transfer failed, 2 nothing was sent (arguments
or local file refused, or the TV could not be reached).
"""
import argparse
import os
import re
import subprocess
import sys
import uuid
import zipfile

TOOLS = os.path.dirname(os.path.abspath(__file__))
MAX_APK = 150 * 1024 * 1024
# Only what the launcher's network pill needs (build-and-install.sh grants it the same way).
GRANTABLE = {"android.permission.ACCESS_FINE_LOCATION"}
PACKAGE_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z][A-Za-z0-9_]*)+")
NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


class InstallError(Exception):
    """exit_code 2: nothing was sent to the TV; 1: the TV or the transfer failed."""

    def __init__(self, message, exit_code=2):
        super().__init__(message)
        self.exit_code = exit_code


def validate_apk(path):
    """Refuse a file that cannot be an APK, before anything goes over the wire."""
    if not os.path.isfile(path):
        raise InstallError(f"{path}: no such file; build the APK first (it is never downloaded or guessed)")
    size = os.path.getsize(path)
    if size == 0 or size > MAX_APK:
        raise InstallError(f"{path}: {size} bytes is not a usable APK (empty, or over {MAX_APK} bytes)")
    try:
        with zipfile.ZipFile(path) as z:
            names = set(z.namelist())
            bad = z.testzip()
    except (zipfile.BadZipFile, OSError) as error:
        raise InstallError(f"{path}: not a readable APK (zip) file: {error}")
    if bad:
        raise InstallError(f"{path}: entry {bad} is corrupt; rebuild the APK")
    if "AndroidManifest.xml" not in names or not any(n.startswith("classes") and n.endswith(".dex") for n in names):
        raise InstallError(f"{path}: no AndroidManifest.xml or classes*.dex inside; this is not an APK")


def remote_path(apk):
    """A staging path nobody else uses: random, and made only of characters the TV's shell takes as is."""
    stem = NAME_RE.sub("-", os.path.basename(apk)).strip(".-") or "app.apk"
    if not stem.endswith(".apk"):
        stem += ".apk"
    return f"/data/local/tmp/cytv-{uuid.uuid4().hex[:12]}-{stem[:60]}"


def quote(arg):
    """Single-quoted for the TV's shell. Every argument that reaches here is already plain characters."""
    return "'" + arg.replace("'", "'\\''") + "'"


def check_grants(package, grants):
    if grants and not package:
        raise InstallError("--grant needs --package: a permission is granted to a named package")
    if package and not PACKAGE_RE.fullmatch(package):
        raise InstallError(f"not a package name: {package!r}")
    for g in grants:
        if g not in GRANTABLE:
            raise InstallError(f"refusing to grant {g}: only {', '.join(sorted(GRANTABLE))} can be granted by "
                               "this helper (never WRITE_SECURE_SETTINGS or anything accessibility-related)")


def _run(argv, env):
    return subprocess.run(argv, capture_output=True, text=True, env=env)


def install(apk, package=None, grants=(), keep_remote=False, run=_run, env=None):
    """Install apk. `run(argv, env)` is the process runner, replaceable for a test. Returns the staging path."""
    check_grants(package, grants)
    validate_apk(apk)
    env = dict(os.environ if env is None else env)
    if not env.get("TV_HOST"):
        raise InstallError("set TV_HOST to the TV's IP address, e.g. TV_HOST=192.168.1.50")
    remote = remote_path(apk)
    py = sys.executable
    push = run([py, "-I", os.path.join(TOOLS, "b64push.py"), apk, remote], env)
    if push.returncode != 0:
        why = (push.stderr or push.stdout).strip()
        raise InstallError(f"could not copy {apk} to the TV: {why}", 1 if push.returncode == 1 else 2)
    out = run([py, "-I", os.path.join(TOOLS, "tv.py"), f"pm install -r {quote(remote)}"], env)
    answer = (out.stdout + out.stderr).strip()
    if out.returncode != 0 or "Success" not in answer:
        raise InstallError(f"pm install refused the APK ({answer or 'no answer'}). The copy stays on the TV as "
                           f"{remote} so it can be inspected; remove it with: tools/tv.py 'rm -f {remote}'", 1)
    for g in grants:
        got = run([py, "-I", os.path.join(TOOLS, "tv.py"), f"pm grant {quote(package)} {quote(g)}"], env)
        if got.returncode != 0 or "Exception" in got.stdout + got.stderr:
            raise InstallError(f"installed, but granting {g} failed: {(got.stdout + got.stderr).strip()}", 1)
    if not keep_remote:
        run([py, "-I", os.path.join(TOOLS, "tv.py"), f"rm -f {quote(remote)}"], env)
    return remote


def main(argv=None):
    p = argparse.ArgumentParser(description="Install an APK as an ordinary app (no Home, accessibility or secure-settings changes).")
    p.add_argument("apk")
    p.add_argument("--package", help="package name, needed with --grant")
    p.add_argument("--grant", action="append", default=[], help="permission to grant: " + ", ".join(sorted(GRANTABLE)))
    p.add_argument("--keep-remote", action="store_true", help="leave the staging file on the TV")
    a = p.parse_args(argv)
    try:
        remote = install(a.apk, a.package, a.grant, a.keep_remote)
    except InstallError as error:
        sys.stderr.write(f"install_apk: {error}\n")
        return error.exit_code
    print(f"installed {a.apk} (staged as {remote}" + (", kept)" if a.keep_remote else ", removed)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
