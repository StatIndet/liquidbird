# Design research

## Reference system

Apple published its macOS 27 Sketch kit on June 23, 2026. The update includes
the current Liquid Glass treatment, expanded component states, improved
resizing, and a complete dark appearance for macOS. It is the closest exact
visual reference for this project:

- [Apple's macOS 27 design-kit announcement](https://developer.apple.com/news/?id=e2lxw9l1)
- [Apple Design Resources](https://developer.apple.com/design/resources/)
- [Human Interface Guidelines: Designing for macOS](https://developer.apple.com/design/human-interface-guidelines/designing-for-macos/)

The Apple kit is not part of LiquidBird. Apple's Design Resources license limits
the kit to mock-ups for Apple-platform software and prohibits embedding or
redistributing its template content. LiquidBird uses the kit and HIG as a visual
reference, then expresses the system through original CSS and open assets.

## Why there is no third-party component library

Thunderbird's `userChrome.css` is a privileged CSS customization sheet, not a
web application runtime. React, SwiftUI wrappers, Web Components, and most
Liquid Glass packages cannot execute there. CSS-only “macOS” libraries tend to
reproduce older releases and do not know Thunderbird's XUL elements, current
web components, or shadow-root tokens.

The useful reusable layer is already inside Gecko: on macOS,
`appearance: -moz-sidebar` and `appearance: -moz-window-titlebar` map regions
to real AppKit `NSVisualEffectView` materials. LiquidBird uses these native hooks
instead of approximating the whole window with blur. Thunderbird's inherited
Bolt color tokens are remapped to semantic system colors, extending the result
into web components that expose those tokens.

Mozilla source references:

- [Gecko maps `MozSidebar` and `MozWindowTitlebar` to macOS theme geometry](https://searchfox.org/firefox-main/source/widget/cocoa/nsNativeThemeCocoa.mm)
- [Gecko's AppKit vibrancy manager](https://searchfox.org/firefox-main/source/widget/cocoa/VibrancyManager.mm)
- [Thunderbird shared color tokens](https://searchfox.org/comm-central/source/mail/themes/shared/mail/colors.css)

## macOS 27 choices represented in CSS

- The sidebar, titlebar, toolbars, and interactive controls form the glass
  functional layer. Message content remains on a standard content material.
- Window-adjacent surfaces use larger, concentric radii; nested controls use
  progressively smaller radii.
- Interactive glass scales on press and settles immediately on release. Motion
  is disabled for the reduced-motion preference.
- Icon-only buttons are circular, icon-plus-text and horizontally grouped
  actions are capsules, and rectangular controls are reserved for structural
  rows or vertical stacks with a substantially larger corner radius.
- System semantic colors and the user's accent color take precedence over
  hard-coded swatches.
- Interface glyphs render through masks and semantic colors: neutral controls
  use adaptive label colors, selected navigation uses the system accent,
  prominent actions use accent-colored backgrounds with adaptive foregrounds,
  and warning/destructive/status colors appear only when they convey meaning.
- User-defined tag colors remain recognizable, but are mixed toward the
  adaptive primary-label color so their glyphs retain contrast in either
  appearance.
- Increased contrast and reduced transparency produce more solid, strongly
  outlined surfaces.

References:

- [Human Interface Guidelines: Materials](https://developer.apple.com/design/human-interface-guidelines/materials)
- [Human Interface Guidelines: Sidebars](https://developer.apple.com/design/human-interface-guidelines/sidebars)
- [Human Interface Guidelines: Buttons](https://developer.apple.com/design/human-interface-guidelines/buttons)
- [Human Interface Guidelines: Toolbars](https://developer.apple.com/design/human-interface-guidelines/toolbars)
- [Human Interface Guidelines: Search fields](https://developer.apple.com/design/human-interface-guidelines/search-fields)
- [Human Interface Guidelines: Lists and tables](https://developer.apple.com/design/human-interface-guidelines/lists-and-tables)
- [Human Interface Guidelines: Focus and selection](https://developer.apple.com/design/human-interface-guidelines/focus-and-selection)
- [Human Interface Guidelines: Typography](https://developer.apple.com/design/human-interface-guidelines/typography)
- [Human Interface Guidelines: Accessibility](https://developer.apple.com/design/human-interface-guidelines/accessibility)
- [Modernize your AppKit app (WWDC26)](https://developer.apple.com/videos/play/wwdc2026/289/)

## Component audit

| Component family | Applied macOS behavior |
| --- | --- |
| Window and tabs | Native titlebar material, traffic-light clearance, subdued inactive-window state, compact selected-tab capsule |
| Unified toolbar | One regular glass layer, logical leading/center/trailing groups, global search in the center, monochrome controls |
| Spaces navigation | Circular icon-only controls, neutral unselected symbols, accent selected symbol, immediate press feedback |
| Folder sidebar | Native sidebar material, accent-colored navigation glyphs, disclosure hierarchy, whole-row selection, adaptive unread badges |
| List and table rows | Whole-row focus highlight, accent plus adaptive text while focused, neutral highlight while focus is elsewhere, no custom selection stripe |
| Search and fields | Search fields remain capsules; ordinary and compose address fields use rounded rectangles with a distinct focus ring |
| Toolbar actions | Related Reply/Archive/More actions share a segmented capsule; isolated icon actions are circular; labeled standalone actions are capsules |
| Toggle buttons | An elevated adaptive material communicates the toggled state; accent remains reserved for navigation, focus, and primary actions |
| Reading content | Header controls are separated from message content; message HTML remains unmodified so sender formatting and accessibility survive |
| Compose | Glass toolbar, accent Send action, standard content editor, compact attachment chips, and status bar separation |
| Contacts, Calendar, Tasks, Chat | Native sidebar/content split, consistent row selection, restrained event colors, and shared toolbar treatment |
| Menus, popovers, dialogs | Native macOS material where Gecko supplies it; concise rounded menu rows, semantic destructive actions, elevated standard material elsewhere |
| Typography | 13 px system-font baseline, 11 px minimum supporting labels, size-specific tracking, tabular dates and counts |
| Accessibility | Dark Mode, inactive-window state, keyboard focus, system accent, increased contrast, reduced motion, reduced transparency, and forced-colors fallbacks |

Thunderbird density remains user-controlled. LiquidBird maps compact, default,
and touch density to different control and navigation sizes instead of forcing
one fixed geometry.

## Icons

SF Symbols is the canonical Apple symbol system, but exported Apple glyphs are
not bundled or republished here. LiquidBird uses Lucide because its thin,
round-capped outline language adapts well to small macOS controls and its ISC
license explicitly allows copying, modification, and redistribution. Every
bundled icon is an unmodified upstream SVG with the complete license notice.

- [Lucide](https://lucide.dev/)
- [Lucide license](https://github.com/lucide-icons/lucide/blob/main/LICENSE)
