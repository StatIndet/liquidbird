#!/usr/bin/env python3
"""Create a deterministic LiquidBird release ZIP."""

from __future__ import annotations

import argparse
import hashlib
import re
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXED_TIMESTAMP = (2026, 7, 25, 0, 0, 0)
CHROME_FILES = {
    "liquidbird.css": "chrome/liquidbird.css",
    "liquidbird-content.css": "chrome/liquidbird-content.css",
    "userChrome.css": "chrome/userChrome.css",
    "userContent.css": "chrome/userContent.css",
    "custom.css": "chrome/custom.css.example",
}
LINUX_RELEASE_SUFFIXES = {".css", ".svg", ".png", ".webp", ".avif", ".woff", ".woff2"}
LINUX_ENTRY_POINTS = {
    "linux/chrome.css",
    "linux/content.css",
    "linux/mail-layout.css",
    "linux/titlebuttons.css",
}
DOCUMENT_FILES = [
    "CHANGELOG.md",
    "LICENSE",
    "README.md",
    "THIRD_PARTY_NOTICES.md",
    "VERSION",
    "checksums/third-party.sha256",
    "docs/COMPATIBILITY.md",
    "docs/COVERAGE.md",
    "docs/DESIGN.md",
    "docs/LINUX.md",
    "docs/LINUX_STAGE1.md",
    "docs/RELEASING.md",
    "docs/SCREENSHOTS.md",
    "docs/screenshots/liquidbird-mail-dark.png",
    "docs/screenshots/liquidbird-mail-light.png",
    "docs/screenshots/liquidbird-linux-niri-dark.png",
    "docs/screenshots/liquidbird-linux-niri-light.png",
    "licenses/FLUENTBIRD.txt",
    "licenses/LUCIDE.txt",
    "licenses/MACTAHOE.txt",
    "integration/niri.kdl",
    "integration/niri-stage1.kdl",
    "scripts/demo.py",
]


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist", help="output directory")
    parser.add_argument("--version", help="release version; defaults to VERSION")
    return parser.parse_args()


def add_file(archive: zipfile.ZipFile, source: Path, destination: str) -> None:
    info = zipfile.ZipInfo(destination, FIXED_TIMESTAMP)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    info.create_system = 3
    archive.writestr(info, source.read_bytes())


def expected_files() -> dict[str, Path]:
    files = {destination: ROOT / source for source, destination in CHROME_FILES.items()}
    for icon in sorted((ROOT / "Icons").glob("*.svg")):
        files[f"chrome/Icons/{icon.name}"] = icon
    linux_root = ROOT / "linux"
    for source in sorted(linux_root.rglob("*")):
        if not source.is_file():
            continue
        relative = source.relative_to(ROOT).as_posix()
        if source.is_symlink() or source.suffix.lower() not in LINUX_RELEASE_SUFFIXES:
            raise SystemExit(f"Unexpected Linux release input: {relative}")
        files[f"chrome/{relative}"] = source
    missing_linux = LINUX_ENTRY_POINTS - {
        path.relative_to(ROOT).as_posix() for path in files.values()
    }
    if missing_linux:
        raise SystemExit("Linux entry points are missing: " + ", ".join(sorted(missing_linux)))
    for relative in DOCUMENT_FILES:
        files[relative] = ROOT / relative
    return files


def main() -> int:
    options = arguments()
    repository_version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    version = options.version or repository_version
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise SystemExit(f"Invalid semantic version: {version!r}")
    if version != repository_version:
        raise SystemExit(f"Requested version {version} does not match VERSION ({repository_version})")

    files = expected_files()
    missing = [destination for destination, source in files.items() if not source.is_file()]
    if missing:
        raise SystemExit("Release inputs are missing: " + ", ".join(missing))

    options.output.mkdir(parents=True, exist_ok=True)
    destination = options.output / f"LiquidBird-{version}.zip"
    with zipfile.ZipFile(destination, "w") as archive:
        for archive_path, source in sorted(files.items()):
            add_file(archive, source, archive_path)

    with zipfile.ZipFile(destination) as archive:
        actual = set(archive.namelist())
        expected = set(files)
        if actual != expected:
            raise SystemExit("Release archive contents differ from the packaging manifest")
        if "chrome/custom.css" in actual or "chrome/custom.css.example" not in actual:
            raise SystemExit("Release must preserve user customizations via custom.css.example")
        bad_paths = [name for name in actual if name.startswith("/") or ".." in Path(name).parts]
        if bad_paths:
            raise SystemExit("Unsafe archive paths: " + ", ".join(bad_paths))

    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    checksum = options.output / "SHA256SUMS"
    checksum.write_text(f"{digest}  {destination.name}\n", encoding="utf-8")
    print(f"Created {destination}")
    print(f"SHA-256 {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
