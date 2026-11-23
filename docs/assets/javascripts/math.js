// SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
// SPDX-License-Identifier: Apache-2.0
//
// Renders maths written as $...$ or $$...$$ (pymdownx.arithmatex, generic mode) with KaTeX. KaTeX itself is
// copied into the site at build time by the privacy plugin; nothing is fetched from a CDN at runtime.
// `document$` is Material's observable that fires on first load and after every instant navigation.
document$.subscribe(function renderMaths() {
  if (typeof katex === "undefined") {
    return;
  }
  document.querySelectorAll(".arithmatex").forEach(function render(element) {
    if (element.dataset.rendered === "true") {
      return;
    }
    const source = element.textContent.trim();
    const display = source.startsWith("\\[");
    const tex = source.replace(/^\\[([]/, "").replace(/\\[)\]]$/, "");
    katex.render(tex, element, { displayMode: display, throwOnError: false, output: "htmlAndMathml" });
    element.dataset.rendered = "true";
  });
});
