---
name: ui-excellence
description: Design system, typography, colour tokens, accessibility rules and a review checklist for every Benchtop Lab user interface (MkDocs site, grader HTML report cards, dataset-doctor reports, dashboards, landing page, charts, rich CLI output). Use before building or changing anything a person looks at.
---

<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# UI excellence: the Benchtop Lab design system

Standing rule from the owner: every interface we ship must look and read like the best university-lab and research
sites (MIT CSAIL / Stanford AI Lab project pages, Distill.pub) with Linear/Vercel-level polish. "Good enough" is a
failing grade. Calm, precise, typographically excellent, fast, accessible. No template look, no stock gradients,
no emoji decoration, no visual noise.

Principles, in priority order:
1. **Legibility first.** Text is the product. Comfortable measure, generous leading, real hierarchy.
2. **One system.** Every surface (docs, reports, CLI, charts) uses the same tokens below. No one-off colours or sizes.
3. **Honest data.** Charts show uncertainty (Wilson / bootstrap intervals), label axes with units, never truncate
   axes to exaggerate, and are readable in greyscale and by colour-blind readers.
4. **Accessible by construction.** WCAG 2.2 AA minimum, in both light and dark themes.
5. **Quiet motion.** Motion only to explain state changes, 150–250 ms, and disabled under `prefers-reduced-motion`.

## 1. Typography

Font pairing (all SIL OFL-1.1, self-hosted as WOFF2 subsets; **never** load fonts from a CDN or Google Fonts, which
would be third-party tracking, see ADR-001). OFL-1.1 is permitted for font files only; vendor them under
`docs/assets/fonts/<family>/` with their `OFL.txt`, list them in NOTICE and REUSE.toml.

| Role | Family | Use | Fallback stack |
| --- | --- | --- | --- |
| Display + headings | **Inter Display** / Inter (600–700, tight tracking) | h1–h4, nav, UI labels | `Inter, "Inter var", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif` |
| Long-form prose | **Source Serif 4** (optical sizes) | lesson body text, report narrative | `"Source Serif 4", "Iowan Old Style", Charter, Georgia, serif` |
| Code, numbers in tables | **JetBrains Mono** (400/500) | code, CLI, metrics | `"JetBrains Mono", ui-monospace, "SF Mono", Menlo, Consolas, monospace` |

If a surface cannot embed fonts (e.g. a single-file HTML report that must stay < 1.5 MB), use the fallback stacks;
they are chosen to degrade gracefully. Subset to Latin + Latin-Extended + punctuation/math, `font-display: swap`.

Type scale: modular, ratio **1.25 (major third)**, base **17 px** (1.0625 rem) for prose, 15 px for dense UI.

| Token | Size | Line height | Weight | Tracking | Use |
| --- | --- | --- | --- | --- | --- |
| `--fs-display` | 3.052rem (clamp 2.25rem → 3.052rem) | 1.08 | 700 | -0.025em | landing hero, report title |
| `--fs-h1` | 2.441rem | 1.15 | 700 | -0.02em | page title |
| `--fs-h2` | 1.953rem | 1.2 | 650 | -0.015em | section |
| `--fs-h3` | 1.563rem | 1.3 | 600 | -0.01em | subsection |
| `--fs-h4` | 1.25rem | 1.4 | 600 | 0 | minor heading |
| `--fs-body` | 1.0625rem | 1.65 (prose) / 1.5 (UI) | 400 | 0 | body |
| `--fs-small` | 0.875rem | 1.5 | 400–500 | 0.005em | captions, meta |
| `--fs-micro` | 0.75rem | 1.4 | 600 | 0.06em, uppercase | eyebrows, table headers |
| `--fs-code` | 0.9em of context | 1.55 | 400 | 0 | code |

Rules:
- Measure: prose **60–75 characters** (`max-width: 68ch`). Tables and figures may break out wider (up to 1100 px),
  Distill-style.
- Vertical rhythm on a **4 px grid**; space before a heading > space after it (≈ 2:1).
- Use real typographic characters: curly quotes, en dash for ranges (10–20), em dash or spaced en dash for breaks,
  `×` for dimensions, proper minus `−` in numbers, non-breaking space between number and unit (`30 fps`, `4.5 h`).
- Numbers in tables: `font-variant-numeric: tabular-nums lining-nums`, right-aligned, consistent decimals,
  uncertainty shown as `0.82 [0.74, 0.88]` with the interval in `--color-text-muted`.
- `text-wrap: balance` on headings, `text-wrap: pretty` on paragraphs, `hanging-punctuation: first` where supported,
  hyphenation only for prose (`hyphens: auto` with `lang` set).
