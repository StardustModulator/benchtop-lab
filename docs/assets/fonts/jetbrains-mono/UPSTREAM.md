<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# JetBrains Mono: upstream record

- Upstream project: <https://github.com/JetBrains/JetBrainsMono> (SIL Open Font License 1.1; `OFL.txt` here is its `OFL.txt` from the `master` branch, fetched 2026-11-23).
- Files: variable WOFF2 subsets (Latin and Latin-Extended; axes: wght 100–800), copied **unmodified** from the npm
  package `@fontsource-variable/jetbrains-mono 5.3.0`, which repackages the Google Fonts build v24 (2025-09-11).
- Used by: `docs/assets/stylesheets/fonts.css` (the `unicode-range` values there are the package's own).
- To update: `npm pack <package>`, copy the same file names from `package/files/`, refresh the checksums below,
  and rebuild the docs.

| File | SHA-256 |
| --- | --- |
| `jetbrains-mono-latin-ext-wght-normal.woff2` | `79bfdab9ba467e26eea4122e6f2567e188dd8a09a8c730d501fc487c4ab99c6e` |
| `jetbrains-mono-latin-wght-normal.woff2` | `18be452724bfdc236c074ca94a249a7f41a86752c7d04ab258ce9ed5651f6a7e` |
