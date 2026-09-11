# Public documentation language switch

Status: implemented

The header offers Korean and English interface buttons. English remains the default and the canonical article language. Korean covers navigation, search controls and results labels, learning-path and topic introductions, reading stages, and diagram controls. Article titles, summaries, bodies, code, and diagrams retain their English source text; the Korean reader explicitly states that boundary. Translation runs locally from a bundled dictionary without an external service.

## Acceptance criteria

1. Both buttons remain visible and keyboard accessible on desktop and narrow mobile screens; `aria-pressed` identifies the active language and the root `lang` matches it.
2. Switching updates the current home, path, topic, document, or search view without changing the route or search input. Article text retains `lang="en"` and code remains unchanged.
3. The selected language survives reload through `docs-language` in local storage. Missing, invalid, or inaccessible storage falls back to English; switching still works in memory when storage writes fail.
4. All three paths and 21 topic introductions have Korean copy, while stable IDs, document membership, links, and the canonical catalog remain unchanged. Search still indexes the English article text.
5. Diagram expansion, zoom, close controls, theme changes, document navigation, and search work in both interfaces. Switching preserves the current scroll offset where the new layout permits it.
6. Build output includes the relative `assets/i18n.js` module. Existing explicitly selected, tracked-source publication and private-path rejection checks continue to pass.

## Verification

The site test suite covers translations, interpolation, fallback, persistence failures, catalog immutability, and the built module alongside existing publication and lab checks. Browser checks cover switching across routes, query preservation, reload, disabled storage, diagram controls, and mobile widths. Full article translation is outside this implementation.
