# Compatibility and test matrix

LiquidBird depends on Thunderbird's internal interface selectors. This matrix
records configurations that have actually been exercised; it is not a promise
that every future point release will remain compatible.

## Verified configuration

| LiquidBird | Thunderbird | Operating system | Appearance | Density | Message list | Pane layout |
| --- | --- | --- | --- | --- | --- | --- |
| 0.1.0 | Thunderbird Beta 154.0, build 15426.7.21 | macOS 27 | Light and dark | Default | Card and table | Vertical and classic |
| Linux/niri port branch | Thunderbird 156.0 (`156.0-1`) | Arch Linux, native Wayland, niri `26.04` modified build | Light and dark | Default | Card | Vertical |

The primary macOS development layout uses default density, card view, and
vertical view. Table view and classic layout were also exercised on macOS.
CSS coverage exists for compact and touch density and wide layout, but those
configurations remain best-effort because they have not completed a formal
release check.

## Unverified configurations

| Configuration | Support level | Notes |
| --- | --- | --- |
| Thunderbird 140–153 | Best effort | Earlier internal selectors may differ; no release matrix is recorded yet. |
| Thunderbird releases other than the exact rows above | Best effort | Internal selectors can change across releases. |
| Other Linux compositors or niri builds without `background-effect` blur | Best effort | Theme CSS can load, but the tested sidebar blur may be unavailable. |
| Windows | Best effort | CSS color/material fallbacks exist; native AppKit materials do not. |

## Linux/niri port verification record

Recorded on 2026-09-25 with Thunderbird 156.0 on native Wayland and niri
`26.04 (v26.04-156-g953a8c3f-modified)`. The profile contained only offline,
synthetic data. The Linux dark and light mail images are tracked in
`docs/screenshots/`.

| Area | Status | Evidence and scope |
| --- | --- | --- |
| Mail in dark and light appearances | Verified | Selected synthetic message, folder pane, card list, reader, attachment bar, and Today Pane were captured in both appearances. |
| Sidebar transparency and niri blur | Verified | Stage 1 on/off captures showed the compositor blur. Final dark sidebars measured 204/255 alpha; the mail list and reader remained 255/255. See `LINUX_STAGE1.md`. |
| Traffic-light title buttons | Partially verified | Left placement and active state appeared in real niri captures; inactive, hover, press, and maximize states were mapped to source images but were not captured. |
| Address Book, Calendar, Settings, Compose | Partially verified | Each surface launched and rendered in the same isolated dark profile. Full interaction and layout combinations were not exercised. |
| Table view, classic/wide panes, compact/touch density, tasks, chat, add-ons, account settings | Unverified | No Linux visual pass recorded. |
| Reduced transparency, increased contrast, keyboard-only interaction | Unverified | CSS fallbacks exist, but no Linux manual pass was recorded. |

The Linux compose window retains Thunderbird's Linux menu bar, and the main
window retains its application menu. Their native menu placement differs from
the macOS README images.

## 0.1.0 release verification record

Recorded on 2026-07-28 with Thunderbird Beta 154.0, build 15426.7.21, on
macOS 27. “Verified” means the behavior was exercised in the stated build;
“unverified” means LiquidBird contains targeted CSS but no release claim is made.

| Area | Status | Evidence and scope |
| --- | --- | --- |
| Light and dark appearances | Verified | Synthetic mail captures are tracked in `docs/screenshots/`; affected secondary surfaces were also reviewed during development. |
| Active and inactive windows | Verified | Both active development use and inactive captured-window states were reviewed. |
| Default density | Verified | Used throughout the release review. |
| Compact and touch density | Unverified | Targeted CSS exists; no completed 0.1.0 manual pass. |
| Card and table message lists | Verified | Selection, unread state, header geometry, scrolling, and quick-filter interactions were exercised in both views. |
| Vertical and classic pane layouts | Verified | Reading-pane layout and the unified message-action bar were exercised in both layouts. |
| Wide pane layout | Unverified | Targeted CSS exists; no completed 0.1.0 manual pass. |
| Folder navigation, message selection, quick filter, and global search | Verified | Navigation, selection contrast, toolbar spacing, search fields, filter states, and menus were reviewed. |
| Reading-pane header and actions | Verified | Header layout, long and emoji subjects, action grouping, split actions, and hover states were reviewed. |
| Compose | Verified | Addressing rows, toolbar and overflow menus, fields, editor controls, and attachments were reviewed. |
| Address book, calendar, and Today Pane | Verified | Navigation, search, contact details, calendar content, and Today Pane were reviewed. |
| Settings, account settings, and add-ons | Verified | Navigation, controls, menus, forms, search, and add-on cards were reviewed. |
| Tasks and chat | Unverified | Targeted CSS exists; no completed 0.1.0 surface pass. |
| Keyboard focus and menu navigation | Partially verified | Focus and menu states were encountered during development; no systematic keyboard-only pass was recorded. |
| Increased contrast, reduced transparency, and reduced motion | Unverified | Fallback rules exist; no completed 0.1.0 manual pass with these system preferences enabled. |

For later releases, copy this table into a new versioned record, update the
exact Thunderbird and macOS builds, and retest every row whose selectors or
component structure changed.

Use the bug-report form for regressions. A report should state whether the
problem reproduces without personal `custom.css` rules and other add-ons.
