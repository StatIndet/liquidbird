#!/usr/bin/env python3
"""Dependency-free release checks for LiquidBird."""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".demo", ".git", "dist", "__pycache__"}
TEXT_SUFFIXES = {".css", ".html", ".kdl", ".md", ".py", ".yml", ".yaml", ".txt"}
REQUIRED = {
    ".gitattributes",
    ".gitignore",
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "README.md",
    "SUPPORT.md",
    "THIRD_PARTY_NOTICES.md",
    "VERSION",
    "liquidbird.css",
    "liquidbird-content.css",
    "custom.css",
    "docs/LINUX.md",
    "docs/screenshots/liquidbird-mail-dark.png",
    "docs/screenshots/liquidbird-mail-light.png",
    "integration/niri.kdl",
    "linux/chrome.css",
    "linux/content.css",
    "linux/mail-layout.css",
    "linux/titlebuttons.css",
    "licenses/MACTAHOE.txt",
    "userChrome.css",
    "userContent.css",
}
LINUX_STYLESHEETS = (
    "linux/chrome.css",
    "linux/content.css",
    "linux/mail-layout.css",
    "linux/titlebuttons.css",
)


class Checks:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.count = 0

    def check(self, condition: bool, message: str) -> None:
        self.count += 1
        if not condition:
            self.errors.append(message)


def repository_files() -> list[Path]:
    try:
        listed = subprocess.run(
            [
                "git",
                "-C",
                str(ROOT),
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
                "-z",
            ],
            check=True,
            capture_output=True,
        ).stdout
    except (FileNotFoundError, subprocess.CalledProcessError):
        listed = None

    if listed is not None:
        return sorted(
            path
            for relative in listed.decode("utf-8").split("\0")
            if relative
            if (path := ROOT / relative).is_file()
            and not any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts)
        )

    return sorted(
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and path.name != ".DS_Store"
        and not path.name.startswith("._")
        and not any(part in SKIP_DIRS for part in path.parts)
    )


def strip_css_comments_and_strings(source: str) -> str:
    output: list[str] = []
    index = 0
    state = "code"
    quote = ""
    while index < len(source):
        char = source[index]
        following = source[index + 1] if index + 1 < len(source) else ""
        if state == "comment":
            if char == "*" and following == "/":
                output.extend("  ")
                index += 2
                state = "code"
            else:
                output.append("\n" if char == "\n" else " ")
                index += 1
        elif state == "string":
            if char == "\\":
                output.append(" ")
                if following:
                    output.append("\n" if following == "\n" else " ")
                    index += 2
                else:
                    index += 1
            elif char == quote:
                output.append(" ")
                index += 1
                state = "code"
            else:
                output.append("\n" if char == "\n" else " ")
                index += 1
        elif char == "/" and following == "*":
            output.extend("  ")
            index += 2
            state = "comment"
        elif char in {'"', "'"}:
            output.append(" ")
            quote = char
            index += 1
            state = "string"
        else:
            output.append(char)
            index += 1
    return "".join(output)


def check_css_balance(checks: Checks, path: Path) -> None:
    source = strip_css_comments_and_strings(path.read_text(encoding="utf-8"))
    stack: list[int] = []
    for line_number, line in enumerate(source.splitlines(), start=1):
        for char in line:
            if char == "{":
                stack.append(line_number)
            elif char == "}":
                checks.check(bool(stack), f"{path.relative_to(ROOT)}:{line_number}: unmatched }}")
                if stack:
                    stack.pop()
    checks.check(not stack, f"{path.relative_to(ROOT)}: unclosed {{ from line {stack[-1] if stack else '?'}")


def check_linux_platform_scope(checks: Checks, path: Path) -> None:
    """Keep the shared loader's Linux imports inert on macOS."""
    source = strip_css_comments_and_strings(path.read_text(encoding="utf-8"))
    depth = 0
    prelude: list[str] = []
    top_level_blocks = 0
    for char in source:
        if char == "{":
            if depth == 0:
                top_level_blocks += 1
                checks.check(
                    "".join(prelude).strip().startswith("@media (-moz-platform: linux)"),
                    f"{path.relative_to(ROOT)}: top-level CSS must be gated to Linux",
                )
                prelude.clear()
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                prelude.clear()
        elif depth == 0:
            prelude.append(char)
    checks.check(top_level_blocks > 0, f"{path.relative_to(ROOT)}: no Linux-scoped CSS blocks")


def local_target(raw_target: str) -> str | None:
    target = unquote(raw_target.strip().strip('"\''))
    if not target or target.startswith(("#", "data:", "var(")):
        return None
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc:
        return None
    return parsed.path or None


def check_reference(checks: Checks, source: Path, target: str) -> None:
    relative = local_target(target)
    if relative is None:
        return
    resolved = (source.parent / relative).resolve()
    checks.check(
        resolved.is_relative_to(ROOT) and resolved.exists(),
        f"{source.relative_to(ROOT)}: missing or out-of-repository reference {target!r}",
    )


