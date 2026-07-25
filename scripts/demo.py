#!/usr/bin/env python3
"""Build and photograph a private-data-free LiquidBird Thunderbird demo.

The generated profile is deliberately disposable, offline, and limited to
synthetic data. Screenshot capture uses only macOS system tools and the
installed Thunderbird application; profile generation is cross-platform.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import shutil
import signal
import socket
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime, time as datetime_time, timedelta, timezone
from email.generator import BytesGenerator
from email.message import EmailMessage
from email.policy import SMTP
from io import BytesIO
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEMO_ROOT = ROOT / ".demo"
DEFAULT_PROFILE = DEMO_ROOT / "profile"
DEFAULT_SCREENSHOTS = DEMO_ROOT / "screenshots"
README_SCREENSHOTS = ROOT / "docs" / "screenshots"
DEFAULT_THUNDERBIRD = Path(
    "/Applications/Thunderbird Beta.app/Contents/MacOS/thunderbird"
)
PROFILE_MARKER = ".liquidbird-demo-profile"
WINDOW_POSITION = (72, 72)
WINDOW_SIZE = (1440, 960)
SURFACES = (
    "mail",
    "message",
    "addressbook",
    "calendar",
    "settings",
    "compose",
    "account-settings",
    "addons",
)


@dataclass(frozen=True)
class MessageSpec:
    sender_name: str
    sender_email: str
    subject: str
    days_ago: int
    hour: int
    minute: int
    body: str
    read: bool = False
    flagged: bool = False
    attachment: tuple[str, str, bytes] | None = None


INBOX_MESSAGES = (
    MessageSpec(
        "Maya Chen",
        "maya.chen@example.com",
        "Final review: Liquid launch assets",
        0,
        10,
        42,
        "The final launch assets are ready for review. I added the alternate "
        "mark, the dark appearance export, and updated spacing notes.\n\n"
        "Could you leave comments before our 14:00 review?",
        flagged=True,
        attachment=(
            "launch-checklist.txt",
            "text/plain",
            b"Liquid launch checklist\n- Review exports\n- Confirm copy\n- Publish\n",
        ),
    ),
    MessageSpec(
        "Noah Williams",
        "noah.williams@example.com",
        "Re: Design systems sync",
        0,
        9,
        18,
        "Tuesday works well. I will bring the component inventory and the "
        "latest accessibility notes.\n\nSee you then,\nNoah",
    ),
    MessageSpec(
        "Atlas Research",
        "digest@atlas.example",
        "Five calmer patterns for productive teams",
        1,
        16,
        5,
        "This week: quieter notification patterns, clearer hierarchy, and "
        "ways to keep complex tools approachable.",
        read=True,
    ),
    MessageSpec(
        "Olivia Martin",
        "olivia.martin@example.com",
        "Photos from the studio workshop ✨",
        1,
        13,
        27,
        "The workshop photos turned out beautifully. I selected twelve that "
        "should work especially well for the case study.",
        read=True,
    ),
    MessageSpec(
        "Elias Novak",
        "elias.novak@example.com",
        "Prototype feedback and next steps",
        2,
        11,
        54,
        "The new navigation feels much more direct. My only remaining note is "
        "to preserve the visible focus ring in the compact layout.",
    ),
    MessageSpec(
        "Northstar Travel",
        "hello@northstar.example",
        "Your Copenhagen itinerary",
        3,
        17,
        12,
        "Your itinerary is ready. Check-in opens Friday at 08:35. The booking "
        "uses fictional locations and contains no real reservation data.",
        read=True,
        flagged=True,
    ),
    MessageSpec(
        "Priya Kapoor",
        "priya.kapoor@example.com",
        "Copy edits for the July notes",
        4,
        14,
        33,
        "I tightened the introduction and made the terminology consistent. "
        "The revised draft is ready whenever you are.",
        read=True,
    ),
    MessageSpec(
        "Studio Calendar",
        "calendar@studio.example",
        "Reminder: weekly planning in 30 minutes",
        5,
        8,
        30,
        "Weekly planning starts at 09:00 in the project room.",
        read=True,
    ),
    MessageSpec(
        "Avery Brooks",
        "avery.brooks@example.com",
        "A small idea for the welcome screen",
        6,
        15,
        48,
        "What if the welcome screen led with one clear action and moved the "
        "secondary choices into a quieter group below it?",
        read=True,
    ),
    MessageSpec(
        "Community Notes",
        "notes@community.example",
        "Issue 42: thoughtful tools, better defaults",
        8,
        12,
        2,
        "A monthly collection of small interface details and the reasoning "
        "behind them.",
        read=True,
    ),
)

SENT_MESSAGES = (
    MessageSpec(
        "Liquid Studio",
        "hello@liquidstudio.example",
        "Re: Final review: Liquid launch assets",
        0,
        11,
        6,
        "Thanks, Maya. The dark appearance export is looking excellent. I left "
        "two small comments and marked the rest approved.",
        read=True,
    ),
    MessageSpec(
        "Liquid Studio",
        "hello@liquidstudio.example",
        "Workshop agenda",
        2,
        16,
        20,
        "Here is the agenda for tomorrow: introductions, component review, "
        "prototype walkthrough, and next steps.",
        read=True,
    ),
)

DRAFT_MESSAGES = (
    MessageSpec(
        "Liquid Studio",
        "hello@liquidstudio.example",
        "Ideas for a quieter inbox",
        0,
        8,
        15,
        "A few early notes on hierarchy, color, and reducing visual noise.",
    ),
)

ARCHIVE_MESSAGES = (
    MessageSpec(
        "Sofia Rossi",
        "sofia.rossi@example.com",
        "Research summary: navigation patterns",
        15,
        9,
        40,
        "The research summary covers sidebar organization, compact controls, "
        "and spatial consistency across settings surfaces.",
        read=True,
    ),
    MessageSpec(
        "Liquid Studio Billing",
        "billing@liquidstudio.example",
        "Receipt for your fictional workspace",
        30,
        10,
        10,
        "This is a synthetic receipt generated exclusively for screenshots.",
        read=True,
    ),
)

PROJECT_MESSAGES = (
    MessageSpec(
        "Project Current",
        "updates@current.example",
        "Milestone 3 is ready for review",
        3,
        10,
        0,
        "Milestone 3 includes the refined toolbar, address book, and calendar "
        "states.",
        read=True,
    ),
)

CONTACTS = (
    ("Maya", "Chen", "Maya Chen", "maya.chen@example.com", "Liquid Studio", "+1 555 0101"),
    ("Noah", "Williams", "Noah Williams", "noah.williams@example.com", "Northstar", "+1 555 0102"),
    ("Olivia", "Martin", "Olivia Martin", "olivia.martin@example.com", "Field Notes", "+1 555 0103"),
    ("Elias", "Novak", "Elias Novak", "elias.novak@example.com", "Current", "+1 555 0104"),
    ("Priya", "Kapoor", "Priya Kapoor", "priya.kapoor@example.com", "Aperture", "+1 555 0105"),
    ("Avery", "Brooks", "Avery Brooks", "avery.brooks@example.com", "Common Thread", "+1 555 0106"),
    ("Sofia", "Rossi", "Sofia Rossi", "sofia.rossi@example.com", "Forma", "+1 555 0107"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("prepare", "launch", "capture", "clean"),
        nargs="?",
        default="prepare",
    )
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--output", type=Path, default=DEFAULT_SCREENSHOTS)
    parser.add_argument("--thunderbird", type=Path, default=DEFAULT_THUNDERBIRD)
    parser.add_argument(
        "--base-date",
        type=date.fromisoformat,
        default=date.today(),
        help="date represented as today in generated mail and calendar data",
    )
    parser.add_argument(
        "--surface",
        action="append",
        choices=SURFACES,
        dest="surfaces",
        help="surface to capture; repeat to select several (default: all)",
    )
    parser.add_argument(
        "--appearance",
        choices=("system", "light", "dark", "both"),
        default="system",
        help="macOS appearance used while capturing",
    )
    parser.add_argument(
        "--settle-seconds",
        type=float,
        default=6.0,
        help="additional UI settling time before each screenshot",
    )
    parser.add_argument(
        "--keep-open",
        action="store_true",
        help="leave Thunderbird open after a single-surface capture",
    )
    parser.add_argument(
        "--reuse-profile",
        action="store_true",
        help="capture the existing generated profile instead of rebuilding it",
    )
    parser.add_argument(
        "--publish-readme",
        action="store_true",
        help="publish synthetic mail-light and mail-dark captures to docs/screenshots",
    )
    return parser.parse_args()


def js_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def ensure_safe_generated_path(path: Path) -> Path:
    path = path.expanduser().resolve()
    safe_root = DEMO_ROOT.resolve()
    if path == safe_root or not path.is_relative_to(safe_root):
        raise SystemExit(
            f"Refusing to reset {path}: generated profiles must be below {safe_root}"
        )
    return path


def reset_generated_directory(path: Path) -> None:
    path = ensure_safe_generated_path(path)
    marker = path / PROFILE_MARKER
    if path.exists():
        if not marker.is_file():
            raise SystemExit(
                f"Refusing to replace unmarked directory {path}; remove or move it manually"
            )
        shutil.rmtree(path)
    path.mkdir(parents=True)
    marker.write_text("Generated by scripts/demo.py. Safe to replace.\n", encoding="utf-8")


def install_theme(profile: Path) -> None:
    chrome = profile / "chrome"
    chrome.mkdir()
    for name in (
        "liquidbird.css",
        "liquidbird-content.css",
        "custom.css",
        "userChrome.css",
        "userContent.css",
    ):
        shutil.copy2(ROOT / name, chrome / name)
    shutil.copytree(ROOT / "Icons", chrome / "Icons")


def render_message(spec: MessageSpec, message_index: int, base_date: date, recipient: str) -> bytes:
    sent_at = datetime.combine(
        base_date - timedelta(days=spec.days_ago),
        datetime_time(spec.hour, spec.minute),
        tzinfo=timezone.utc,
    )
    message = EmailMessage()
    message["From"] = f"{spec.sender_name} <{spec.sender_email}>"
    message["To"] = recipient
    if message_index == 1:
        message["Cc"] = "Noah Williams <noah.williams@example.com>"
    message["Subject"] = spec.subject
    message["Date"] = sent_at.strftime("%a, %d %b %Y %H:%M:%S %z")
    message["Message-ID"] = f"<liquidbird-demo-{message_index}@mail.example>"
    status = (0x0001 if spec.read else 0) | (0x0004 if spec.flagged else 0)
    message["X-Mozilla-Status"] = f"{status:04X}"
    message["X-Mozilla-Status2"] = "00000000"
    message["X-Account-Key"] = "account1"
    message.set_content(spec.body)
    message.add_alternative(
        "<html><body style=\"font: 16px -apple-system, sans-serif; line-height: 1.5\">"
        f"<p>{html.escape(spec.body).replace(chr(10), '</p><p>')}</p>"
        "<p style=\"color: #6e6e73\">LiquidBird synthetic demo message</p>"
        "</body></html>",
        subtype="html",
    )
    if spec.attachment:
        filename, mime_type, payload = spec.attachment
        maintype, subtype = mime_type.split("/", 1)
        message.add_attachment(payload, maintype=maintype, subtype=subtype, filename=filename)

    output = BytesIO()
    BytesGenerator(output, policy=SMTP, mangle_from_=True).flatten(message)
    separator = f"From - {sent_at.strftime('%a %b %d %H:%M:%S %Y')}\r\n".encode()
    return separator + output.getvalue() + b"\r\n"


def write_mbox(path: Path, specs: tuple[MessageSpec, ...], base_date: date, start_index: int) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    recipient = "Liquid Studio <hello@liquidstudio.example>"
    with path.open("wb") as mailbox:
        for offset, spec in enumerate(specs):
            mailbox.write(render_message(spec, start_index + offset, base_date, recipient))
    return start_index + len(specs)


def create_mail_store(profile: Path, base_date: date) -> None:
    account = profile / "Mail" / "studio.example.invalid"
    account.mkdir(parents=True)
    message_index = 1
    message_index = write_mbox(account / "Inbox", INBOX_MESSAGES, base_date, message_index)
    message_index = write_mbox(account / "Sent", SENT_MESSAGES, base_date, message_index)
    message_index = write_mbox(account / "Drafts", DRAFT_MESSAGES, base_date, message_index)
    message_index = write_mbox(account / "Archives", ARCHIVE_MESSAGES, base_date, message_index)
    (account / "Trash").touch()
    (account / "Junk").touch()
    (account / "Projects").touch()
    write_mbox(
        account / "Projects.sbd" / "Liquid Launch",
        PROJECT_MESSAGES,
        base_date,
        message_index,
    )
    local = profile / "Mail" / "Local Folders"
    local.mkdir(parents=True)
    (local / "Trash").touch()
    (local / "Unsent Messages").touch()
    standalone = render_message(
        INBOX_MESSAGES[0], 1, base_date, "Liquid Studio <hello@liquidstudio.example>"
    ).split(b"\r\n", 1)[1]
    (profile / "synthetic-message.eml").write_bytes(standalone)


def create_address_book(profile: Path) -> None:
    database = sqlite3.connect(profile / "abook.sqlite")
    try:
        database.executescript(
            """
            PRAGMA journal_mode=DELETE;
            PRAGMA user_version=4;
            CREATE TABLE properties (card TEXT, name TEXT, value TEXT);
            CREATE TABLE lists (uid TEXT PRIMARY KEY, name TEXT, nickName TEXT, description TEXT);
            CREATE TABLE list_cards (list TEXT, card TEXT, PRIMARY KEY(list, card));
            CREATE INDEX properties_card ON properties(card);
            CREATE INDEX properties_name ON properties(name);
            """
        )
        for index, (first, last, display, email, organization, phone) in enumerate(CONTACTS, start=1):
            uid = f"liquidbird-contact-{index:02d}"
            vcard = (
                "BEGIN:VCARD\r\n"
                "VERSION:4.0\r\n"
                f"UID:{uid}\r\n"
                f"N:{last};{first};;;\r\n"
                f"FN:{display}\r\n"
                f"EMAIL;PREF=1:{email}\r\n"
                f"ORG:{organization}\r\n"
                f"TEL;TYPE=work:{phone}\r\n"
                "END:VCARD\r\n"
            )
            database.executemany(
                "INSERT INTO properties(card, name, value) VALUES (?, ?, ?)",
                (
                    (uid, "_vCard", vcard),
                    (uid, "PopularityIndex", "0"),
                    (uid, "LastModifiedDate", "0"),
                ),
            )
        database.commit()
    finally:
        database.close()


def format_ics_datetime(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def create_calendar(profile: Path, base_date: date) -> Path:
    start = datetime.combine(base_date + timedelta(days=1), datetime_time(9), timezone.utc)
    all_day = base_date + timedelta(days=1)
    events = (
        ("weekly-planning", "Weekly planning", start, 45, "Project Room"),
        ("design-review", "Design review", start + timedelta(hours=3), 60, "Studio"),
        ("prototype-walkthrough", "Prototype walkthrough", start + timedelta(days=1, hours=5), 45, "Focus Room"),
        ("research-interviews", "Research interviews", start + timedelta(days=2, hours=1), 90, "Online"),
        ("launch-retrospective", "Launch retrospective", start + timedelta(days=4, hours=6), 60, "Project Room"),
    )
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//LiquidBird//Synthetic Screenshot Calendar//EN",
        "CALSCALE:GREGORIAN",
        "X-WR-CALNAME:Liquid Studio",
        "BEGIN:VEVENT",
        "UID:liquidbird-launch-day@calendar.example",
        f"DTSTAMP:{format_ics_datetime(start)}",
        f"DTSTART;VALUE=DATE:{all_day.strftime('%Y%m%d')}",
        f"DTEND;VALUE=DATE:{(all_day + timedelta(days=1)).strftime('%Y%m%d')}",
        "SUMMARY:LiquidBird launch day",
        "DESCRIPTION:Synthetic LiquidBird screenshot event.",
        "END:VEVENT",
    ]
    for uid, summary, event_start, minutes, location in events:
        lines.extend(
            (
                "BEGIN:VEVENT",
                f"UID:{uid}@calendar.example",
                f"DTSTAMP:{format_ics_datetime(start)}",
                f"DTSTART:{format_ics_datetime(event_start)}",
                f"DTEND:{format_ics_datetime(event_start + timedelta(minutes=minutes))}",
                f"SUMMARY:{summary}",
                f"LOCATION:{location}",
                "DESCRIPTION:Synthetic LiquidBird screenshot event.",
                "END:VEVENT",
            )
        )
    lines.append("END:VCALENDAR")
    calendar = profile / "liquidbird-demo.ics"
    calendar.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
    return calendar


def create_session(profile: Path) -> None:
    folder_uri = "mailbox://demo@studio.example.invalid/Inbox"
    state = {
        "rev": 0,
        "windows": [
            {
                "type": "3pane",
                "tabs": {
                    "rev": 0,
                    "selectedIndex": 0,
                    "tabs": [
                        {
                            "mode": "mail3PaneTab",
                            "state": {
                                "firstTab": True,
                                "folderPaneVisible": True,
                                "folderURI": folder_uri,
                                "messagePaneVisible": True,
                            },
                            "ext": {},
                        }
                    ],
                },
            }
        ],
    }
    (profile / "session.json").write_text(
        json.dumps(state, indent=2) + "\n", encoding="utf-8"
    )
    folder_tree = {
        "open": {
            "all": [
                "mailbox://demo@studio.example.invalid",
                "mailbox://demo@studio.example.invalid/Projects",
            ]
        }
    }
    (profile / "folderTree.json").write_text(
        json.dumps(folder_tree, indent=2) + "\n", encoding="utf-8"
    )

    window_properties = {
        "screenX": str(WINDOW_POSITION[0]),
        "screenY": str(WINDOW_POSITION[1]),
        "width": str(WINDOW_SIZE[0]),
        "height": str(WINDOW_SIZE[1]),
        "sizemode": "normal",
    }
    xul_store = {
        "chrome://messenger/content/messenger.xhtml": {
            "messengerWindow": window_properties
        },
        "chrome://messenger/content/messengercompose/messengercompose.xhtml": {
            "msgcomposeWindow": window_properties
        },
        "chrome://messenger/content/messageWindow.xhtml": {
            "messengerWindow": window_properties
        },
    }
    (profile / "xulstore.json").write_text(
        json.dumps(xul_store, indent=2) + "\n", encoding="utf-8"
    )


def create_preferences(profile: Path, calendar: Path) -> None:
    calendar_id = "liquidbird-demo-calendar"
    preferences: dict[str, str | int | bool] = {
        "toolkit.legacyUserProfileCustomizations.stylesheets": True,
        "offline.startup_state": 3,
        "offline.autoDetect": False,
        "network.online": False,
        "mail.shell.checkDefaultClient": False,
        "mail.rights.version": 1,
        "mail.spotlight.firstRunDone": True,
        "mailnews.start_page.enabled": False,
        # Fresh profiles otherwise compare their empty last-seen version with
        # Thunderbird's machine-level update history. If that update requested
        # a What's New page, Thunderbird opens it in the system browser. Keep a
        # stable future milestone in this disposable, update-disabled profile
        # so demo launches never trigger an external release-notes page.
        "mailnews.start_page_override.mstone": "999999.0",
        "mailnews.start_page.override_url": "",
        "mailnews.database.global.indexer.enabled": False,
        "mail.biff.show_alert": False,
        "mail.biff.play_sound": False,
        "datareporting.healthreport.uploadEnabled": False,
        "datareporting.policy.dataSubmissionEnabled": False,
        "datareporting.policy.dataSubmissionPolicyBypassNotification": True,
        "toolkit.telemetry.enabled": False,
        "toolkit.telemetry.unified": False,
        "app.update.auto": False,
        "app.update.enabled": False,
        "extensions.update.enabled": False,
        "extensions.getAddons.showPane": False,
        "browser.search.update": False,
        "mail.accountmanager.accounts": "account1,account2",
        "mail.accountmanager.defaultaccount": "account1",
        "mail.accountmanager.localfoldersserver": "server2",
        "mail.account.account1.server": "server1",
        "mail.account.account1.identities": "id1",
        "mail.account.account2.server": "server2",
        "mail.identity.id1.fullName": "Liquid Studio",
        "mail.identity.id1.useremail": "hello@liquidstudio.example",
        "mail.identity.id1.reply_to": "",
        "mail.identity.id1.smtpServer": "smtp1",
        "mail.identity.id1.valid": True,
        "mail.server.server1.type": "pop3",
        "mail.server.server1.hostname": "studio.example.invalid",
        "mail.server.server1.realhostname": "studio.example.invalid",
        "mail.server.server1.userName": "demo",
        "mail.server.server1.realuserName": "demo",
        "mail.server.server1.name": "hello@liquidstudio.example",
        "mail.server.server1.directory-rel": "[ProfD]Mail/studio.example.invalid",
        "mail.server.server1.check_new_mail": False,
        "mail.server.server1.login_at_startup": False,
        "mail.server.server1.download_on_biff": False,
        "mail.server.server1.socketType": 0,
        "mail.server.server1.authMethod": 3,
        "mail.server.server1.port": 110,
        "mail.server.server1.valid": True,
        "mail.server.server2.type": "none",
        "mail.server.server2.hostname": "Local Folders",
        "mail.server.server2.userName": "nobody",
        "mail.server.server2.name": "Local Folders",
        "mail.server.server2.directory-rel": "[ProfD]Mail/Local Folders",
        "mail.server.server2.valid": True,
        "mail.smtp.defaultserver": "smtp1",
        "mail.smtpservers": "smtp1",
        "mail.smtpserver.smtp1.hostname": "smtp.example.invalid",
        "mail.smtpserver.smtp1.username": "demo",
        "mail.smtpserver.smtp1.port": 587,
        "mail.smtpserver.smtp1.authMethod": 3,
        "mail.smtpserver.smtp1.try_ssl": 2,
        "ldap_2.servers.pab.description": "Studio Contacts",
        "ldap_2.servers.pab.dirType": 101,
        "ldap_2.servers.pab.filename": "abook.sqlite",
        "ldap_2.servers.pab.position": 1,
        "ldap_2.servers.pab.uid": "liquidbird-demo-address-book",
        # Thunderbird enables the macOS Contacts provider through a default
        # preference. Disable it so even selecting every address-book row can
        # never reveal system contacts during a demo.
        "ldap_2.servers.osx.dirType": -1,
        f"calendar.registry.{calendar_id}.type": "ics",
        f"calendar.registry.{calendar_id}.uri": calendar.as_uri(),
        f"calendar.registry.{calendar_id}.name": "Liquid Studio",
        f"calendar.registry.{calendar_id}.color": "#0A84FF",
        f"calendar.registry.{calendar_id}.calendar-main-in-composite": True,
        f"calendar.registry.{calendar_id}.calendar-main-default": True,
        "calendar.list.sortOrder": calendar_id,
        "calendar.week.start": 1,
        "calendar.view-minimonth.showWeekNumber": False,
        "calendar.alarms.show": False,
    }
    lines = ["// Generated by scripts/demo.py. Contains synthetic settings only."]
    for key, value in sorted(preferences.items()):
        if isinstance(value, bool):
            serialized = "true" if value else "false"
        elif isinstance(value, int):
            serialized = str(value)
        else:
            serialized = js_string(value)
        lines.append(f"user_pref({js_string(key)}, {serialized});")
    (profile / "user.js").write_text("\n".join(lines) + "\n", encoding="utf-8")


def prepare(profile: Path, base_date: date) -> Path:
    profile = ensure_safe_generated_path(profile)
    reset_generated_directory(profile)
    install_theme(profile)
    create_mail_store(profile, base_date)
    create_address_book(profile)
    calendar = create_calendar(profile, base_date)
    create_preferences(profile, calendar)
    create_session(profile)
    summary = {
        "synthetic": True,
        "offline": True,
        "baseDate": base_date.isoformat(),
        "mailboxes": {
            "Inbox": len(INBOX_MESSAGES),
            "Sent": len(SENT_MESSAGES),
            "Drafts": len(DRAFT_MESSAGES),
            "Archives": len(ARCHIVE_MESSAGES),
            "Projects/Liquid Launch": len(PROJECT_MESSAGES),
        },
        "contacts": len(CONTACTS),
        "calendarEvents": 6,
        "systemContactsDisabled": True,
    }
    (profile / "DEMO.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Prepared synthetic offline profile: {profile}")
    print(
        f"Generated {sum(summary['mailboxes'].values())} messages, "
        f"{summary['contacts']} contacts, and {summary['calendarEvents']} events."
    )
    return profile


def thunderbird_command(
    executable: Path,
    profile: Path,
    surface: str,
    *,
    marionette: bool = False,
) -> list[str]:
    command = [
        str(executable),
        "--no-remote",
        "--profile",
        str(profile),
        "--purgecaches",
    ]
    if marionette:
        command.extend(("--marionette", "--remote-allow-system-access"))
    direct_flags = {
        "mail": "-mail",
        "addressbook": "-addressbook",
        "calendar": "-calendar",
        "settings": "-options",
    }
    if surface in direct_flags:
        command.append(direct_flags[surface])
    elif surface == "message":
        command.extend(("-file", str(profile / "synthetic-message.eml")))
    elif surface == "compose":
        compose_fields = (
            "to='Maya Chen <maya.chen@example.com>',"
            "subject='A calmer inbox',"
            "body='Hi Maya,\n\nHere are the refined concepts for the next review.'"
        )
        command.extend(
            (
                "-compose",
                compose_fields,
            )
        )
    else:
        command.append("-mail")
    return command


def run_osascript(source: str, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["osascript", "-", *arguments],
        input=source,
        text=True,
        capture_output=True,
        check=check,
    )


def reserve_loopback_port() -> int:
    # Marionette's long-standing default is 2828. Stay in a nearby explicit
    # range: Gecko can reject a transient high port even when the OS allowed a
    # short-lived probe bind there during startup.
    for port in range(2828, 2928):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            try:
                listener.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError("No free loopback port is available for Marionette")


class MarionetteClient:
    """Minimal client for Thunderbird's length-prefixed Marionette protocol."""

    def __init__(self, port: int, timeout: float = 30.0) -> None:
        deadline = time.monotonic() + timeout
        while True:
            try:
                self.socket = socket.create_connection(
                    ("127.0.0.1", port), timeout=min(2.0, timeout)
                )
                break
            except OSError as error:
                if time.monotonic() >= deadline:
                    raise RuntimeError(
                        f"Timed out connecting to Thunderbird Marionette on port {port}"
                    ) from error
                time.sleep(0.25)
        self.socket.settimeout(timeout)
        self.buffer = bytearray()
        self.command_id = 0
        greeting = self.receive()
        if not isinstance(greeting, dict) or greeting.get("marionetteProtocol") != 3:
            raise RuntimeError(f"Unexpected Marionette greeting: {greeting!r}")

    def close(self) -> None:
        self.socket.close()

    def receive(self) -> object:
        while b":" not in self.buffer:
            chunk = self.socket.recv(4096)
            if not chunk:
                raise RuntimeError("Marionette closed the connection")
            self.buffer.extend(chunk)
        raw_length, remainder = self.buffer.split(b":", 1)
        try:
            length = int(raw_length)
        except ValueError as error:
            raise RuntimeError(f"Invalid Marionette packet header: {raw_length!r}") from error
        self.buffer = bytearray(remainder)
        while len(self.buffer) < length:
            chunk = self.socket.recv(max(4096, length - len(self.buffer)))
            if not chunk:
                raise RuntimeError("Marionette closed an incomplete packet")
            self.buffer.extend(chunk)
        payload = bytes(self.buffer[:length])
        del self.buffer[:length]
        return json.loads(payload)

    def command(self, name: str, parameters: dict[str, object]) -> object:
        self.command_id += 1
        payload = json.dumps(
            [0, self.command_id, name, parameters], separators=(",", ":")
        ).encode("ascii")
        self.socket.sendall(str(len(payload)).encode("ascii") + b":" + payload)
        while True:
            response = self.receive()
            if (
                isinstance(response, list)
                and len(response) == 4
                and response[0] == 1
                and response[1] == self.command_id
            ):
                if response[2] is not None:
                    raise RuntimeError(f"Marionette {name} failed: {response[2]!r}")
                result = response[3]
                return result.get("value") if isinstance(result, dict) else result


