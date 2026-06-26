"""The ``richdocs`` MkDocs plugin.

Folds the former ``docs/hooks/*.py`` into one config-driven plugin and registers
all bundled assets (JS, CSS, mkdocstrings templates, Shiki theme) so a downstream
project enables the whole experience with a single ``plugins: [richdocs]`` entry.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from mkdocs.exceptions import ConfigurationError
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import File, Files

from richdocs import _jupyter
from richdocs._api_index import ApiIndexer
from richdocs._assets import (
    CONFIG_JS_URI,
    PALETTE_CSS_URI,
    SYMBOLS_CSS_URI,
    bundled_static_files,
    generate_config_js,
    generate_symbols_css,
    generate_theme_overrides_css,
    register_static_assets,
    set_mkdocstrings_templates,
)
from richdocs._config import RichDocsConfig
from richdocs._jupyter import JupyterLauncher
from richdocs._linkify import Linkifier
from richdocs._nav_priority import build_priority_resolver
from richdocs._symbol_index import IndexSpec, SymbolIndex
from richdocs._toc_labels import relabel_decorator_labels, sync_toc_labels

log = logging.getLogger("mkdocs.plugins.richdocs")

#: Directory holding the bundled front-end assets (javascripts/, stylesheets/,
#: templates/, themes/). Resolved relative to this installed package so it works
#: for both editable and wheel installs.
ASSETS_DIR = Path(__file__).resolve().parent / "assets"


class RichDocsPlugin(BasePlugin[RichDocsConfig]):
    """Batteries-included Shades-of-Purple docs experience for MkDocs Material."""

    def __init__(self) -> None:
        self._symbol_index: SymbolIndex | None = None
        self._linkifier: Linkifier | None = None
        self._api_indexer: ApiIndexer | None = None
        self._launcher: JupyterLauncher | None = None
        self._config_js: str = ""
        self._palette_css: str = ""
        self._symbols_css: str = ""

    # -- configuration ----------------------------------------------------

    def on_startup(self, *, command: str, dirty: bool) -> None:
        _jupyter.note_command(command)

    def on_config(self, config: Any) -> Any:
        package = self.config.package.strip()
        if not package:
            raise ConfigurationError(
                "richdocs: 'package' is required — set it to the Python package to "
                "document and index, e.g.\n    plugins:\n      - richdocs:\n          package: your_package"
            )
        self._warn_if_after_mkdocstrings(config)

        api = self.config.api
        id_prefix = (api.id_prefix or package).strip()
        token = self.config.live_code.token or f"{package}-docs"
        project_dir = self._project_dir(config)

        lowercase = frozenset(api.registry_exports) | frozenset(api.extra_short_names)
        spec = IndexSpec(
            package=package,
            id_prefix=id_prefix,
            cache_path=project_dir / ".richdocs-cache" / "api-anchor-ids.json",
            registry_exports=dict(api.registry_exports),
            ambiguous_short_names=frozenset(api.ambiguous_short_names),
            prefer_class_for_short=dict(api.prefer_class_for_short),
            short_name_blocklist=frozenset(api.short_name_blocklist),
            lowercase_short_names=lowercase,
            extra_modules=tuple(api.extra_modules),
            section_suffixes=tuple(api.section_suffixes),
        )
        self._symbol_index = SymbolIndex(spec)
        link = api.linkify
        self._linkifier = (
            Linkifier(
                self._symbol_index,
                skip_extensions=tuple(link.skip_extensions),
                link_short_names=bool(link.short_names),
                link_dotted=bool(link.dotted),
                aliases=dict(link.aliases),
            )
            if self.config.features.linkify_inline_code
            else None
        )
        overrides = {k: int(v) for k, v in api.page_priority_overrides.items()}
        priority = build_priority_resolver(config.get("nav"), overrides)
        self._api_indexer = ApiIndexer(spec, priority)

        live = self.config.live_code
        if live.enabled:
            script = (project_dir / live.launcher_script).resolve() if live.launcher_script else None
            self._launcher = JupyterLauncher(
                jupyter_url=live.jupyter_url,
                token=token,
                launcher_port=live.launcher_port,
                launcher_script=script,
                cwd=project_dir,
            )

        self._config_js = generate_config_js(self.config, id_prefix=id_prefix, token=token, assets_dir=ASSETS_DIR)
        self._palette_css = generate_theme_overrides_css(self.config)
        self._symbols_css = generate_symbols_css(self.config)

        register_static_assets(config, self.config)
        set_mkdocstrings_templates(config, ASSETS_DIR)
        return config

    # -- files ------------------------------------------------------------

    def on_files(self, files: Files, config: Any) -> Files:
        bundled = [
            *bundled_static_files(ASSETS_DIR, config),
            File.generated(config, CONFIG_JS_URI, content=self._config_js),
            File.generated(config, PALETTE_CSS_URI, content=self._palette_css),
            File.generated(config, SYMBOLS_CSS_URI, content=self._symbols_css),
        ]
        for file in bundled:
            # Plugin assets win over any same-named project file (e.g. before the
            # project removes its own copies). Remove-before-append per the
            # MkDocs Files API to avoid a DeprecationWarning.
            existing = files.get_file_from_path(file.src_uri)
            if existing is not None:
                files.remove(existing)
            files.append(file)
        return files

    # -- markdown ---------------------------------------------------------

    def on_page_markdown(self, markdown: str, *, page: Any, config: Any, files: Any) -> str:
        if self._linkifier is None:
            return markdown
        if not str(getattr(page.file, "src_path", "")).endswith(".md"):
            return markdown
        return self._linkifier.linkify_markdown(markdown)

    # -- post build -------------------------------------------------------

    def on_post_build(self, *, config: Any) -> None:
        site_dir = Path(config["site_dir"])
        if self.config.features.api_hover and self._api_indexer and self._symbol_index:
            anchor_ids = self._api_indexer.write_symbol_index(site_dir)
            self._symbol_index.write_anchor_cache(anchor_ids)
        sync_toc_labels(site_dir)
        # Relabel decorator-label text after the TOC mirror so both are rewritten.
        relabel_decorator_labels(site_dir, dict(self.config.symbols.decorator_labels))
        if self._launcher:
            self._launcher.on_post_build()

    # -- live-code dev server --------------------------------------------

    def on_serve(self, server: Any, *, config: Any, builder: Any) -> Any:
        if self._launcher:
            return self._launcher.on_serve(server)
        return server

    def on_shutdown(self) -> None:
        if self._launcher:
            self._launcher.on_shutdown()

    # -- helpers ----------------------------------------------------------

    @staticmethod
    def _project_dir(config: Any) -> Path:
        config_file = config.get("config_file_path")
        if config_file:
            return Path(config_file).resolve().parent
        return Path(config["docs_dir"]).resolve().parent

    @staticmethod
    def _warn_if_after_mkdocstrings(config: Any) -> None:
        names = list(config["plugins"].keys())
        if "mkdocstrings" in names and "richdocs" in names and names.index("richdocs") > names.index("mkdocstrings"):
            log.warning(
                "richdocs: list the 'richdocs' plugin BEFORE 'mkdocstrings' in mkdocs.yml "
                "so its enum/decorator-badge templates take effect."
            )
