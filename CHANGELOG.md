# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.1] - 2026-06-26

### Fixed

- Inline API-symbol mentions (autoref links) now have a clear **navigable
  affordance** — accent color + a dotted underline (with a hover/focus state) —
  so it's obvious you can click through to the reference.
- Shiki no longer re-highlights code **inside links**, which had masked the
  symbol-link styling.
- The plugin auto-enables Material's **`content.tooltips`** (when `api_hover` is
  on), so the rich hover tooltips on API symbols work without extra config (this
  was missing on the bundled demo site).

[0.4.1]: https://github.com/ryanrudes/richdocs/releases/tag/v0.4.1

## [0.4.0] - 2026-06-26

### Changed

- **Pyodide now runs in a Web Worker** (off the main thread), so executing a
  block no longer blocks the page; output streams back as it's produced.
- The header status bar shows a dedicated **"Python · browser"** indicator (and
  "Loading Python…" during the first WASM load) when the browser runtime is
  active, instead of the Jupyter "Not running" state.

[0.4.0]: https://github.com/ryanrudes/richdocs/releases/tag/v0.4.0

## [0.3.1] - 2026-06-26

### Changed

- `live_code.runtime` now defaults to **`jupyter`** (was `auto`). Web execution
  (`pyodide`/`auto`) is opt-in, because Pyodide can't import a project's own
  (non-WASM) package — an `auto` default would make `import yourpkg` blocks error
  on published sites. The bundled demo opts into `auto` to showcase it.

### Added

- First-run loading notice for the Pyodide runtime (the multi-MB WASM download no
  longer looks frozen).

[0.3.1]: https://github.com/ryanrudes/richdocs/releases/tag/v0.3.1

## [0.3.0] - 2026-06-26

### Added

- **In-browser live code via Pyodide** — `live_code.runtime: auto | jupyter |
  pyodide`. `pyodide` runs Python in the browser (WebAssembly), so runnable
  blocks work on a published static site with no server; `auto` uses Jupyter when
  reachable and falls back to Pyodide. Configure WASM-wheel packages via
  `live_code.pyodide.packages`. (Python only; shell blocks need Jupyter.)
- **`symbols.decorator_labels`** — rewrite the text of mkdocstrings decorator
  labels (`property` → `prop`, …) via a build-time pass, in headings and the TOC.

[0.3.0]: https://github.com/ryanrudes/richdocs/releases/tag/v0.3.0

## [0.2.0] - 2026-06-26

Deep configurability for badges, linking, and highlighting. All additions are
override-only — defaults reproduce the 0.1.0 look exactly.

### Added

- **`symbols.labels`** — relabel any API symbol-kind badge (`class` → `def` /
  `dataclass` / `enum` / `member` / anything) in both headings and the TOC.
- **`symbols.colors`** — set `{fg, bg}` per kind; also recolors the decorator
  labels that map to a kind (e.g. `property` follows `attribute`).
- **`api.linkify`** — `short_names`, `dotted`, `skip_extensions`, and custom
  `aliases` (map an arbitrary word to a symbol) for both prose and code-block
  linking.
- **`theme.highlight`** — Shiki `theme`, `inline`, `default_language`,
  `languages`, and `aliases`.
- **`toc`** — `collapse_default` and `scrollspy_offset`.

[0.2.0]: https://github.com/ryanrudes/richdocs/releases/tag/v0.2.0

## [0.1.0] - 2026-06-26

Initial release. richdocs began as the bespoke docs machinery of the
[retarget](https://github.com/ryanrudes/retarget) project and was extracted into
a standalone, configurable MkDocs Material plugin.

### Added

- Single `richdocs` MkDocs plugin entry point that wires up the whole experience
  (no manual `extra_css` / `extra_javascript` / `custom_templates`).
- Typed, validated config schema (`api`, `live_code`, `theme`, `features`);
  only `package` is required.
- Shiki syntax highlighting (default theme: VS Code "Shades of Purple") for code
  blocks and inline code.
- Runnable live-code blocks backed by a local Jupyter kernel (dev only).
- API-symbol hover tooltips + click-to-navigate in code blocks, and automatic
  linking of inline `` `Symbol` `` mentions to the mkdocstrings reference.
- mkdocstrings template overrides: enums render as `enum` / `member`; decorator
  badges (`property`, `classmethod`, …) in headings and the TOC.
- Collapsible in-page TOC sections and a scroll-spy tuned for long API pages.
- Themeable palette via `theme.palette` (friendly keys or raw `--rd-*` tokens),
  generated into a stylesheet at build time.
- Canonical API page derived from nav order, with `page_priority_overrides`.

### Fixed

- API-symbol hover state is reset on Material instant navigation (stale hover /
  orphaned tooltips after navigating between pages).
- Inline-link short-name tie-breaks are now deterministic across builds.

[Unreleased]: https://github.com/ryanrudes/richdocs/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/ryanrudes/richdocs/releases/tag/v0.1.0
