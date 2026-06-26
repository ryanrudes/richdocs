"""Tests for deriving canonical-page priorities from the mkdocs nav."""

from __future__ import annotations

from richdocs._nav_priority import build_priority_resolver

_NAV = [
    {"Home": "index.md"},
    {
        "API": [
            {"Overview": "api/index.md"},
            {"Models": "api/models.md"},
            {"Registries": "api/registries.md"},
            {"Full reference": "api/reference.md"},
        ]
    },
]


def test_reference_is_least_preferred_and_index_high():
    pr = build_priority_resolver(_NAV, {})
    assert pr("/api/reference/") == 100  # last resort
    assert pr("/api/") == 90  # api landing page
    # curated pages are more preferred (lower) than the full reference
    assert pr("/api/models/") < pr("/api/reference/")
    assert pr("/api/registries/") < pr("/api/reference/")


def test_nav_order_orders_curated_pages():
    pr = build_priority_resolver(_NAV, {})
    # models appears before registries in nav -> preferred (lower number)
    assert pr("/api/models/") < pr("/api/registries/")


def test_overrides_win_and_longest_suffix_matches():
    pr = build_priority_resolver(_NAV, {"/api/models/": 5, "/api/": 91})
    assert pr("/api/models/") == 5  # specific override beats nav derivation
    assert pr("/api/") == 91  # /api/ override does not shadow /api/models/


def test_unknown_page_gets_default():
    assert build_priority_resolver([], {})("/guide/intro/") == 50
