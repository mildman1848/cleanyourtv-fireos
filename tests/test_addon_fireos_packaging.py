"""Sources and Open on wake sign their release APK with the debug key so `pm install` accepts it; TV Hub's
release is signed only from environment variables, so its Fire OS install uses the debug APK. Each README says so."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent.parent


def read(addon, name):
    return (ROOT / "addons" / addon / name).read_text(encoding="utf-8")


class PackagingTest(unittest.TestCase):
    def test_sources_and_wake_release_is_installable(self):
        for a in ("sources", "wake-app"):
            with self.subTest(addon=a):
                self.assertIn("signingConfig signingConfigs.debug", read(a, "app/build.gradle"))

    def test_tv_hub_signing_comes_only_from_environment(self):
        g = read("tv-hub", "app/build.gradle.kts")
        self.assertIn('System.getenv("TVHUB_KEYSTORE")', g)
        self.assertNotRegex(g, r'(storePassword|keyPassword)\s*=\s*"')
        self.assertFalse(list((ROOT / "addons").glob("*/**/*.jks")) + list((ROOT / "addons").glob("*/**/*.keystore")))

    def test_readmes_say_how_the_apk_is_signed(self):
        for a in ("tv-hub", "sources", "wake-app"):
            with self.subTest(addon=a):
                self.assertRegex(read(a, "README.md"), r"(?i)signed with the debug key|debug-signed")

    def test_tv_hub_readme_warns_release_without_key_is_unsigned(self):
        self.assertRegex(read("tv-hub", "README.md"), r"(?i)unsigned")

    def test_fireos_doc_names_the_exact_apk_paths(self):
        doc = (ROOT / "docs/fireos.md").read_text(encoding="utf-8")
        for p in ("addons/tv-hub/app/build/outputs/apk/debug/app-debug.apk",
                  "addons/sources/app/build/outputs/apk/release/app-release.apk",
                  "addons/wake-app/app/build/outputs/apk/release/app-release.apk"):
            self.assertIn(p, doc)


if __name__ == "__main__":
    unittest.main()
