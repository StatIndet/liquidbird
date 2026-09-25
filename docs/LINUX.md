# Linux and niri setup

LiquidBird's Linux layer brings the macOS theme's spacing, controls, and
sidebar material to Thunderbird on native Wayland. The layer is distributed
with the regular release ZIP. Its chrome loader applies the shared theme,
then Linux material, layout, and title-button sheets, followed by `custom.css`.
The content loader applies the shared content sheet before its Linux layer.
All Linux rules are platform-gated, so the same release files also work on
macOS.

The blur seen through translucent areas is drawn by niri, not by Thunderbird.
The tested machine ran Thunderbird 156.0 and a niri 26.04 build with
`background-effect { blur true }` support. A niri build without that option can
still use the theme, but it cannot produce the same compositor blur. The
[stage 1 record](LINUX_STAGE1.md) describes the measured alpha and comparison
captures. The original README screenshots were taken on macOS; the Linux
appearance is an adaptation of those views, not a claim of pixel identity.
The [Linux dark](screenshots/liquidbird-linux-niri-dark.png) and
[Linux light](screenshots/liquidbird-linux-niri-light.png) captures show the
actual port on the tested system.

## What you need

- Thunderbird running as a native Wayland window. The stage 1 machine used
  Thunderbird 156.0; other versions can change internal selectors.
- niri with background-effect blur support if you want the translucent
  sidebar to blur the desktop behind it. The release's
  `integration/niri.kdl` contains the tested window rule.
- The release ZIP and its `SHA256SUMS` file. Python is only needed for the
  optional synthetic demo; `grim` is only needed for manual screenshots.
- An installed MacTahoe GTK theme is optional for closer desktop-wide visual
  consistency. The GTK theme package is separate; the release includes a
  licensed set of its title-button images.

The Linux accent defaults to the blue used in the upstream README screenshots.
To follow your desktop accent instead, set `--lb-accent: AccentColor;` in
`custom.css`. The Linux titlebar keeps Thunderbird's application menu because
it provides access to commands that macOS exposes through its native menu bar.

No additional runtime package was required on the stage 1 machine: its
Thunderbird, niri, and MacTahoe GTK theme were already installed.

Until a fork release is tagged, build the installable ZIP from this branch with
`python3 scripts/package_release.py --output dist`. The generated ZIP and
`SHA256SUMS` are in `dist/`; check the checksum from that directory with
`(cd dist && sha256sum -c SHA256SUMS)`.

## Install

1. In Thunderbird, set
   `toolkit.legacyUserProfileCustomizations.stylesheets` to `true` under
   **Settings → General → Config Editor**.
2. Open **Help → Troubleshooting Information**, find **Profile Folder**, and
   choose **Open Directory**. Record that path, then fully quit Thunderbird.
3. Back up any existing `chrome` directory outside the active profile's
   `chrome` directory.
4. From the release ZIP's `chrome` directory, copy `liquidbird.css`,
   `liquidbird-content.css`, and the complete `Icons` and `linux` directories
   into the profile's `chrome` directory. Keep their relative paths exactly
   as distributed.
5. If `userChrome.css` does not exist, copy it from the release. If it does
   exist, add these imports at the very beginning, before other CSS rules:

   ```css
   @import url("liquidbird.css");
   @import url("linux/chrome.css");
   @import url("linux/mail-layout.css");
   @import url("linux/titlebuttons.css");
   @import url("custom.css");
   ```

6. If `userContent.css` does not exist, copy it from the release. Otherwise,
   add these imports at the very beginning:

   ```css
   @import url("liquidbird-content.css");
   @import url("linux/content.css");
   ```

7. Preserve any existing `custom.css`. If it does not exist, duplicate
   `custom.css.example` from the release and rename the duplicate
   `custom.css`. Put personal overrides there.
8. Fully reopen Thunderbird. For the closest match to the README mail view,
   use default density, card view, and vertical view.

The release's two loader files are shared between macOS and Linux. Their
Linux imports have no effect on macOS because the imported rules are
platform-gated. Keep all imported files in the profile so the loaders resolve
cleanly on either platform.

## Enable niri blur

Copy the release's `integration/niri.kdl` to a stable location such as
`~/.config/niri/liquidbird.kdl`. Back up your niri config, then include the
copied file from your main config using its actual absolute path:

```kdl
include "/absolute/path/to/liquidbird.kdl"
```

Run `niri validate` after editing the config. Reopen Thunderbird so the new
window receives the rule. The rule targets the native Wayland app ID
`org.mozilla.Thunderbird`, keeps the overall window at opacity `1.0`, and
blurs only where LiquidBird's CSS exposes alpha. The mail list and reading
pane remain opaque. If niri rejects `background-effect`, use a build that
supports that option or omit the rule; installing a CSS package cannot add
compositor blur.
The popup rule sets an 18 px corner radius so niri clips its own blur behind
Thunderbird's rounded menus.

If Thunderbird inherits `GDK_BACKEND=x11` from your session, launch it with
`GDK_BACKEND=wayland MOZ_ENABLE_WAYLAND=1` so the native Wayland rule can
match. The isolated `scripts/demo.py launch` command sets these variables for
its child process on Linux and does not change your normal profile.

## Verify safely

The synthetic demo creates a separate, offline Thunderbird profile. From the
repository or release directory, run:

```sh
python3 scripts/demo.py prepare
python3 scripts/demo.py launch
```

Inspect the folder pane against a high-contrast desktop background. With
niri blur enabled, the background behind the translucent sidebar should be
soft; message text and the reading pane should stay sharp. The stage 1 run
measured alpha `179/255` at an empty sidebar pixel and `255/255` in the mail
and reading panes. In the final dark port capture, both left sidebars measured
`204/255` and the mail list and reader remained `255/255`. These measurements
describe the tested main window, not every Thunderbird surface or display
configuration.

## Update, disable, or remove

Before an update, fully quit Thunderbird and back up the profile's `chrome`
directory. Replace the release-owned `liquidbird.css`,
`liquidbird-content.css`, `Icons`, and `linux` files. Compare the new loader
files with your existing loaders and merge import changes; do not overwrite
personal rules or `custom.css`. Update the copied niri rule if it changed,
then validate the niri config and reopen Thunderbird.

To disable the theme temporarily, fully quit Thunderbird and comment out
LiquidBird's imports in both loader files. To disable only compositor blur,
remove the `integration/niri.kdl` include from your niri config and validate
the configuration; then reopen Thunderbird.

To uninstall while keeping other profile CSS, fully quit Thunderbird, remove
the LiquidBird imports from the loader files, and remove the release-owned
`liquidbird.css`, `liquidbird-content.css`, `Icons`, and `linux` files. Keep
`custom.css` if it contains personal work. Remove the niri include and copied
rule, validate the configuration, and reopen Thunderbird. Restoring the
backed-up `chrome` directory is the simplest rollback.