- Never use more than two weights on one screen besides bold emphasis. Never fake bold or italic.
- Never centre long text. Never justify without hyphenation. No ALL CAPS beyond `--fs-micro` labels.

## 2. Colour tokens

Neutral, slightly warm paper with a single ink-blue accent. Every text pairing below was measured (WCAG contrast
ratio against `bg` / `surface`); keep it that way when adding tokens.

| Token | Light | Dark | Contrast (light / dark, vs bg) |
| --- | --- | --- | --- |
| `--color-bg` | `#FCFCFA` | `#0E1014` | – |
| `--color-surface` | `#F4F4F0` | `#171A20` | – |
| `--color-surface-raised` | `#FFFFFF` | `#1D2129` | – |
| `--color-text` | `#16181D` | `#E8E9EC` | 17.3 / 15.7 |
| `--color-text-muted` | `#4F5562` | `#A9AFBB` | 7.3 / 8.7 |
| `--color-text-subtle` | `#636A77` | `#8C93A1` | 5.3 / 6.2 (≥ 4.9 on surface) |
| `--color-border` | `#D9DBD6` | `#2A2F38` | decorative only |
| `--color-border-strong` | `#8A909B` | `#5E6573` | 3.1 / 3.3 (inputs, focus-adjacent UI) |
| `--color-accent` | `#1F4FD1` | `#7FA6FF` | 6.6 / 8.0 |
| `--color-on-accent` | `#FFFFFF` | `#0E1014` | 6.8 / 8.0 on accent |
| `--color-link` | `#1F4FD1` | `#8DB0FF` | 6.6 / 8.9 |
| `--color-success` | `#1A7F4B` | `#4CC38A` | 4.9 / 8.6 |
| `--color-warning` | `#9A5B00` | `#E8A93B` | 5.3 / 9.2 |
| `--color-danger` | `#C0262D` | `#FF7A7F` | 5.8 / 7.6 |
| `--color-focus` | `#1F4FD1` | `#7FA6FF` | 2 px outline + 2 px offset |

- Status is **never** conveyed by colour alone: pair with an icon/glyph and a word (`✓ Pass`, `▲ Merit`, `✕ Fail`).
- Grades: Fail = danger, Pass = success, Merit = accent, Distinction = `#6A3FC1` light / `#B79CFF` dark (≥ 4.5:1).
- Tinted backgrounds for callouts: the status colour at 8 % (light) / 14 % (dark) alpha over `bg`, text stays
  `--color-text`.
- Dark mode is a first-class theme, not an inversion: honour `prefers-color-scheme`, offer a toggle that persists
  in `localStorage` (no cookies), avoid pure `#000`/`#FFF` text on bg, reduce image brightness slightly
  (`filter: brightness(.92)`) only for photos, never for charts.
- Data-visualisation palette (colour-blind safe, Okabe–Ito), in order:
  `#0072B2 #E69F00 #009E73 #D55E00 #CC79A7 #56B4E9 #F0E442 #000000` (use `#E8E9EC` instead of black in dark).
  Sequential: viridis / cividis. Diverging: `RdBu` centred on a meaningful zero. Never rainbow/jet.

## 3. Space, layout, shape

- Spacing scale (rem): `0.25 0.5 0.75 1 1.5 2 3 4 6 8` as `--space-1 … --space-10`.
- Breakpoints: 480, 768, 1024, 1280 px. Mobile first. Content column 68ch, wide column 1100 px, page max 1280 px.
- Radii: `--radius-sm: 4px` (inputs, code), `--radius-md: 8px` (cards), `--radius-lg: 12px` (hero panels). No pills
  unless it is a tag.
- Elevation: borders before shadows. One shadow token: `0 1px 2px rgb(0 0 0 / .06), 0 4px 12px rgb(0 0 0 / .06)`
  (dark: rely on `--color-surface-raised` plus a 1 px border instead).
- Hit targets ≥ 44 × 44 px on touch, ≥ 24 × 24 px on pointer (WCAG 2.5.8).

## 4. Surface-specific guidance

**MkDocs Material site** (from S04): custom palette via `extra_css` mapping the tokens above onto
`--md-*` variables for both `scheme: default` and `scheme: slate`; self-hosted fonts (`theme.font: false`);
`navigation.instant`, `navigation.sections`, `content.code.copy`, `search.suggest`; Distill-style figure captions
(`<figure>` + numbered `<figcaption>`); KaTeX for maths; admonitions restyled to the callout tokens; no
Google Analytics or any analytics plugin.

