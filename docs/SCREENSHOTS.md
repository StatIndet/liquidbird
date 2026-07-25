# Synthetic screenshot workflow

LiquidBird includes a deterministic, isolated Thunderbird fixture for taking
screenshots without opening a personal profile. It creates fictional mail,
contacts, and calendar events, installs the current working-tree theme, and
forces Thunderbird to start offline.

The generated profile and screenshots live below `.demo/`, which is ignored by
Git. The automation never reads Thunderbird's profile registry or a normal
Thunderbird profile.
The built-in macOS Contacts provider is explicitly disabled as well, so the
Address Book surface cannot reveal contacts from the computer.

## Requirements

- macOS
- Thunderbird Beta in `/Applications/Thunderbird Beta.app`
- Python 3.10 or newer
- Xcode Command Line Tools (the bundled Swift compiler is used to identify the
  isolated window without inspecting other applications)
- Screen Recording permission for the terminal or Codex process running the
  script

Account Settings and Add-ons additionally require Accessibility permission
because Thunderbird does not expose command-line flags for those two tabs.

Use `--thunderbird` if Thunderbird is installed elsewhere.

## Prepare and inspect the demo

Generate the profile:

```sh
python3 scripts/demo.py prepare
```

Open its synthetic inbox in a separate Thunderbird process:

```sh
python3 scripts/demo.py launch
```

The launcher always supplies `--no-remote`, `--profile`, and `--purgecaches`.
The profile uses only reserved `.example` and `.invalid` addresses, disables
new-mail checks and update services, and starts in Thunderbird's always-offline
mode. It cannot authenticate to or display a personal account.

Re-running `prepare` replaces only a directory carrying the generator's marker
file. It refuses to replace arbitrary or unmarked directories.

## Capture screenshots

Capture every supported surface in the Mac's current appearance:

```sh
python3 scripts/demo.py capture
```

The generated PNG files are placed in `.demo/screenshots/`. The complete set
contains Mail, a standalone synthetic Message, Address Book, Calendar,
Settings, Account Settings, Add-ons, and Compose.

Each capture run rebuilds the generated profile so it always contains the
current working-tree CSS and fresh fixture data. Pass `--reuse-profile` only
when intentionally photographing manual changes made inside the demo profile.

Capture a smaller set:

```sh
python3 scripts/demo.py capture \
  --surface mail \
  --surface addressbook
```

Capture both light and dark appearances:

```sh
python3 scripts/demo.py capture --appearance both
```

Regenerate the tracked light and dark screenshots displayed in the README:

```sh
python3 scripts/demo.py capture \
  --surface mail \
  --appearance both \
  --publish-readme
```

Publication copies only those two synthetic mail captures to
`docs/screenshots/liquidbird-mail-light.png` and
`docs/screenshots/liquidbird-mail-dark.png`. Other generated screenshots remain
ignored below `.demo/screenshots/`.

For `light`, `dark`, or `both`, the script changes the system appearance only
for the duration of the run and restores the original setting in a `finally`
block. Avoid changing the appearance manually while a capture is running.

To inspect a single prepared surface after capture:

```sh
python3 scripts/demo.py capture --surface mail --keep-open
```

Window placement and the 1440 by 960 point capture region are fixed in the
script so repeated images line up. `--settle-seconds` can be increased on a
slower machine.

For Mail captures, the runner briefly enables Thunderbird's built-in
Marionette service on an available loopback-only port and selects the first
synthetic Inbox message after the database view is ready. The connection is
closed before capture completes and the isolated Thunderbird process is then
terminated.

## Fixture contents

The profile contains:

- an offline fictional POP account called `hello@liquidstudio.example`;
- Inbox, Sent, Drafts, Archives, Trash, Junk, and nested project folders;
- realistic read, unread, flagged, attachment, plain-text, HTML, and emoji mail;
- seven fictional contacts in a native Thunderbird SQLite address book;
- six fictional events in a local ICS calendar;
- a preselected Inbox and expanded folder tree;
- the current repository copies of LiquidBird CSS and icons.

The chosen base date defaults to the day the profile is generated. A fixed date
can be supplied for reproducible visual comparisons:

```sh
python3 scripts/demo.py prepare --base-date 2026-07-28
```

## Cleanup

```sh
python3 scripts/demo.py clean
```

This removes only the marked generated profile. Screenshots remain available
until `.demo/` is removed manually.
