# Designed coverage and constraints

This document records surfaces for which LiquidBird contains targeted styling.
It is a selector-coverage inventory, not a claim that every combination has
been verified on every Thunderbird version. See
[`COMPATIBILITY.md`](COMPATIBILITY.md) for the tested release matrix.

## Styled surfaces

| Thunderbird surface | LiquidBird coverage |
| --- | --- |
| Window chrome and titlebar | Native macOS titlebar material, tab strip, traffic-light spacing, inactive-window state |
| Unified toolbar | Leading and trailing action groups, toolbar customization, global search, toggle states |
| Spaces toolbar | Mail, contacts, calendar, tasks, chat, and settings states/glyphs |
| Folder pane | Accounts, all standard folders, tags, custom folders, unread badges, selection |
| Message list | Card view, table view, grouped rows, unread state, hover/focus selection |
| Reading pane | Subject, sender/recipients, avatars, notifications, all header actions |
| Search and quick filter | Global search, quick-filter field, filter and display controls |
| Compose | Toolbar, addressing fields, attachments, editor container, status area |
| Contacts | Books, lists, contact cards, details pane, selection states |
| Calendar and tasks | Sidebar/content surfaces, events, task rows, today pane |
| Chat | Conversation list, content deck, selected and hover states |
| Settings and accounts | Shared semantic tokens plus `userContent.css` internal-page styling |
| Add-ons | Internal page, cards, controls, search, navigation |
| Menus, panels, dialogs | Native macOS menu material where available; glass fallback elsewhere |
| Accessibility | Dark mode, system accent, keyboard focus, compact/default/touch density, increased contrast, forced colors, reduced transparency/motion |

Compared with the pinned FluentBird revision listed in
[`THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md), LiquidBird contains targeted
rules for the same main mail chrome plus compose, settings, account settings,
add-ons, dialogs, and secondary Thunderbird surfaces. Actual behavior still
depends on the Thunderbird version and which internals it exposes.

## Why coverage cannot be literally 100%

`userChrome.css` is an unsupported customization mechanism. Some Thunderbird
components render inside closed shadow roots and don't expose style parts or
semantic variables. Message bodies are intentionally not themed so sender
content and accessibility choices remain intact. Native macOS menu and window
materials are also rendered outside normal CSS.

LiquidBird uses “designed coverage” to mean that a reachable Thunderbird UI
surface has targeted rules without modifying Thunderbird itself. Components inside a closed
shadow root keep Thunderbird's native styling, but inherit LiquidBird's colors
when Thunderbird exposes its Bolt variables.

## Implementation notes

- `appearance: -moz-sidebar` and `appearance: -moz-window-titlebar` ask Gecko
  to create real `NSVisualEffectView` regions on macOS.
- Liquid Glass is reserved for functional chrome: titlebars, sidebars,
  toolbars, buttons, and panels. Message/content backgrounds remain standard
  materials, matching Apple's hierarchy guidance.
- Controls use system `AccentColor`, `CanvasText`, and semantic color mixing
  rather than fixed Apple color values.
- Focused list selections use the system accent and adaptive text; inactive
  selections use a neutral highlight so focus location remains unambiguous.
- Liquid Glass is never placed inside message, settings, card, or editor
  content layers. Those areas use standard opaque or elevated materials.
- Press scaling is removed when the user requests reduced motion.