def prepare_capture_window(
    port: int,
    *,
    select_mail_message: bool,
    timeout: float = 30.0,
) -> None:
    client = MarionetteClient(port, timeout)
    try:
        client.command(
            "WebDriver:NewSession",
            {"capabilities": {"alwaysMatch": {"acceptInsecureCerts": True}}},
        )
        client.command("Marionette:SetContext", {"value": "chrome"})
        script = """
const [screenX, screenY, width, height, selectMailMessage] = arguments;
const captureWindow = Services.focus.activeWindow || Services.wm.getMostRecentWindow(null);
if (!captureWindow) {
  return 0;
}
captureWindow.moveTo(screenX, screenY);
captureWindow.resizeTo(width, height);
if (!selectMailMessage) {
  return 1;
}
const mailWindow = Services.wm.getMostRecentWindow("mail:3pane");
if (!mailWindow) {
  return 0;
}
const tabmail = mailWindow.document.getElementById("tabmail");
const threePane = tabmail?.currentTabInfo?.chromeBrowser?.contentWindow;
if (!threePane?.gDBView || threePane.gDBView.rowCount < 1) {
  return 0;
}
threePane.threadTree.selectedIndex = -1;
threePane.threadTree.selectedIndex = 0;
return threePane.gDBView.rowCount;
"""
        deadline = time.monotonic() + timeout
        while True:
            count = client.command(
                "WebDriver:ExecuteScript",
                {
                    "script": script,
                    "args": [
                        WINDOW_POSITION[0],
                        WINDOW_POSITION[1],
                        WINDOW_SIZE[0],
                        WINDOW_SIZE[1],
                        select_mail_message,
                    ],
                    "sandbox": "system",
                    "newSandbox": True,
                },
            )
            if isinstance(count, int) and count > 0:
                return
            if time.monotonic() >= deadline:
                if select_mail_message:
                    raise RuntimeError("Inbox loaded without any selectable messages")
                raise RuntimeError("Thunderbird opened without a capturable window")
            time.sleep(0.25)
    finally:
        client.close()


