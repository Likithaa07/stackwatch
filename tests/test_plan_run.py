import csv

import pytest
import requests

from scripts import plan

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
}
INITECH = {
    "id": "initech",
    "region": "eu-west-1",
    "ingest_gb_per_day": 300,
    "retention_days": 30,
    "search_profile": "light",
    "concurrent_users": 15,
    "premium_apps": [],
    "smartstore": False,
    "high_availability": True,
}
CUSTOMERS = [ACME, INITECH]


class FakeResponse:
    def __init__(self, status, body=None):
        self.status_code = status
        self._body = body or {}

    def json(self):
        return self._body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} error")


def ok(sizing_id, indexers):
    result = {"rules_version": "v1", "indexers": indexers, "core_search_heads": 3, "premium_search_heads": 0}
    return FakeResponse(201, {"id": sizing_id, "result": result})


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.bodies = []

    def post(self, url, json, timeout):
        self.bodies.append(json)
        r = self.responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def test_run_writes_lookup_for_every_customer(tmp_path):
    out = tmp_path / "plans.csv"
    session = FakeSession([ok(1, 5), ok(2, 3)])
    rows = plan.run(session, "https://sr", CUSTOMERS, out, sleep=lambda s: None)
    assert [r["customer_id"] for r in rows] == ["acme", "initech"]
    written = list(csv.DictReader(out.open()))
    assert [w["planned_capacity_gb"] for w in written] == ["500", "900"]
    assert written[0]["rules_version"] == "v1"


def test_run_retries_then_succeeds(tmp_path):
    sleeps = []
    session = FakeSession([requests.ConnectionError("asleep"), FakeResponse(503), ok(1, 5), ok(2, 3)])
    plan.run(session, "https://sr", CUSTOMERS, tmp_path / "p.csv", sleep=sleeps.append)
    assert sleeps == [2, 4]


def test_failure_never_writes_partial_lookup(tmp_path):
    out = tmp_path / "plans.csv"
    out.write_text("previous good lookup\n")
    session = FakeSession([ok(1, 5)] + [FakeResponse(500)] * 3)
    with pytest.raises(requests.HTTPError):
        plan.run(session, "https://sr", CUSTOMERS, out, sleep=lambda s: None)
    assert out.read_text() == "previous good lookup\n"


def test_main_requires_token(monkeypatch):
    monkeypatch.delenv("SIZERIGHT_TOKEN", raising=False)
    with pytest.raises(SystemExit, match="SIZERIGHT_TOKEN"):
        plan.main()


def test_main_reports_clear_error_and_keeps_old_lookup(monkeypatch, tmp_path):
    monkeypatch.setenv("SIZERIGHT_TOKEN", "t")
    customers = tmp_path / "customers.yaml"
    customers.write_text("customers: []\n")
    monkeypatch.setattr(plan, "CUSTOMERS", customers)
    monkeypatch.setattr(plan, "OUT", tmp_path / "plans.csv")

    def boom(*args, **kwargs):
        raise requests.ConnectionError("SizeRight down")

    monkeypatch.setattr(plan, "run", boom)
    with pytest.raises(SystemExit, match="lookup NOT updated"):
        plan.main()
    assert not (tmp_path / "plans.csv").exists()