def check_references(checks: Checks, path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    if path.suffix == ".css":
        for match in re.finditer(r"url\(\s*([^)]*?)\s*\)", source, re.IGNORECASE):
            check_reference(checks, path, match.group(1))
    elif path.suffix == ".html":
        for match in re.finditer(r"(?:href|src)\s*=\s*[\"']([^\"']+)[\"']", source, re.IGNORECASE):
            check_reference(checks, path, match.group(1))
    elif path.suffix == ".md":
        for match in re.finditer(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+[^)]*)?\)", source):
            check_reference(checks, path, match.group(1).strip("<>"))


def check_svg(checks: Checks, path: Path) -> None:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as error:
        checks.check(False, f"{path.relative_to(ROOT)}: malformed SVG: {error}")
        return
    checks.check(root.tag.rsplit("}", 1)[-1] == "svg", f"{path.relative_to(ROOT)}: root element is not svg")
    dangerous = {"script", "foreignObject", "iframe", "object", "embed"}
    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1]
        checks.check(tag not in dangerous, f"{path.relative_to(ROOT)}: disallowed <{tag}> element")
        for attribute, value in element.attrib.items():
            name = attribute.rsplit("}", 1)[-1].lower()
            checks.check(not name.startswith("on"), f"{path.relative_to(ROOT)}: event attribute {name}")
            if name == "href":
                checks.check(
                    not urlsplit(value).scheme and not value.startswith("//"),
                    f"{path.relative_to(ROOT)}: external SVG reference {value!r}",
                )


def check_checksums(checks: Checks) -> None:
    manifest = ROOT / "checksums/third-party.sha256"
    entries: set[str] = set()
    for line_number, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        checks.check(match is not None, f"{manifest.relative_to(ROOT)}:{line_number}: invalid checksum line")
        if match is None:
            continue
        expected, relative = match.groups()
        entries.add(relative)
        path = ROOT / relative
        checks.check(path.is_file(), f"Checksum target missing: {relative}")
        if path.is_file():
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            checks.check(actual == expected, f"Third-party file changed without manifest update: {relative}")
    expected_entries = {
        path.relative_to(ROOT).as_posix() for path in (ROOT / "Icons").glob("*.svg")
    } | {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "linux/titlebuttons").glob("*.png")
    } | {"licenses/FLUENTBIRD.txt", "licenses/LUCIDE.txt", "licenses/MACTAHOE.txt"}
    checks.check(
        entries == expected_entries,
        "Third-party checksum manifest must exactly cover bundled icons, title buttons, and licenses",
    )


def main() -> int:
    checks = Checks()
    files = repository_files()
    relative_files = {path.relative_to(ROOT).as_posix() for path in files}

    for required in sorted(REQUIRED):
        checks.check(required in relative_files, f"Required release file missing: {required}")

    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    checks.check(
        bool(re.fullmatch(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)", version)),
        f"Invalid VERSION value: {version!r}",
    )

    private_home_prefix = "/" + "Users" + "/"
    owner_placeholder = "github.com/" + "OWNER" + "/"
    local_file_scheme = "file" + "://"

    for path in files:
        relative = path.relative_to(ROOT)
        checks.check(path.name != ".DS_Store" and not path.name.startswith("._"), f"Forbidden macOS metadata: {relative}")
        if path.suffix in TEXT_SUFFIXES or path.name in {"VERSION", "LICENSE"}:
            text = path.read_text(encoding="utf-8")
            checks.check(private_home_prefix not in text and local_file_scheme not in text, f"Private local path found in {relative}")
            checks.check(owner_placeholder not in text, f"Unresolved repository-owner placeholder in {relative}")
        if path.suffix in {".css", ".html", ".md"}:
            check_references(checks, path)
        if path.suffix == ".css":
            check_css_balance(checks, path)
        if path.suffix == ".svg":
            check_svg(checks, path)

    for relative in LINUX_STYLESHEETS:
        path = ROOT / relative
        if path.is_file():
            check_linux_platform_scope(checks, path)

    user_chrome = (ROOT / "userChrome.css").read_text(encoding="utf-8")
    chrome_imports = re.findall(r'^@import\s+url\("([^"]+)"\);\s*$', user_chrome, re.MULTILINE)
    checks.check(
        chrome_imports == [
            "liquidbird.css",
            "linux/chrome.css",
            "linux/mail-layout.css",
            "linux/titlebuttons.css",
            "custom.css",
        ],
        "userChrome.css must import core, Linux layers, then custom CSS in that order",
    )
    user_content = (ROOT / "userContent.css").read_text(encoding="utf-8")
    content_imports = re.findall(r'^@import\s+url\("([^"]+)"\);\s*$', user_content, re.MULTILINE)
    checks.check(
        content_imports == ["liquidbird-content.css", "linux/content.css"],
        "userContent.css must import core content CSS before Linux content CSS",
    )
    notices = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
    checks.check("471eace530c469ed97c943b07927939e83cf8966" in notices, "Pinned FluentBird revision missing")
    checks.check("33342b87902b8d2e596fbcddb01a253c6e6586d0" in notices, "Pinned Lucide revision missing")
    checks.check("f19899811eff6d127afc38c4fa4981b220cb2ea2" in notices, "Pinned MacTahoe revision missing")
    check_checksums(checks)

    if checks.errors:
        print(f"LiquidBird checks failed ({len(checks.errors)} errors):", file=sys.stderr)
        for error in checks.errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print(f"LiquidBird checks passed ({checks.count} assertions across {len(files)} files).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
