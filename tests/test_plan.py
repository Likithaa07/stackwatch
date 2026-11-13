from scripts.plan import build_request, plan_row
from simulator.capacity import gb_per_indexer, planned_capacity_gb

ACME = {
    "id": "acme",
    "region": "ap-southeast-2",
    "ingest_gb_per_day": 500,
    "retention_days": 90,
    "search_profile": "moderate",
    "concurrent_users": 40,
    "premium_apps": ["enterprise_security"],
    "smartstore": True,
    "high_availability": True,
    "actual": {"start": 0.85, "growth_per_day": 0.0},
}


def test_request_only_has_fields_sizeright_accepts():
    body = build_request(ACME)
    assert body["customer_id"] == "acme"
    assert body["cloud"] == "aws"
    assert "actual" not in body and "id" not in body


def test_es_uses_lower_per_indexer_capacity():
    assert gb_per_indexer("moderate", ["enterprise_security"]) == 100
    assert gb_per_indexer("moderate", []) == 200
    assert gb_per_indexer("heavy", ["itsi"]) == 150


def test_planned_capacity():
    assert planned_capacity_gb(5, "moderate", ["enterprise_security"]) == 500


def test_plan_row_matches_sizeright_golden_case():
    result = {"rules_version": "v1", "indexers": 5, "core_search_heads": 3, "premium_search_heads": 1}
    row = plan_row(ACME, 42, result)
    assert row["planned_capacity_gb"] == 500
    assert row["sizing_id"] == 42
    assert row["declared_ingest_gb"] == 500


def test_plan_row_is_stamped_with_planned_at_for_staleness_alerts():
    import time

    result = {"rules_version": "v1", "indexers": 3, "core_search_heads": 1, "premium_search_heads": 0}
    assert plan_row(ACME, 1, result, planned_at=1_700_000_000)["planned_at"] == 1_700_000_000
    assert abs(plan_row(ACME, 1, result)["planned_at"] - time.time()) < 5
