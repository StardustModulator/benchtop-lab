<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Inter: upstream record

- Upstream project: <https://github.com/rsms/inter> (SIL Open Font License 1.1; `OFL.txt` here is its `LICENSE.txt` from the `master` branch, fetched 2026-11-23).
- Files: variable WOFF2 subsets (Latin and Latin-Extended; axes: opsz 14–32, wght 100–900), copied **unmodified** from the npm
  package `@fontsource-variable/inter 5.3.0`, which repackages the Google Fonts build v20 (2025-09-10).
- Used by: `docs/assets/stylesheets/fonts.css` (the `unicode-range` values there are the package's own).
- To update: `npm pack <package>`, copy the same file names from `package/files/`, refresh the checksums below,
  and rebuild the docs.

| File | SHA-256 |
| --- | --- |
| `inter-latin-ext-opsz-normal.woff2` | `5e6d4fe9d9f4bff8b2a2469d25ab19576bb85331e22c6ed51398e16f95d56a9c` |
| `inter-latin-opsz-normal.woff2` | `2c295d99e26dcf357d4d01bcf270fd6924b600c9a13dd8c363ef114f4c6976fa` |
