# Contributing to LiquidBird

Thank you for helping make LiquidBird more reliable across Thunderbird releases.

## Before opening an issue

1. Update to the latest LiquidBird release.
2. Temporarily move personal rules out of `custom.css`.
3. Disable other `userChrome.css` and `userContent.css` customizations.
4. Fully quit and reopen Thunderbird.
5. Check the [support guide](SUPPORT.md) and
   [compatibility matrix](docs/COMPATIBILITY.md).

For visual bugs, use the bug-report template and include the exact Thunderbird
version and build, macOS version, appearance, density, pane layout, and a
screenshot. Remove or obscure personal mail and account information first.

## Proposing a change

- Keep changes focused on one component or compatibility problem.
- Prefer Thunderbird semantic variables and system colors over fixed colors.
- Preserve keyboard focus, increased contrast, reduced transparency, reduced
  motion, and forced-colors behavior.
- Do not add Apple Design Resources, SF Symbols, or assets whose license does
  not permit redistribution.
- Put new redistributable third-party assets in `THIRD_PARTY_NOTICES.md` and
  include their full license under `licenses/`.
- Run `python3 scripts/check.py` before submitting a pull request.
- Run `python3 -m unittest discover -s tests` after changing the synthetic
  profile or screenshot automation.
- If the change affects release contents, also run
  `python3 scripts/package_release.py --output dist` and inspect the archive.

## Testing checklist

At minimum, exercise the affected surface in both light and dark appearances.
For layout changes, also check compact and default density, keyboard focus, and
the relevant card/table or horizontal/vertical pane combinations. Record the
tested configuration in the pull request.

## Pull requests

Explain the visible problem, the selector or component changed, and why the
new rule is narrowly scoped. Include before-and-after screenshots for visual
changes. Do not include a Thunderbird profile, mailbox data, `.DS_Store`, or
generated `dist/` archives in a pull request.

By contributing, you agree that your contribution is licensed under the
project's [MIT License](LICENSE).
