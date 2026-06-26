# Configuration

richdocs is configured under the `richdocs` key in `mkdocs.yml`. Every option
except `package` is optional and has a sensible default.

```yaml
plugins:
  - richdocs:
      package: your_package        # required: the package to document & index

      api:
        id_prefix: your_package     # mkdocstrings anchor prefix (default: = package)
        page_priority_overrides: {} # pin canonical pages, e.g. {"/api/reference/": 100}
        registry_exports: {}        # {name: "pkg.module.singleton"}
        ambiguous_short_names: []   # short names to never auto-link
        prefer_class_for_short: {}  # {short_name: ClassName}
        short_name_blocklist: []
        extra_modules: []           # extra submodules whose __all__ to index
        section_suffixes: ["-functions", "-attributes", "-classes"]

      live_code:                    # runnable code blocks (dev only)
        enabled: true
        jupyter_url: http://127.0.0.1:8888/
        token: your_package-docs    # default: <package>-docs
        launcher_port: 8889
        launcher_script: scripts/docs-jupyter.sh
        kernel: python3
        runnable_languages: [python, bash]

      theme:
        shiki_theme: shades-of-purple
        palette: {}                 # override colors (see below)
        layout: {}                  # TOC spacing tokens

      features:
        shiki: true
        api_hover: true
        linkify_inline_code: true
        toc_collapsible: true
        toc_scrollspy: true
        hide_empty_toc: true
```

## Theming

Override palette colors with friendly keys, or any raw `--rd-*` custom property:

```yaml
plugins:
  - richdocs:
      package: your_package
      theme:
        palette:
          page_bg: "#1e1e3f"
          code_bg: "#2d2b55"
          gold: "#fad000"           # accent
          purple_bright: "#b362ff"  # links
          "--rd-text-muted": "#a599e9"   # raw token
```

| Friendly key | Sets |
| --- | --- |
| `page_bg`, `sidebar_bg`, `code_bg`, `code_fg` | core backgrounds / code text |
| `surface_1`–`surface_4` | elevated surfaces |
| `text`, `text_muted`, `text_soft` | text colors |
| `purple`, `purple_bright`, `gold` / `accent` | accents & links |
| `enum_fg`/`enum_bg`, `member_fg`/`member_bg` | mkdocstrings badge colors |
| `toc_row_gap`, `toc_branch_gap`, `toc_section_gap`, `toc_link_min_height` | TOC spacing |

!!! note "Plugin order"
    List `richdocs` **before** `mkdocstrings` so its enum/badge templates apply.