def wait_for_window_id(pid: int, timeout: int = 35) -> int:
    swift_source = """
import CoreGraphics
import Foundation

guard let rawPID = ProcessInfo.processInfo.environment["LIQUIDBIRD_WINDOW_PID"],
      let targetPID = Int32(rawPID) else {
  exit(2)
}
let deadline = Date().addingTimeInterval(TIMEOUT)
repeat {
  let options = CGWindowListOption(arrayLiteral: .optionOnScreenOnly, .excludeDesktopElements)
  let windows = CGWindowListCopyWindowInfo(options, kCGNullWindowID) as! [[String: Any]]
  for window in windows {
    let ownerPID = window[kCGWindowOwnerPID as String] as? Int32
    let layer = window[kCGWindowLayer as String] as? Int
    if ownerPID == targetPID && layer == 0,
       let windowID = window[kCGWindowNumber as String] as? Int {
      print(windowID)
      exit(0)
    }
  }
  Thread.sleep(forTimeInterval: 0.25)
} while Date() < deadline
exit(3)
""".replace("TIMEOUT", str(timeout))
    try:
        swift_environment = dict(os.environ)
        swift_environment["LIQUIDBIRD_WINDOW_PID"] = str(pid)
        result = subprocess.run(
            ["swift", "-e", swift_source],
            text=True,
            capture_output=True,
            check=True,
            env=swift_environment,
        )
        return int(result.stdout.strip().splitlines()[-1])
    except subprocess.CalledProcessError as error:
        detail = error.stderr.strip() or error.stdout.strip()
        raise SystemExit(
            f"Timed out waiting for the isolated Thunderbird window (PID {pid}).\n{detail}"
        ) from error


