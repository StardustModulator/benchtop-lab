<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Source Serif 4: upstream record

- Upstream project: <https://github.com/adobe-fonts/source-serif> (SIL Open Font License 1.1; `OFL.txt` here is its `LICENSE.md` from the `release` branch, fetched 2026-11-23).
- Files: variable WOFF2 subsets (Latin and Latin-Extended; axes: opsz 8–60, wght 200–900), copied **unmodified** from the npm
  package `@fontsource-variable/source-serif-4 5.3.1`, which repackages the Google Fonts build v15 (2026-10-01).
- Used by: `docs/assets/stylesheets/fonts.css` (the `unicode-range` values there are the package's own).
- To update: `npm pack <package>`, copy the same file names from `package/files/`, refresh the checksums below,
  and rebuild the docs.

| File | SHA-256 |
| --- | --- |
| `source-serif-4-latin-ext-opsz-italic.woff2` | `2078240cee94e627d0e180d56d74a11b2a1d387bbd61a9b7269f0a43df756896` |
| `source-serif-4-latin-ext-opsz-normal.woff2` | `155f6e701097cc269cf8d5d7ac86795f263f1afbeb47c14d1d747108c9335389` |
| `source-serif-4-latin-opsz-italic.woff2` | `96e6393209728ab93c334ae739af8a040cd2006c82e8614d6465a8084db88f89` |
| `source-serif-4-latin-opsz-normal.woff2` | `f2ea9c12d2fe9bd3a9589b02ad2c0909da88f30938c91adc838c4f4098f9f9e0` |
