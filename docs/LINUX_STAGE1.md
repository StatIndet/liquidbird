# Linux/niri stage 1: isolated profile and material test

This document records the first isolated test of the main Thunderbird window,
before the Linux port was packaged. For the current release installation, see
[the Linux/niri setup guide](LINUX.md). In this stage 1 test, the upstream
theme files and normal Thunderbird profiles were not modified. The demo
copied the small Linux probe into `.demo/profile` only; `.demo/` is ignored by
Git.

## Tested environment (2026-09-25)

| Item | Observed value |
| --- | --- |
| LiquidBird source | `5535479d73618cf8a4c644412c485783bcfd6cc7` (0.1.0) |
| Thunderbird | Arch `thunderbird 156.0-1`; native `wayland` window protocol |
| Rendering | `WebRender`, remote layer manager enabled (queried inside Thunderbird) |
| niri | `26.04 (v26.04-156-g953a8c3f-modified)` with background blur |
| Window app-id | `org.mozilla.Thunderbird` |
| Output | DP-1, 2560 × 1440, scale 1, 180 Hz; eDP-1 disabled |
| GTK theme | `MacTahoe-Dark` |
| Fontconfig sans-serif match | `LXGW WenKai GB Screen` |
| MacTahoe source | `f19899811eff6d127afc38c4fa4981b220cb2ea2` (not yet used by this probe) |
| Test appearance | Dark, default Thunderbird density, card view, vertical view |
| Test window | 1440 × 960 logical pixels, floating |
| Fixture | 16 synthetic messages, 7 contacts, 6 events; offline profile |

No additional package was needed on this machine. Thunderbird, Python, the
modified niri, and `grim` were already installed. `kitty` was used only to
display a high-contrast test backdrop. Pillow was used only to inspect PNG
alpha; neither is a runtime dependency of the theme.

## Reproduce

Close the synthetic Thunderbird window before rebuilding its profile. Then:

```sh
python3 scripts/demo.py prepare --base-date 2026-07-28
python3 scripts/demo.py launch
```

`launch` uses the installed `thunderbird` on Linux. In a Wayland session it
sets `GDK_BACKEND=wayland` and `MOZ_ENABLE_WAYLAND=1` for that child process,
because this machine exports `GDK_BACKEND=x11` globally. The launcher uses
`--no-remote --profile ... --purgecaches`, so it cannot open the normal profile.
It logs startup diagnostics to `.demo/thunderbird-launch.log`.

Open the synthetic Inbox and select the first message, **Final review: Liquid
launch assets**. `niri msg windows` reports the window ID and app-id. To match
the reference's logical size, use that ID in:

```sh
niri msg action move-window-to-floating --id <ID>
niri msg action set-window-width --id <ID> 1440
niri msg action set-window-height --id <ID> 960
niri msg action center-window --id <ID>
```

For the blur run, temporarily add this include to your niri config, adjusting
the absolute repository path if needed:

```kdl
include "/absolute/path/to/liquidbird/integration/niri-stage1.kdl"
```

Run `niri validate`, restart the synthetic Thunderbird window so the rule is
applied to a new surface, and capture with `grim` or `niri msg action
screenshot-window`. Remove the include and restart the window for the
no-blur control. The test rule keeps window `opacity 1.0`; alpha comes only from
`linux/chrome.css`. This rule was removed from the live niri config after the
test.

## Result

The original opaque layer behind the folder pane was `#tabpanelcontainer` in
Thunderbird 156.0. In the synthetic window, `#folderPane` already computed to
`rgba(46, 46, 49, 0.7)`, but `#tabpanelcontainer` and the `about:3pane` root
computed to opaque `rgb(51, 51, 51)`. The Linux probe clears those two backing
layers and applies the material to the tab strip and sidebars.

The niri window capture showed alpha **179/255** on an empty sidebar pixel and
**255/255** in the mail list and reading pane. Against a sharp checkerboard,
the sidebar showed sharp blocks with blur disabled and softened blocks with
blur enabled. Foreground text remained crisp in both captures; the selected
message body remained opaque. The local evidence is in `.demo/`:

- `mail-selected-blur-off.png`
- `mail-selected-blur-on.png`
- `mail-selected-window-alpha.png`

These images and the profile are generated test artifacts and are not tracked.
The two blur captures used the same 1440 × 960 window size, but niri placed the
floating window at different screen coordinates. They establish the material
behavior, not pixel-perfect similarity to the macOS reference.

## Scope and cleanup

The probe covers the main window in dark mode on Thunderbird 156.0. It does not
yet validate light mode, popup menus, compose, settings, or other Thunderbird
versions. MacTahoe assets and title buttons are for a later stage. The existing
`scripts/demo.py capture` automation remains macOS-only.

The live niri include and contrast-backdrop window were removed after testing.
The synthetic profile can be removed with `python3 scripts/demo.py clean` after
closing its Thunderbird window. The normal Thunderbird profile was not opened
or changed.
