"""Derive canonical-page priorities for API symbols from the mkdocs ``nav``.

When a symbol is documented on several API pages, the indexer keeps the one with
the lowest priority number. Instead of a hand-tuned per-URL table, the priority
is derived from nav order (earlier pages preferred), with the full ``reference``
page kept as the least-preferred fallback. Projects can still pin specific pages
via ``api.page_priority_overrides``.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

# Priority constants (lower = preferred as the canonical page).
_REFERENCE_PRIORITY = 100  # the giant full-reference dump: last resort
_API_INDEX_PRIORITY = 90  # the /api/ landing page
_FIRST_PAGE_PRIORITY = 60  # first curated api page in nav order
_DEFAULT_PRIORITY = 50  # not in nav / unknown


def _iter_doc_urls(nav: Any) -> list[str]:
    """Flatten a mkdocs ``nav`` structure into an ordered list of doc paths."""
    urls: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, str):
            urls.append(node)
        elif isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, dict):
            for value in node.values():
                walk(value)

    walk(nav)
    return urls


def _doc_to_url_suffix(doc_path: str) -> str:
    """``api/models.md`` → ``/api/models/`` (matches built page URLs)."""
    path = doc_path.rsplit(".", 1)[0]  # strip extension
    if path.endswith("/index"):
        path = path[: -len("/index")]
    elif path == "index":
        path = ""
    return "/" + path.strip("/") + "/" if path else "/"


def build_priority_resolver(nav: Any, overrides: dict[str, int]) -> Callable[[str], int]:
    """Return ``priority(page_url) -> int`` from nav order + explicit overrides.

    ``overrides`` maps a URL suffix (e.g. ``/api/models/``) to a priority; the
    longest matching suffix wins, so ``/api/`` never shadows ``/api/models/``.
    """
    derived: dict[str, int] = {}
    position = 0
    for doc in _iter_doc_urls(nav):
        suffix = _doc_to_url_suffix(doc)
        if "/api/" not in suffix and not suffix.endswith("/api/"):
            continue
        if suffix.endswith("/reference/"):
            derived[suffix] = _REFERENCE_PRIORITY
        elif suffix.endswith("/api/"):
            derived[suffix] = _API_INDEX_PRIORITY
        else:
            derived.setdefault(suffix, _FIRST_PAGE_PRIORITY + position)
            position += 1

    # Overrides win; check longest (most specific) suffix first.
    override_suffixes = sorted(overrides, key=len, reverse=True)

    def priority(page_url: str) -> int:
        for suffix in override_suffixes:
            if page_url.endswith(suffix):
                return int(overrides[suffix])
        for suffix in sorted(derived, key=len, reverse=True):
            if page_url.endswith(suffix):
                return derived[suffix]
        return _DEFAULT_PRIORITY

    return priority