def navigate_surface(pid: int, surface: str) -> None:
    if surface not in {"addons", "account-settings"}:
        return
    action = (
        'keystroke "a" using {command down, shift down}'
        if surface == "addons"
        else 'click menu item "Account Settings" of menu "Tools" of menu bar 1'
    )
    script = f"""
on run argv
  set targetPID to item 1 of argv as integer
  tell application "System Events"
    set matches to every application process whose unix id is targetPID
    if (count of matches) is 0 then error "Thunderbird process disappeared"
    tell item 1 of matches
      set frontmost to true
      {action}
    end tell
  end tell
end run
"""
    try:
        run_osascript(script, str(pid))
    except subprocess.CalledProcessError as error:
        detail = error.stderr.strip() or error.stdout.strip()
        raise SystemExit(
            f"Capturing {surface} requires Accessibility permission for the "
            "terminal or Codex process running scripts/demo.py.\n"
            f"{detail}"
        ) from error


def screenshot_window(window_id: int, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "screencapture",
            "-x",
            "-l",
            str(window_id),
            str(destination),
        ],
        check=True,
    )
    if not destination.is_file() or destination.stat().st_size == 0:
        raise SystemExit(
            "Screenshot capture produced no image. Grant Screen Recording "
            "permission to your terminal/Codex and retry."
        )


