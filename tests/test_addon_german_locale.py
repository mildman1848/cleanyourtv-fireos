"""TV Hub, Sources and Open on wake ship a complete German (values-de) locale next to the English defaults."""
from collections import Counter
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
ADDONS = ("tv-hub", "sources", "wake-app")
PLACEHOLDER = re.compile(r"%(?:\d+\$)?[sdf]")


def res(addon, folder):
    return ROOT / "addons" / addon / "app/src/main/res" / folder / "strings.xml"


def load(path):
    strings, plurals = {}, {}
    for el in ET.parse(path).getroot():
        if el.tag == "string":
            strings[el.get("name")] = el.text or ""
        elif el.tag == "plurals":
            plurals[el.get("name")] = {i.get("quantity"): i.text or "" for i in el}
    return strings, plurals


def holes(text):
    return Counter(PLACEHOLDER.findall(text))


class GermanLocaleTest(unittest.TestCase):
    def test_german_has_every_default_string_and_nothing_extra(self):
        for a in ADDONS:
            with self.subTest(addon=a):
                (s, p), (ds, dp) = load(res(a, "values")), load(res(a, "values-de"))
                self.assertEqual(set(s), set(ds), "string names differ")
                self.assertEqual(set(p), set(dp), "plural names differ")
                for k, v in ds.items():
                    self.assertTrue(v.strip(), f"{a}: empty German string {k}")

    def test_placeholders_match(self):
        for a in ADDONS:
            (s, p), (ds, dp) = load(res(a, "values")), load(res(a, "values-de"))
            for k in s:
                self.assertEqual(holes(s[k]), holes(ds[k]), f"{a}:{k} placeholders differ")
            for k in p:
                self.assertEqual({"one", "other"}, set(dp[k]), f"{a}:{k} German needs one and other")
                for q, v in dp[k].items():
                    self.assertEqual(holes(p[k]["other"]), holes(v), f"{a}:{k}/{q} placeholders differ")

    def test_german_is_not_a_copy_of_english(self):
        for a in ADDONS:
            s, _ = load(res(a, "values"))
            ds, _ = load(res(a, "values-de"))
            same = [k for k in s if s[k] == ds[k] and len(s[k]) > 25]
            self.assertEqual([], same, f"{a}: long strings left in English")

    def test_english_stays_the_default(self):
        for a in ADDONS:
            self.assertFalse((ROOT / "addons" / a / "app/src/main/res/values-en").exists())


class TvHubResourceUsageTest(unittest.TestCase):
    SRC = ROOT / "addons/tv-hub/app/src/main/java"
    # a user-facing literal handed straight to a UI call
    LITERAL = re.compile(
        r'(?:Ui\.(?:text|button)\([^,]+,\s*|Toast\.makeText\([^,]+,\s*|\.set(?:Title|Message|PositiveButton|NegativeButton|NeutralButton|Hint)\(|hint\(|\.hint = |\.contentDescription = )"[^"$]*[A-Za-z]{2}')

    def kotlin(self):
        return {p: p.read_text() for p in self.SRC.rglob("*.kt")}

    def test_every_reference_exists_and_every_string_is_used(self):
        s, p = load(res("tv-hub", "values"))
        code = "\n".join(self.kotlin().values()) + (ROOT / "addons/tv-hub/app/src/main/AndroidManifest.xml").read_text()
        used_s = set(re.findall(r"R\.string\.(\w+)", code)) | set(re.findall(r"@string/(\w+)", code))
        used_p = set(re.findall(r"R\.plurals\.(\w+)", code))
        self.assertEqual(set(), used_s - set(s), "R.string used but not defined")
        self.assertEqual(set(), used_p - set(p), "R.plurals used but not defined")
        self.assertEqual(set(), set(s) - used_s, "strings defined but unused")
        self.assertEqual(set(), set(p) - used_p, "plurals defined but unused")

    def test_no_hardcoded_ui_text_left(self):
        left = []
        for path, text in self.kotlin().items():
            for n, line in enumerate(text.splitlines(), 1):
                if self.LITERAL.search(line):
                    left.append(f"{path.name}:{n}: {line.strip()[:90]}")
        self.assertEqual([], left)


if __name__ == "__main__":
    unittest.main()
