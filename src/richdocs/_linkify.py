"""On-page-markdown: auto-link inline ``code`` to mkdocstrings/autorefs targets.

Ported from the former ``docs/hooks/linkify_api_refs.py``. Uses the shared
:class:`~richdocs._symbol_index.SymbolIndex` to resolve identifiers, skipping
fenced code blocks and obvious non-symbols (paths, numbers, filenames).
"""

from __future__ import annotations

import re

from richdocs._symbol_index import SymbolIndex

_FENCED_BLOCK_RE = re.compile(r"(```[\s\S]*?```|~~~[\s\S]*?~~~)", re.MULTILINE)
_INLINE_CODE_RE = re.compile(r"(?<!\[)(`)([^`\n]+)\1(?!\])")
_SKIP_INLINE_RE = re.compile(r"[\s/\\]|\.(?:md|py|yaml|yml|npz|json|toml|txt)\b|^[0-9]+$")


class Linkifier:
    """Linkify inline code spans against a project's API symbol index."""

    def __init__(self, symbol_index: SymbolIndex) -> None:
        self._symbol_index = symbol_index
        self._index: tuple[dict[str, str], dict[str, str]] | None = None

    def _resolved_index(self) -> tuple[dict[str, str], dict[str, str]]:
        if self._index is None:
            self._index = self._symbol_index.build_autoref_index()
        return self._index

    def _linkify_segment(self, segment: str) -> str:
        by_id, by_short = self._resolved_index()

        def repl(match: re.Match[str]) -> str:
            inner = match.group(2)
            if _SKIP_INLINE_RE.search(inner):
                return match.group(0)
            target = self._symbol_index.resolve_identifier(inner, by_id, by_short)
            if not target:
                return match.group(0)
            return f"[`{inner}`][{target}]"

        return _INLINE_CODE_RE.sub(repl, segment)

    def linkify_markdown(self, markdown: str) -> str:
        parts = _FENCED_BLOCK_RE.split(markdown)
        for index, part in enumerate(parts):
            if index % 2 == 1:  # inside a fenced block
                continue
            parts[index] = self._linkify_segment(part)
        return "".join(parts)