def terminate_demo(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    process.send_signal(signal.SIGTERM)
    try:
        process.wait(timeout=12)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def capture_surface(
    executable: Path,
    profile: Path,
    output: Path,
    surface: str,
    label: str,
    settle_seconds: float,
    keep_open: bool,
) -> None:
    marionette_port = reserve_loopback_port()
    command = thunderbird_command(
        executable,
        profile,
        surface,
        marionette=marionette_port is not None,
    )
    process_environment = dict(os.environ)
    if marionette_port is not None:
        process_environment["MOZ_MARIONETTE"] = "1"
        process_environment["MOZ_MARIONETTE_PREF_STATE_ACROSS_RESTARTS"] = (
            json.dumps({"port": marionette_port})
        )
    process = subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=process_environment,
    )
    leave_open = False
    try:
        window_id = wait_for_window_id(process.pid)
        time.sleep(max(0.0, settle_seconds))
        # Some command-line handlers create the main window first and their
        # requested tab or compose window shortly afterwards. Re-read the
        # frontmost window after settling instead of retaining the startup ID.
        window_id = wait_for_window_id(process.pid)
        prepare_capture_window(
            marionette_port,
            select_mail_message=surface == "mail",
        )
        time.sleep(2)
        navigate_surface(process.pid, surface)
        if surface in {"addons", "account-settings"}:
            time.sleep(max(3.0, settle_seconds))
            window_id = wait_for_window_id(process.pid)
        filename = f"{surface}-{label}.png" if label != "system" else f"{surface}.png"
        destination = output / filename
        screenshot_window(window_id, destination)
        print(f"Captured {surface}: {destination}")
        if keep_open:
            leave_open = True
            print(f"Thunderbird demo remains open (PID {process.pid}).")
            return
    finally:
        if not leave_open:
            terminate_demo(process)


