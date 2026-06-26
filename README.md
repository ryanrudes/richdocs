<div align="center">

# richdocs

**A batteries-included documentation experience for [MkDocs Material](https://squidfunk.github.io/mkdocs-material/).**

Shiki syntax highlighting · runnable live code · API-symbol hover & auto-linking · mkdocstrings enum/decorator badges · a polished collapsible TOC — all from a single plugin entry.

[![PyPI](https://img.shields.io/pypi/v/richdocs.svg)](https://pypi.org/project/richdocs/)
[![Python](https://img.shields.io/pypi/pyversions/richdocs.svg)](https://pypi.org/project/richdocs/)
[![CI](https://github.com/ryanrudes/richdocs/actions/workflows/ci.yml/badge.svg)](https://github.com/ryanrudes/richdocs/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

[**Live demo →**](https://ryanrudes.github.io/richdocs/)

</div>

---

## Why

MkDocs Material is excellent, but a *great* API-docs site usually means hand-wiring a pile of hooks, JavaScript, CSS, and mkdocstrings template overrides — and then re-doing it for the next project. **richdocs** packages that whole experience into one configurable plugin. The default look is the VS Code **"Shades of Purple"** theme; everything is overridable.

## Features

- 🎨 **Shiki syntax highlighting** — VS Code-accurate highlighting at runtime (the default theme is *Shades of Purple*), in both code blocks and inline code.
- ▶️ **Runnable live code** — execute Python/shell blocks against a local Jupyter kernel, right in the page (dev only).
- 🔗 **API-symbol hover & auto-linking** — inline `` `Symbol` `` mentions link to your mkdocstrings reference automatically, and hovering symbols in code blocks shows rich tooltips; click to jump.
- 🏷️ **Smarter mkdocstrings rendering** — enums render as `enum` / `member`, and headings & the TOC show decorator badges (`property`, `classmethod`, …).
- 🧭 **Polished TOC** — scroll-spy tuned for long API pages, plus collapsible sections that expand on demand.
- 🌈 **One dark palette, fully themeable** — override any color or the Shiki theme from `mkdocs.yml`.

## Install

```bash
pip install richdocs
```

`richdocs` pulls in `mkdocs-material` and `mkdocstrings[python]`, so that's all you need.

## Quickstart

Add the plugin to `mkdocs.yml` — the only required option is the package you're documenting:

```yaml
theme:
  name: material
  palette:
    scheme: slate          # richdocs ships a single dark scheme

plugins:
  - search
  - richdocs:              # ← list BEFORE mkdocstrings
      package: your_package
  - mkdocstrings:
      handlers:
        python:
          paths: [src]
```

That's it. The plugin registers its stylesheets/scripts, points mkdocstrings at its templates, indexes your API, and serves the Shiki theme — no `extra_css` / `extra_javascript` / `custom_templates` plumbing required.

> **Ordering:** list `richdocs` **before** `mkdocstrings` so its enum/badge templates take effect.

## Configuration

Everything except `package` is optional and has sensible defaults:

```yaml
plugins:
  - richdocs:
      package: your_package        # required: the Python package to document & index

      api:
        id_prefix: your_package     # mkdocstrings anchor prefix (default: = package)
        # When a symbol is documented on several pages, the canonical page is
        # derived from nav order; pin specific pages here if needed:
        page_priority_overrides: {}            # {"/api/reference/": 100, ...}
        registry_exports: {}                   # {name: "pkg.module.singleton"} for registry-style singletons
        ambiguous_short_names: []              # short names to never auto-link
        prefer_class_for_short: {}             # {short_name: ClassName} to disambiguate
        short_name_blocklist: []
        extra_modules: []                      # extra submodules whose __all__ to index
        section_suffixes: ["-functions", "-attributes", "-classes"]

      live_code:                                # runnable code blocks (dev only)
        enabled: true
        jupyter_url: http://127.0.0.1:8888/
        token: your_package-docs                # default: <package>-docs
        launcher_port: 8889
        launcher_script: scripts/docs-jupyter.sh # script that starts Jupyter
        kernel: python3
        runnable_languages: [python, bash]

      theme:
        shiki_theme: shades-of-purple           # bundled id, or path to a Shiki theme JSON
        palette: {}                             # override any color (see below)
        layout: {}                              # TOC spacing tokens

      features:                                 # turn pieces on/off
        shiki: true
        api_hover: true
        linkify_inline_code: true
        toc_collapsible: true
        toc_scrollspy: true
        hide_empty_toc: true
```

### Theming

Override individual palette colors with friendly keys (or any raw `--rd-*` CSS custom property):

```yaml
plugins:
  - richdocs:
      package: your_package
      theme:
        palette:
          page_bg: "#1e1e3f"
          code_bg: "#2d2b55"
          sidebar_bg: "#222244"
          gold: "#fad000"          # accent
          purple_bright: "#b362ff" # links
          # ...or a raw token:
          "--rd-text-muted": "#a599e9"
```

Supported friendly keys: `page_bg`, `sidebar_bg`, `code_bg`, `code_fg`, `surface_1`–`surface_4`, `text`, `text_muted`, `text_soft`, `purple`, `purple_bright`, `gold`/`accent`, `enum_fg`/`enum_bg`, `member_fg`/`member_bg`, and the TOC layout tokens `toc_row_gap`, `toc_branch_gap`, `toc_section_gap`, `toc_link_min_height`.

## How it works

A single `RichDocsPlugin` (MkDocs entry point) replaces what used to be four build hooks plus scattered asset wiring:

| Event | What it does |
| --- | --- |
| `on_config` | validates config, derives defaults, registers bundled CSS/JS, points mkdocstrings at the templates |
| `on_files` | emits `richdocs-config.js` (`window.__richdocsConfig`, read by the JS) and `richdocs-palette.css` (your overrides) |
| `on_page_markdown` | auto-links inline `` `Symbol` `` mentions to the API reference |
| `on_post_build` | scans the built site to index API anchors (`javascripts/api-symbols.json`) and injects decorator badges into the TOC |
| `on_serve` | runs a tiny local helper so the page can launch Jupyter for live code |

## Requirements

- Python 3.11+
- MkDocs Material 9.5+
- mkdocstrings[python] 0.25+ (for the API features)

## Development

```bash
git clone https://github.com/ryanrudes/richdocs
cd richdocs
uv venv && uv pip install -e ".[dev]"
uv run pytest        # unit tests
uv run ruff check .  # lint
```

## License

[Apache-2.0](LICENSE) © Ryan Rudes
