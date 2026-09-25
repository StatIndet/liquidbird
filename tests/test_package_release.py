"""End-to-end checks for the installable release archive."""

from __future__ import annotations

import hashlib
import posixpath
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()


class ReleaseArchiveTest(unittest.TestCase):
    def test_linux_install_files_and_references_are_complete(self) -> None:
        with tempfile.TemporaryDirectory(prefix="liquidbird-release-test-") as directory:
            output = Path(directory)
            completed = subprocess.run(
                [sys.executable, str(ROOT / "scripts/package_release.py"), "--output", str(output)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, completed.returncode, completed.stderr or completed.stdout)

            archive_path = output / f"LiquidBird-{VERSION}.zip"
            checksum_line = (output / "SHA256SUMS").read_text(encoding="utf-8")
            self.assertEqual(
                f"{hashlib.sha256(archive_path.read_bytes()).hexdigest()}  {archive_path.name}\n",
                checksum_line,
            )

            with zipfile.ZipFile(archive_path) as archive:
                names = set(archive.namelist())
                self.assertTrue(
                    {
                        "chrome/liquidbird.css",
                        "chrome/liquidbird-content.css",
                        "chrome/linux/chrome.css",
                        "chrome/linux/content.css",
                        "chrome/linux/mail-layout.css",
                        "chrome/linux/titlebuttons.css",
                        "chrome/linux/titlebuttons/titlebutton-close@2.png",
                        "chrome/userChrome.css",
                        "chrome/userContent.css",
                        "chrome/custom.css.example",
                        "docs/LINUX.md",
                        "integration/niri.kdl",
                        "THIRD_PARTY_NOTICES.md",
                        "checksums/third-party.sha256",
                        "licenses/MACTAHOE.txt",
                    }
                    <= names
                )
                self.assertTrue(any(name.startswith("chrome/Icons/") for name in names))
                self.assertNotIn("chrome/custom.css", names)
                self.assertEqual(
                    (ROOT / "userChrome.css").read_bytes(), archive.read("chrome/userChrome.css")
                )
                self.assertEqual(
                    (ROOT / "userContent.css").read_bytes(), archive.read("chrome/userContent.css")
                )
                for name in names:
                    if not name.endswith(".css"):
                        continue
                    source = archive.read(name).decode("utf-8")
                    references = re.findall(r"url\(\s*([^)]*?)\s*\)", source, re.IGNORECASE)
                    for raw in references:
                        target = unquote(raw.strip().strip('"\''))
                        if not target or target.startswith(("#", "data:", "var(")):
                            continue
                        parsed = urlsplit(target)
                        if parsed.scheme or parsed.netloc or not parsed.path:
                            continue
                        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(name), parsed.path))
                        if resolved == "chrome/custom.css":
                            self.assertIn("chrome/custom.css.example", names)
                            continue
                        self.assertIn(resolved, names, f"{name} references absent {target}")


if __name__ == "__main__":
    unittest.main()