def get_system_dark_mode() -> bool:
    result = run_osascript(
        'tell application "System Events" to tell appearance preferences to get dark mode'
    )
    return result.stdout.strip().lower() == "true"


def set_system_dark_mode(enabled: bool) -> None:
    value = "true" if enabled else "false"
    run_osascript(
        f'tell application "System Events" to tell appearance preferences to set dark mode to {value}'
    )
    time.sleep(2)


def publish_readme_screenshots(output: Path) -> None:
    README_SCREENSHOTS.mkdir(parents=True, exist_ok=True)
    sources = {
        output / "mail-light.png": README_SCREENSHOTS / "liquidbird-mail-light.png",
        output / "mail-dark.png": README_SCREENSHOTS / "liquidbird-mail-dark.png",
    }
    missing = [str(path) for path in sources if not path.is_file()]
    if missing:
        raise SystemExit(
            "README publication requires both light and dark mail captures; missing: "
            + ", ".join(missing)
        )
    for source, destination in sources.items():
        shutil.copy2(source, destination)
        print(f"Published README screenshot: {destination}")


def capture_all(options: argparse.Namespace, profile: Path) -> None:
    if sys.platform != "darwin":
        raise SystemExit("Automated screenshot capture currently requires macOS.")
    executable = options.thunderbird.expanduser().resolve()
    if not executable.is_file():
        raise SystemExit(f"Thunderbird executable not found: {executable}")
    output = ensure_safe_generated_path(options.output)
    surfaces = options.surfaces or list(SURFACES)
    if options.keep_open and len(surfaces) != 1:
        raise SystemExit("--keep-open requires exactly one --surface")
    if options.publish_readme and (
        options.appearance != "both" or "mail" not in surfaces
    ):
        raise SystemExit(
            "--publish-readme requires --appearance both and the mail surface"
        )

    appearances: tuple[tuple[str, bool | None], ...]
    if options.appearance == "both":
        appearances = (("light", False), ("dark", True))
    elif options.appearance == "light":
        appearances = (("light", False),)
    elif options.appearance == "dark":
        appearances = (("dark", True),)
    else:
        appearances = (("system", None),)

    original_dark_mode = get_system_dark_mode() if any(value is not None for _, value in appearances) else None
    try:
        for label, dark_mode in appearances:
            if dark_mode is not None:
                set_system_dark_mode(dark_mode)
            for surface in surfaces:
                capture_surface(
                    executable,
                    profile,
                    output,
                    surface,
                    label,
                    options.settle_seconds,
                    options.keep_open,
                )
        if options.publish_readme:
            publish_readme_screenshots(output)
    finally:
        if original_dark_mode is not None:
            set_system_dark_mode(original_dark_mode)


