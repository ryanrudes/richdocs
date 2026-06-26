"""Post-build: index mkdocstrings API anchors for code-block hover/click nav.

Ported from the former ``docs/hooks/api_symbols.py``. Scans the built API pages
for anchor ids, picks a canonical page per symbol (via a nav-derived priority),
scrapes rich autoref tooltip titles, and writes ``javascripts/api-symbols.json``
for ``api-navigation.mjs`` to consume at runtime.
"""

from __future__ import annotations

import html
import json
import logging
import re
from collections.abc import Callable
from pathlib import Path

from richdocs._symbol_index import IndexSpec

log = logging.getLogger("mkdocs.plugins.richdocs")

_AUTOREF_TITLE_RE = re.compile(r'<a class="autorefs[^"]*" title="([^"]*)" href="[^"]*#([^"]+)"')


class ApiIndexer:
    """Builds the runtime API-symbol index from the rendered site."""

    def __init__(self, spec: IndexSpec, priority: Callable[[str], int]) -> None:
        self.spec = spec
        self.priority = priority
        prefix = re.escape(spec.id_prefix)
        self._anchor_re = re.compile(rf'\bid="({prefix}[^"]+)"')
        self._heading_title_re = re.compile(
            rf'<h[1-6] id="({prefix}[^"]+)" class="doc doc-heading"[^>]*>(.*?)</h[1-6]>',
            re.DOTALL,
        )

    # -- symbol classification -------------------------------------------

    def _is_primary_symbol(self, anchor_id: str) -> bool:
        if anchor_id == self.spec.id_prefix:
            return True
        if any(anchor_id.endswith(suffix) for suffix in self.spec.section_suffixes):
            return False
        return anchor_id.startswith(f"{self.spec.id_prefix}.")

    def _short_name(self, anchor_id: str) -> str | None:
        short = anchor_id.rsplit(".", 1)[-1]
        if short[0].isupper():
            return short
        if short in self.spec.lowercase_short_names:
            return short
        if "_" in short and short.islower():
            return short
        return None

    # -- tooltip scraping -------------------------------------------------

    @staticmethod
    def _normalize_heading_tooltip(inner: str) -> str:
        inner = re.sub(
            r'<a href="#[^"]*" class="headerlink"[^>]*>.*?</a>',
            "",
            inner,
            flags=re.DOTALL,
        )
        return re.sub(r"\s+", " ", inner).strip()

    def _scrape_tooltip_titles(self, site_dir: Path) -> dict[str, str]:
        """Rich autoref tooltip HTML (symbol-kind badge + name), keyed by anchor id."""
        titles: dict[str, str] = {}
        for html_path in site_dir.glob("**/*.html"):
            text = html_path.read_text(encoding="utf-8")
            for match in _AUTOREF_TITLE_RE.finditer(text):
                titles[match.group(2)] = html.unescape(match.group(1))
            if "/api/" not in html_path.as_posix():
                continue
            for match in self._heading_title_re.finditer(text):
                anchor_id = match.group(1)
                if anchor_id in titles:
                    continue
                inner = self._normalize_heading_tooltip(match.group(2))
                if "doc-symbol" in inner:
                    titles[anchor_id] = inner
        return titles

    # -- page scan --------------------------------------------------------

    def _scan_api_pages(self, site_dir: Path) -> tuple[dict[str, str], dict[str, str], set[str], dict[str, str]]:
        by_id: dict[str, tuple[str, int]] = {}
        by_short: dict[str, tuple[str, int, str]] = {}
        anchor_ids: set[str] = set()

        for html_path in sorted(site_dir.glob("api/**/index.html")):
            page_url = "/" + html_path.relative_to(site_dir).parent.as_posix() + "/"
            priority = self.priority(page_url)
            text = html_path.read_text(encoding="utf-8")

            for match in self._anchor_re.finditer(text):
                anchor_id = match.group(1)
                if not self._is_primary_symbol(anchor_id):
                    continue
                anchor_ids.add(anchor_id)

                href = f"{page_url}#{anchor_id}"
                existing = by_id.get(anchor_id)
                if existing is None or priority < existing[1]:
                    by_id[anchor_id] = (href, priority)

                short = self._short_name(anchor_id)
                if short is None:
                    continue
                existing_short = by_short.get(short)
                if existing_short is None or priority < existing_short[1]:
                    by_short[short] = (href, priority, anchor_id)

        titles = self._scrape_tooltip_titles(site_dir)
        return (
            {key: href for key, (href, _) in by_id.items()},
            {key: href for key, (href, _, _) in by_short.items()},
            anchor_ids,
            titles,
        )

    # -- output -----------------------------------------------------------

    def write_symbol_index(self, site_dir: Path) -> set[str]:
        """Write ``javascripts/api-symbols.json``; return the indexed anchor ids."""
        by_id, by_short, anchor_ids, titles = self._scan_api_pages(site_dir)

        titles_by_short: dict[str, str] = {}
        for short, href in by_short.items():
            anchor_id = href.split("#", 1)[-1]
            if anchor_id in titles:
                titles_by_short[short] = titles[anchor_id]

        payload = {
            "version": 2,
            "byId": by_id,
            "byShortName": by_short,
            "titles": titles,
            "titlesByShortName": titles_by_short,
        }
        encoded = json.dumps(payload, separators=(",", ":"))

        out_path = site_dir / "javascripts" / "api-symbols.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(encoded, encoding="utf-8")

        log.info(
            "richdocs API symbol index: %d anchors, %d tooltip titles",
            len(by_id),
            len(titles),
        )
        return anchor_ids