**Grader report cards and dataset-doctor reports (HTML)**: single self-contained file (inline CSS/SVG, base64
posters for videos or relative paths beside it), opens offline, works without JavaScript (JS only enhances:
sorting, theme toggle). Layout: header with task, policy, date, overall grade badge and the headline metric with
its interval; then a summary row of 3–5 key numbers; then failure-taxonomy breakdown (horizontal bar chart with
intervals); then per-split tables; then failure videos as a grid with captions; then reproducibility block (seed,
versions, command) in mono. Include `@media print` styles (A4/Letter, no dark mode, page breaks between sections)
so a report prints as a clean portfolio PDF. Generate HTML from Jinja2 templates with autoescape on.

**Charts (matplotlib)**: one shared style module (`benchtop_core.style` or equivalent) applying the tokens: font
families as above with fallbacks, 10–11 pt labels, no top/right spines, light grid on y only, Okabe–Ito cycle,
`svg` for web and 2× PNG for raster, `bbox_inches="tight"`, units in axis labels, intervals as error bars or bands.
Every figure gets alt text.

**Rich CLI output**: semantic styles only (`success`, `warning`, `error`, `muted`, `accent`) defined once in a
theme; honour `NO_COLOR`, `FORCE_COLOR`, non-TTY (plain text, no spinners), and terminal width; tables with
right-aligned tabular numbers; errors say what happened, likely cause, next command (CLAUDE.md). No emoji except
the status glyphs `✓ ✕ ▲ •`. Output must stay readable on both dark and light terminals.

**Landing page**: same tokens; one clear headline, one-sentence value proposition, a real screenshot/GIF of a report
card, three proof points, a copy-paste install command, then links. No dark patterns, no trackers, no cookie banner
(because no cookies). Lighthouse ≥ 95 in Performance, Accessibility, Best Practices, SEO.

## 5. Accessibility (WCAG 2.2 AA, non-negotiable)

- Text contrast ≥ 4.5:1 (≥ 3:1 for ≥ 24 px or ≥ 18.66 px bold); UI components and chart marks ≥ 3:1.
- Semantic HTML first (`header`, `nav`, `main`, `figure`, `table` with `th scope`); one `h1`; no heading skips.
- Visible focus on every interactive element (`:focus-visible` outline using `--color-focus`); full keyboard use;
  skip-to-content link.
- `lang` on `<html>`; alt text for every image and chart (describe the finding, not the pixels); captions for videos.
- Reflow at 320 px wide without horizontal scrolling (tables scroll inside their own container).
- Respect `prefers-reduced-motion` and `prefers-color-scheme`.

## 6. Verification (do it, don't assume it)

When a session builds or changes UI, before finishing:
1. Render it. For HTML/docs: take screenshots at 375, 768 and 1280 px in light **and** dark (Playwright if
   available in the dev group; otherwise headless Chromium) and look at them. Fix what looks off.
2. Run an automated accessibility check (axe-core via Playwright, or `pa11y`) when the tools are available; zero
   serious/critical violations.
3. Add tests: template renders with autoescape, report HTML contains required landmarks/sections, theme tokens file
   matches this skill, contrast of token pairs ≥ thresholds (a tiny pure-Python WCAG contrast test), CLI output
   under `NO_COLOR` has no ANSI codes.
4. Check performance: report HTML < 1.5 MB without videos, no layout shift from fonts (size-adjusted fallbacks).
5. Record screenshots of notable UI in the PR description (never commit large binaries; keep committed images
   < 300 KB, optimised).

## 7. Review checklist (reviewer agents use this for any UI diff)

- [ ] Uses only the tokens above (no stray hex values, font sizes or spacing).
- [ ] Font pairing and type scale applied; prose measure 60–75ch; headings balanced; tabular numbers in tables.
- [ ] Typographic details correct (quotes, dashes, minus, units with non-breaking space).
- [ ] Light and dark themes both designed and checked; no unreadable chart or image in dark mode.
- [ ] Contrast meets AA for all text and ≥ 3:1 for UI/chart elements; status never colour-only.
- [ ] Keyboard navigable, visible focus, semantic landmarks, alt text, captions, `lang` set.
- [ ] Responsive at 320/375/768/1280 px; no horizontal page scroll.
- [ ] Charts: units, honest axes, uncertainty shown, colour-blind-safe palette, alt text.
- [ ] Works offline, no CDN fonts, no trackers/analytics, no cookies.
- [ ] Reduced motion respected; motion purposeful and short.
- [ ] CLI: honours NO_COLOR / non-TTY / width; semantic theme; readable errors.
- [ ] Screenshots (light + dark, mobile + desktop) were taken and inspected; a11y check run or its absence noted.
- [ ] Would this hold up next to a Distill.pub article or a Stanford/MIT lab project page? If not, it is not done.