def launch(options: argparse.Namespace, profile: Path) -> None:
    executable = options.thunderbird.expanduser().resolve()
    if not executable.is_file():
        raise SystemExit(f"Thunderbird executable not found: {executable}")
    surface = (options.surfaces or ["mail"])[0]
    process = subprocess.Popen(thunderbird_command(executable, profile, surface))
    print(f"Launched isolated LiquidBird demo (PID {process.pid}, profile {profile}).")


def clean(profile: Path) -> None:
    profile = ensure_safe_generated_path(profile)
    marker = profile / PROFILE_MARKER
    if not profile.exists():
        print(f"No generated profile to remove: {profile}")
        return
    if not marker.is_file():
        raise SystemExit(f"Refusing to remove unmarked directory: {profile}")
    shutil.rmtree(profile)
    print(f"Removed generated demo profile: {profile}")


def main() -> int:
    options = parse_args()
    profile = options.profile.expanduser().resolve()
    if options.command == "clean":
        clean(profile)
        return 0
    if options.command == "prepare":
        prepare(profile, options.base_date)
        return 0
    if options.command == "capture" and not options.reuse_profile:
        prepare(profile, options.base_date)
    elif not (profile / PROFILE_MARKER).is_file():
        prepare(profile, options.base_date)
    if options.command == "launch":
        launch(options, profile)
    elif options.command == "capture":
        capture_all(options, profile)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
