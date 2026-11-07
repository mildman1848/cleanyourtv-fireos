"""tools/home_redirect.py: the accessibility list is edited entry by entry, never overwritten."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import home_redirect as hr  # noqa: E402

OTHER = "com.example.reader/com.example.reader.Svc"
OTHER2 = "com.gathin.tvhome/com.gathin.tvhome.HomeKeyService"


class ListLogicTest(unittest.TestCase):
    def test_unset_values_parse_as_empty(self):
        for v in (None, "", "null", "  null\n"):
            self.assertEqual([], hr.parse_list(v))

    def test_add_preserves_other_services_once(self):
        both = f"{OTHER}:{OTHER2}"
        added = hr.with_component(both)
        self.assertEqual(f"{both}:{hr.COMPONENT}", added)
        self.assertEqual(added, hr.with_component(added))
        self.assertEqual(hr.COMPONENT, hr.with_component("null"))

    def test_remove_touches_only_our_entry_in_either_form(self):
        for ours in (hr.COMPONENT, hr.SHORT):
            self.assertEqual(f"{OTHER}:{OTHER2}", hr.without_component(f"{OTHER}:{ours}:{OTHER2}"))
        self.assertEqual("", hr.without_component(hr.COMPONENT))
        # the sibling HomeKeyService of the same package is not ours
        self.assertEqual(OTHER2, hr.without_component(OTHER2))

    def test_change_script_is_compare_and_set_and_deletes_an_empty_list(self):
        s = hr.change_script(f"{OTHER}:{hr.COMPONENT}", OTHER)
        self.assertIn(f"[ \"$c\" = '{OTHER}:{hr.COMPONENT}' ]", s)
        self.assertIn(f"settings put secure enabled_accessibility_services '{OTHER}'", s)
        self.assertIn("settings delete secure enabled_accessibility_services", hr.change_script(hr.COMPONENT, ""))
        self.assertNotIn("accessibility_enabled", s)

    def test_fire_os_detection(self):
        self.assertTrue(hr.is_fire_os("Amazon", "", "", []))
        self.assertTrue(hr.is_fire_os("Hisense", "Amazon", "x", []))
        self.assertTrue(hr.is_fire_os("x", "y", "aftkm", []))
        self.assertTrue(hr.is_fire_os("x", "y", "z", ["com.amazon.tv.launcher"]))
        self.assertFalse(hr.is_fire_os("Xiaomi", "Xiaomi", "MiTV", ["com.android.tv.settings"]))


class FakeTv:
    def __init__(self, listing="null", manufacturer="Amazon", packages=("com.amazon.tv.launcher", "com.gathin.tvhome")):
        self.listing, self.manufacturer, self.packages, self.commands = listing, manufacturer, packages, []

    def __call__(self, cmd):
        self.commands.append(cmd)
        if cmd == "getprop ro.product.manufacturer":
            return self.manufacturer
        if cmd.startswith("getprop"):
            return ""
        if cmd == "pm list packages":
            return "\n".join("package:" + p for p in self.packages)
        if cmd == "settings get secure enabled_accessibility_services":
            return self.listing
        if cmd.startswith('c=$(settings get'):
            return "cytv-changed"
        return ""

    def writes(self):
        return [c for c in self.commands if "settings put" in c or "settings delete" in c]


class CommandTest(unittest.TestCase):
    def test_enable_needs_confirm_and_touches_nothing_without_it(self):
        tv = FakeTv()
        self.assertEqual(2, hr.main(["enable"], shell=tv))
        self.assertEqual([], tv.commands)

    def test_enable_refuses_a_non_fire_tv_and_a_missing_launcher(self):
        tv = FakeTv(manufacturer="Xiaomi", packages=("com.gathin.tvhome",))
        self.assertEqual(2, hr.main(["enable", "--confirm"], shell=tv))
        self.assertEqual([], tv.writes())
        tv = FakeTv(packages=("com.amazon.tv.launcher",))
        self.assertEqual(2, hr.main(["enable", "--confirm"], shell=tv))
        self.assertEqual([], tv.writes())

    def test_enable_appends_and_keeps_other_services(self):
        tv = FakeTv(listing=OTHER)
        self.assertEqual(0, hr.main(["enable", "--confirm"], shell=tv))
        script = [c for c in tv.commands if c.startswith("c=$(")][0]
        self.assertIn(f"'{OTHER}:{hr.COMPONENT}'", script)

    def test_disable_removes_only_ours_and_leaves_accessibility_enabled_alone(self):
        tv = FakeTv(listing=f"{OTHER}:{hr.COMPONENT}")
        self.assertEqual(0, hr.main(["disable"], shell=tv))
        joined = " ".join(tv.commands)
        self.assertIn(f"settings put secure enabled_accessibility_services '{OTHER}'", joined)
        self.assertNotIn("accessibility_enabled", joined)

    def test_disable_when_already_off_writes_nothing(self):
        tv = FakeTv(listing=OTHER)
        self.assertEqual(0, hr.main(["disable"], shell=tv))
        self.assertEqual([], tv.writes())

    def test_a_moved_list_is_not_overwritten(self):
        tv = FakeTv(listing=hr.COMPONENT)
        orig = tv.__call__
        tv_cmd = lambda c: "cytv-list-moved" if c.startswith("c=$(") else orig(c)  # noqa: E731
        self.assertEqual(1, hr.main(["disable"], shell=tv_cmd))

    def test_bad_arguments(self):
        for argv in ([], ["bogus"], ["status", "x"], ["disable", "--confirm"]):
            self.assertEqual(2, hr.main(argv, shell=FakeTv()), argv)


if __name__ == "__main__":
    unittest.main()
