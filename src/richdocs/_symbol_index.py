"""Build API symbol ids for autorefs / api-navigation (config-driven).

Ported from the former ``docs/hooks/symbol_index.py``. The hard-coded ``retarget``
constants now live on an :class:`IndexSpec` supplied by the plugin, so the same
engine indexes any package.
"""

from __future__ import annotations

import importlib
import inspect
import json
import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger("mkdocs.plugins.richdocs")


@dataclass(frozen=True)
class IndexSpec:
    """Everything the indexer needs to know about one project's API surface."""

    package: str
    id_prefix: str
    cache_path: Path
    registry_exports: dict[str, str] = field(default_factory=dict)
    ambiguous_short_names: frozenset[str] = frozenset()
    prefer_class_for_short: dict[str, str] = field(default_factory=dict)
    short_name_blocklist: frozenset[str] = frozenset()
    lowercase_short_names: frozenset[str] = frozenset()
    extra_modules: tuple[str, ...] = ()
    section_suffixes: tuple[str, ...] = ("-functions", "-attributes", "-classes")

    @property
    def package_prefixes(self) -> tuple[str, ...]:
        return (f"{self.id_prefix}.",)


class SymbolIndex:
    """Resolve identifiers to mkdocstrings anchor ids for a given package."""

    def __init__(self, spec: IndexSpec) -> None:
        self.spec = spec

    # -- module introspection (conservative fallback) ---------------------

    def _import_package(self) -> object | None:
        try:
            return importlib.import_module(self.spec.package)
        except ImportError as exc:  # pragma: no cover - depends on env
            log.warning(
                "richdocs: could not import package %r for the conservative API index: %s",
                self.spec.package,
                exc,
            )
            return None

    def _qualname(self, obj: object) -> str | None:
        package = self.spec.package
        if inspect.ismodule(obj):
            name = getattr(obj, "__name__", "")
            return name if name.startswith(package) else None
        module = getattr(obj, "__module__", None)
        qual = getattr(obj, "__qualname__", None)
        if not module or not qual or not str(module).startswith(package):
            return None
        return f"{module}.{qual}"

    def _export_entries(self) -> list[tuple[str, bool]]:
        entries: list[tuple[str, bool]] = []
        module = self._import_package()
        if module is None:
            return entries
        prefix = self.spec.id_prefix
        for name in getattr(module, "__all__", ()):
            obj = getattr(module, name)
            canonical = self._qualname(obj) or self.spec.registry_exports.get(name)
            if canonical:
                entries.append((canonical, True))
            if name not in self.spec.registry_exports:
                entries.append((f"{prefix}.{name}", True))
        for mod_path in self.spec.extra_modules:
            try:
                submod = importlib.import_module(mod_path)
            except ImportError:  # pragma: no cover - depends on env
                continue
            for name in getattr(submod, "__all__", ()):
                obj = getattr(submod, name)
                full = self._qualname(obj)
                if full:
                    entries.append((full, True))
        return entries

    # -- short-name ranking ----------------------------------------------

    def _short_name(self, anchor_id: str) -> str | None:
        short = anchor_id.rsplit(".", 1)[-1]
        if short in self.spec.ambiguous_short_names or short in self.spec.short_name_blocklist:
            return None
        if short[0].isupper():
            return short
        if short in self.spec.lowercase_short_names:
            return short
        if "_" in short and short.islower():
            return short
        return None

    def _register_short(
        self,
        by_short: dict[str, str],
        rank: dict[str, tuple[int, int]],
        anchor_id: str,
    ) -> None:
        short = self._short_name(anchor_id)
        if short is None:
            return
        depth = len(anchor_id.split("."))
        preferred = self.spec.prefer_class_for_short.get(short)
        if preferred and f".{preferred}." in anchor_id:
            tier = 0
        elif preferred:
            tier = 1
        else:
            tier = 0
        priority = (tier, depth)
        if short in rank and rank[short] <= priority:
            return
        rank[short] = priority
        by_short[short] = anchor_id

    # -- index builders ---------------------------------------------------

    def build_conservative_index(self) -> tuple[dict[str, str], dict[str, str]]:
        """First-build fallback: top-level exports + extra-module helpers only."""
        by_id: dict[str, str] = {}
        by_short: dict[str, str] = {}
        rank: dict[str, tuple[int, int]] = {}
        prefix = f"{self.spec.id_prefix}."
        for full_id, _exported in self._export_entries():
            if not full_id.startswith(prefix):
                continue
            by_id[full_id] = full_id
            self._register_short(by_short, rank, full_id)
        return by_id, by_short

    def build_index_from_anchor_ids(self, anchor_ids: set[str]) -> tuple[dict[str, str], dict[str, str]]:
        by_id = {anchor_id: anchor_id for anchor_id in sorted(anchor_ids)}
        by_short: dict[str, str] = {}
        rank: dict[str, tuple[int, int]] = {}
        # Iterate in sorted order so short-name tie-breaks are deterministic
        # across builds (a Python set's iteration order varies by hash seed).
        for anchor_id in sorted(anchor_ids):
            self._register_short(by_short, rank, anchor_id)

        # Resolve any short names that map to several anchors via the
        # prefer-class hint; otherwise drop them.
        collisions: dict[str, list[str]] = defaultdict(list)
        for short, full in list(by_short.items()):
            collisions[short].append(full)
        for short, ids in collisions.items():
            unique = list(dict.fromkeys(ids))
            if len(unique) == 1:
                continue
            preferred = self.spec.prefer_class_for_short.get(short)
            if preferred:
                matches = [item for item in unique if f".{preferred}." in item or item.endswith(f".{preferred}")]
                if matches:
                    by_short[short] = matches[0]
                    continue
            del by_short[short]
        return by_id, by_short

    # -- anchor-id cache --------------------------------------------------

    def load_cached_anchor_ids(self) -> set[str] | None:
        if not self.spec.cache_path.is_file():
            return None
        try:
            payload = json.loads(self.spec.cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if not isinstance(payload, list):
            return None
        prefixes = self.spec.package_prefixes
        return {item for item in payload if isinstance(item, str) and item.startswith(prefixes)}

    def write_anchor_cache(self, anchor_ids: set[str]) -> None:
        self.spec.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.spec.cache_path.write_text(
            json.dumps(sorted(anchor_ids), indent=0),
            encoding="utf-8",
        )

    def build_autoref_index(self) -> tuple[dict[str, str], dict[str, str]]:
        cached = self.load_cached_anchor_ids()
        if cached:
            return self.build_index_from_anchor_ids(cached)
        return self.build_conservative_index()

    # -- identifier resolution -------------------------------------------

    def resolve_identifier(self, text: str, by_id: dict[str, str], by_short: dict[str, str]) -> str | None:
        if text in by_id:
            return text
        if not re.fullmatch(r"[A-Za-z_][\w.]*", text):
            return None
        if text in by_short:
            return by_short[text]
        if "." in text and text.startswith(self.spec.package_prefixes):
            return by_id.get(text)
        return None
