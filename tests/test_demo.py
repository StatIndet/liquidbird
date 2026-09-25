"""Structural tests for the synthetic Thunderbird screenshot fixture."""

from __future__ import annotations

import importlib.util
import json
import mailbox
import shutil
import sqlite3
import sys
import unittest
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("liquidbird_demo", ROOT / "scripts/demo.py")
assert SPEC and SPEC.loader
demo = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = demo
SPEC.loader.exec_module(demo)


class DemoProfileTest(unittest.TestCase):
    profile = ROOT / ".demo" / "test-profile"

    @classmethod
    def setUpClass(cls) -> None:
        demo.prepare(cls.profile, date(2026, 7, 28))

    @classmethod
    def tearDownClass(cls) -> None:
        marker = cls.profile / demo.PROFILE_MARKER
        if marker.is_file():
            shutil.rmtree(cls.profile)

    def test_summary_and_native_fixture_counts(self) -> None:
        summary = json.loads((self.profile / "DEMO.json").read_text(encoding="utf-8"))
        self.assertTrue(summary["synthetic"])
        self.assertTrue(summary["offline"])
        self.assertTrue(summary["systemContactsDisabled"])
        self.assertEqual(16, sum(summary["mailboxes"].values()))
        self.assertEqual(7, summary["contacts"])
        self.assertEqual(6, summary["calendarEvents"])

        inbox = mailbox.mbox(self.profile / "Mail/studio.example.invalid/Inbox")
        try:
            self.assertEqual(10, len(inbox))
            self.assertEqual("Final review: Liquid launch assets", inbox[0]["Subject"])
            self.assertEqual(
                "Noah Williams <noah.williams@example.com>",
                inbox[0]["Cc"],
            )
        finally:
            inbox.close()

        database = sqlite3.connect(self.profile / "abook.sqlite")
        try:
            cards = database.execute(
                "SELECT COUNT(DISTINCT card) FROM properties WHERE name = '_vCard'"
            ).fetchone()[0]
            version = database.execute("PRAGMA user_version").fetchone()[0]
        finally:
            database.close()
        self.assertEqual(7, cards)
        self.assertEqual(4, version)

        calendar = (self.profile / "liquidbird-demo.ics").read_text(encoding="utf-8")
        self.assertEqual(6, calendar.count("BEGIN:VEVENT"))
        self.assertIn("DTSTART;VALUE=DATE:20260729", calendar)

    def test_privacy_and_offline_guards(self) -> None:
        prefs = (self.profile / "user.js").read_text(encoding="utf-8")
        self.assertIn('user_pref("offline.startup_state", 3);', prefs)
        self.assertIn('user_pref("network.online", false);', prefs)
        self.assertIn('user_pref("mail.rights.version", 1);', prefs)
        self.assertIn(
            'user_pref("mailnews.start_page_override.mstone", "999999.0");',
            prefs,
        )
        self.assertIn('user_pref("mailnews.start_page.override_url", "");', prefs)
        self.assertIn('user_pref("ldap_2.servers.osx.dirType", -1);', prefs)
        self.assertIn("studio.example.invalid", prefs)
        self.assertNotIn("@gmail.", prefs)
        self.assertNotIn("@icloud.", prefs)

        for path in (self.profile / "Mail").rglob("*"):
            if path.is_file():
                contents = path.read_bytes()
                self.assertNotIn(b"@gmail.", contents)
                self.assertNotIn(b"@icloud.", contents)

    def test_theme_is_installed_from_working_tree(self) -> None:
        chrome = self.profile / "chrome"
        for name in (
            "liquidbird.css",
            "liquidbird-content.css",
            "custom.css",
            "userChrome.css",
            "userContent.css",
        ):
            self.assertEqual((ROOT / name).read_bytes(), (chrome / name).read_bytes())
        self.assertEqual(
            {
                path.relative_to(ROOT / "linux"): path.read_bytes()
                for path in (ROOT / "linux").rglob("*") if path.is_file()
            },
            {
                path.relative_to(chrome / "linux"): path.read_bytes()
                for path in (chrome / "linux").rglob("*") if path.is_file()
            },
        )
        self.assertEqual(
            {path.name for path in (ROOT / "Icons").glob("*.svg")},
            {path.name for path in (chrome / "Icons").glob("*.svg")},
        )

    def test_mail_capture_enables_local_system_automation(self) -> None:
        command = demo.thunderbird_command(
            Path("/Applications/Thunderbird Beta.app/Contents/MacOS/thunderbird"),
            self.profile,
            "mail",
            marionette=True,
        )
        self.assertIn("--marionette", command)
        self.assertIn("--remote-allow-system-access", command)
        self.assertIn("--no-remote", command)

    def test_reset_refuses_unmarked_directory(self) -> None:
        unmarked = ROOT / ".demo" / "unmarked-test"
        unmarked.mkdir(parents=True, exist_ok=True)
        try:
            with self.assertRaises(SystemExit):
                demo.reset_generated_directory(unmarked)
        finally:
            unmarked.rmdir()


if __name__ == "__main__":
    unittest.main()
