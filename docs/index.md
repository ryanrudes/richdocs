# richdocs

A **batteries-included documentation experience** for [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) — Shiki syntax highlighting, runnable live code, API-symbol hover & auto-linking, mkdocstrings enum/decorator badges, and a polished collapsible TOC, all from a single plugin entry.

This site is itself built with richdocs.

!!! tip "One plugin, the whole experience"
    No hand-wiring `extra_css`, `extra_javascript`, or `custom_templates`. Add
    `richdocs` to `plugins:` and point it at your package.

## Install

```bash
pip install richdocs
```

## Quickstart

```yaml
# mkdocs.yml
theme:
  name: material
  palette:
    scheme: slate

plugins:
  - search
  - richdocs:            # list BEFORE mkdocstrings
      package: your_package
  - mkdocstrings:
      handlers:
        python:
          paths: [src]
```

The plugin's configuration is the [`RichDocsPlugin`][richdocs.RichDocsPlugin] entry
point — see the [API reference](api.md) and the full [configuration guide](configuration.md).

## What you get

=== "Highlighted code"

    ```python
    from dataclasses import dataclass

    @dataclass
    class Widget:
        """A small widget."""
        size: int = 1

        def grow(self, by: int) -> "Widget":
            return Widget(self.size + by)
    ```

=== "Runnable live code"

    Click **▶ Run** below — on this published site it executes **in your browser**
    via Pyodide (WebAssembly), no server needed. The first run downloads the
    Python runtime, so give it a few seconds.

    ```python
    import sys
    print("hello from richdocs")
    print("running", sys.version.split()[0], "in the browser via Pyodide")
    ```

=== "Auto-linked prose"

    Mentions of API symbols like `RichDocsPlugin` in prose become links to the
    reference automatically — no manual cross-references.

## Highlights

- 🎨 VS Code-accurate **Shades of Purple** highlighting (Shiki), themeable.
- 🔗 Inline `` `Symbol` `` auto-linking + hover tooltips in code blocks.
- 🏷️ Enums render as `enum` / `member`; decorator badges in headings & TOC.
- 🧭 Scroll-spy + collapsible TOC tuned for long API pages.
- ⚙️ Typed, validated config — only `package` is required.
