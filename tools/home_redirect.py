#!/usr/bin/env python3
"""Status, enable and disable the launcher's opt-in Home redirect on a Fire OS TV.

Usage: TV_HOST=<tv ip> home_redirect.py status
       TV_HOST=<tv ip> home_redirect.py enable --confirm
       TV_HOST=<tv ip> home_redirect.py disable

The redirect is HomeRedirectService, an accessibility service of the launcher (docs/fireos.md). It
is OFF after every install: nothing in this repo turns it on except `enable --confirm`, which a
person types after reading what it changes. Both directions touch only this one entry of
`enabled_accessibility_services`, every other service on the list stays, and the write is a
compare-and-set (it is dropped if the list changed between the read and the write). `disable` never
touches `accessibility_enabled`; `enable` sets it to 1 only if it is not 1 already.

`enable` refuses on a TV that does not look like Fire OS, and when the launcher is not installed.
Exit status: 0 done, 1 the TV's answer was not what the change needed, 2 refused before any change.
"""
import os
import re
import subprocess
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
PACKAGE = "com.gathin.tvhome"
COMPONENT = f"{PACKAGE}/{PACKAGE}.HomeRedirectService"
SHORT = f"{PACKAGE}/.HomeRedirectService"
LIST_KEY = "enabled_accessibility_services"
# Fire OS's own home screens (cleanyourtv-app core/planner PlatformFacts.kt, FireOs.HOMES). Never switched off.
FIRE_HOMES = ("com.amazon.tv.launcher", "com.amazon.firehomestarter")


def quote(arg):
    return "'" + arg.replace("'", "'\\''") + "'"


def parse_list(value):
    """The colon list Android stores; unset reads back as '', 'null' or nothing."""
    if value is None or value.strip() in ("", "null"):
        return []
    return [item for item in value.strip().split(":") if item]


def has_component(value):
    return any(item in (COMPONENT, SHORT) for item in parse_list(value))


def with_component(value):
    """The list with our entry added once; every other entry kept, in order."""
    items = parse_list(value)
    return ":".join(items if has_component(value) else items + [COMPONENT])


def without_component(value):
    """The list with only our entry removed (full or short form)."""
    return ":".join(i for i in parse_list(value) if i not in (COMPONENT, SHORT))


def is_fire_os(manufacturer, brand, model, packages):
    """cleanyourtv-app's FireOs.isFireOs: Amazon as maker or brand, an AFT model code, or a Fire home installed."""
    return ("amazon" in (manufacturer.strip().lower(), brand.strip().lower())
            or model.strip().upper().startswith("AFT")
            or any(h in packages for h in FIRE_HOMES))


def change_script(current, new):
    """Compare-and-set shell line: write `new` only while the list still reads `current`."""
    write = (f"settings delete secure {LIST_KEY}" if not new
             else f"settings put secure {LIST_KEY} {quote(new)}")
    return (f'c=$(settings get secure {LIST_KEY}); if [ "$c" = {quote(current)} ]; then {write}; '
            f"echo cytv-changed; else echo cytv-list-moved; fi")


def tv_shell(command):
    r = subprocess.run([sys.executable, "-I", os.path.join(TOOLS, "tv.py"), command],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"home_redirect: tv.py could not run the command: {(r.stderr or r.stdout).strip()}")
    return r.stdout.strip()


def read_list(shell):
    return shell(f"settings get secure {LIST_KEY}")


def set_list(shell, current, new):
    out = shell(change_script(current, new))
    if "cytv-changed" not in out:
        raise SystemExit("home_redirect: the accessibility list changed while this ran, so nothing was written. "
                         "Run it again.")


def status(shell):
    current = read_list(shell)
    state = "ON" if has_component(current) else "off"
    print(f"Home redirect: {state}\naccessibility services on the TV: {current or 'none'}")
    return 0


def enable(shell):
    props = {k: shell(f"getprop ro.product.{k}") for k in ("manufacturer", "brand", "model")}
    pkgs = shell("pm list packages").replace("package:", " ")
    if not is_fire_os(props["manufacturer"], props["brand"], props["model"], pkgs.split()):
        raise SystemExit("home_redirect: this does not look like a Fire OS TV; nothing was changed.")
    if PACKAGE not in pkgs.split():
        raise SystemExit(f"home_redirect: {PACKAGE} is not installed; install the launcher first. Nothing was changed.")
    current = read_list(shell)
    if not has_component(current):
        set_list(shell, current, with_component(current))
    shell('[ "$(settings get secure accessibility_enabled)" = 1 ] || settings put secure accessibility_enabled 1')
    print("Home redirect is ON. Check it with the real remote's Home button, then reboot once and confirm ADB "
          "and Amazon's Home come back. Undo: home_redirect.py disable")
    return 0


def disable(shell):
    current = read_list(shell)
    if has_component(current):
        set_list(shell, current, without_component(current))
    print("Home redirect is off (other accessibility services were left as they were).")
    return 0


def main(argv=None, shell=tv_shell):
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] not in ("status", "enable", "disable") or len(args) > 2:
        sys.stderr.write(__doc__.split("\n\n")[0] + "\n")
        return 2
    if args[0] == "enable" and args[1:] != ["--confirm"]:
        sys.stderr.write("home_redirect: `enable` changes what Home does on this TV. Read docs/fireos.md, then run "
                         "`enable --confirm`. Nothing was changed.\n")
        return 2
    if args[0] != "enable" and len(args) > 1:
        sys.stderr.write(f"home_redirect: `{args[0]}` takes no argument.\n")
        return 2
    try:
        return {"status": status, "enable": enable, "disable": disable}[args[0]](shell)
    except SystemExit as stop:
        if isinstance(stop.code, str):
            sys.stderr.write(stop.code + "\n")
            return 2 if "does not look" in stop.code or "not installed" in stop.code else 1
        raise


if __name__ == "__main__":
    sys.exit(main())
