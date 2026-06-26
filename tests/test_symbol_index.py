"""Tests for the config-driven API symbol index engine."""

from __future__ import annotations

from richdocs._symbol_index import IndexSpec, SymbolIndex


def _spec(tmp_path, **kw) -> IndexSpec:
    return IndexSpec(package="pkg", id_prefix="pkg", cache_path=tmp_path / "c.json", **kw)


def test_short_name_heuristics(tmp_path):
    si = SymbolIndex(
        _spec(
            tmp_path,
            ambiguous_short_names=frozenset({"State"}),
            short_name_blocklist=frozenset({"name"}),
            lowercase_short_names=frozenset({"robots"}),
        )
    )
    assert si._short_name("pkg.Robot") == "Robot"  # CapWords
    assert si._short_name("pkg.load_motion") == "load_motion"  # snake_case
    assert si._short_name("pkg.robots") == "robots"  # allow-listed lowercase
    assert si._short_name("pkg.State") is None  # ambiguous
    assert si._short_name("pkg.name") is None  # blocklisted
    assert si._short_name("pkg.lower") is None  # bare lowercase, not allow-listed


def test_index_is_deterministic_and_rank_breaks_ties(tmp_path):
    si = SymbolIndex(_spec(tmp_path))
    anchors = {"pkg.A", "pkg.mod.A", "pkg.b_func"}
    a = si.build_index_from_anchor_ids(anchors)
    b = si.build_index_from_anchor_ids(set(anchors))
    assert a == b  # deterministic regardless of set ordering
    by_id, by_short = a
    assert by_id == {x: x for x in anchors}
    assert by_short["A"] == "pkg.A"  # shallower depth wins the tie
    assert by_short["b_func"] == "pkg.b_func"


def test_prefer_class_for_short(tmp_path):
    # Only indexable short names (CapWords / snake_case / allow-listed) participate;
    # `frame_count` is snake_case so it is indexed, and prefer_class picks the
    # anchor under RetargetingResult over the equal-depth alternative.
    si = SymbolIndex(_spec(tmp_path, prefer_class_for_short={"frame_count": "RetargetingResult"}))
    _by_id, by_short = si.build_index_from_anchor_ids({"pkg.RetargetingResult.frame_count", "pkg.Other.frame_count"})
    assert by_short["frame_count"] == "pkg.RetargetingResult.frame_count"


def test_resolve_identifier(tmp_path):
    si = SymbolIndex(_spec(tmp_path))
    by_id = {"pkg.Robot": "pkg.Robot"}
    by_short = {"Robot": "pkg.Robot"}
    assert si.resolve_identifier("Robot", by_id, by_short) == "pkg.Robot"
    assert si.resolve_identifier("pkg.Robot", by_id, by_short) == "pkg.Robot"
    assert si.resolve_identifier("Unknown", by_id, by_short) is None
    assert si.resolve_identifier("foo/bar", by_id, by_short) is None  # not an identifier


def test_cache_roundtrip_filters_by_prefix(tmp_path):
    si = SymbolIndex(_spec(tmp_path))
    si.write_anchor_cache({"pkg.A", "pkg.B", "other.C"})
    # load filters to the configured package prefix
    assert si.load_cached_anchor_ids() == {"pkg.A", "pkg.B"}


def test_missing_cache_returns_none(tmp_path):
    assert SymbolIndex(_spec(tmp_path)).load_cached_anchor_ids() is None
