# Release process

LiquidBird releases are deterministic ZIP archives created from a clean Git tag.
The version follows [Semantic Versioning](https://semver.org/). Because the
theme relies on unsupported Thunderbird internals, compatibility fixes may be
released frequently without implying support for every Thunderbird version.

## Prepare a release

1. Confirm the working tree contains only intentional changes.
2. Update `VERSION` and move entries from **Unreleased** into a dated section
   in `CHANGELOG.md`.
3. Update `docs/COMPATIBILITY.md` with configurations that were actually
   exercised. Do not infer support from selector coverage alone.
4. Complete the manual release checklist in that document.
5. Run:

   ```sh
   python3 scripts/check.py
   python3 scripts/package_release.py --output dist
   ```

6. Inspect `dist/LiquidBird-<version>.zip`. It must contain the `chrome/`
   directory, `chrome/linux/` (including `chrome.css` and `content.css`),
   `integration/niri.kdl`, `custom.css.example` rather than `custom.css`, all
   bundled-asset licenses, `checksums/third-party.sha256`, notices, and the
   release documentation. Check that no temporary files from the Linux visual
   tests entered the ZIP.
7. Verify the checksum from `dist/SHA256SUMS`.

## Publish

Commit the prepared release, create an annotated `v<version>` tag, and push the
commit to `main`, then push the tag. The release workflow verifies that the tag
matches `VERSION` and points to a commit on `main`, runs all checks, rebuilds
the ZIP, and publishes the ZIP and checksum as a GitHub release. To retry a
failed publication, run the **Release** workflow manually from GitHub Actions
and enter the existing tag. A version tag from an earlier release cannot be
reused for a new commit; update `VERSION` and create a new tag for the Linux
port release.

Do not create or push the tag until the commit is ready to be public. Never
publish a Thunderbird profile, a populated `custom.css`, generated `.DS_Store`
metadata, or screenshots containing personal information.

## After publishing

Install the release ZIP into a clean test profile using only the public README.
Confirm that the GitHub release notes and checksum are present, then reset the
**Unreleased** section for subsequent work.
