import random

import pytest

from simulator.usage import daily_curve, ingest_rate_gb, sample

STEADY = {
    "id": "steady",
    "region": "us-east-1",
    "ingest_gb_per_day": 1000,
    "concurrent_users": 100,
    "actual": {"start": 1.0, "growth_per_day": 0.0},
}
GROWER = {**STEADY, "id": "grower", "actual": {"start": 1.0, "growth_per_day": 1.0}}


def test_daily_curve_peaks_at_noon_and_dips_at_midnight():
    assert daily_curve(12) == pytest.approx(1.3)
    assert daily_curve(0) == pytest.approx(0.7)
    assert daily_curve(6) == pytest.approx(1.0)


def test_steady_customer_stays_near_declared_ingest():
    rng = random.Random(1)
    values = [ingest_rate_gb(STEADY, sim_day=d, hour=6, rng=rng) for d in range(30)]
    avg = sum(values) / len(values)
    assert 950 < avg < 1050


def test_sample_fields_and_bounds():
    rng = random.Random(7)
    for capacity in (100, 1000, 100_000):
        s = sample(STEADY, capacity, sim_day=0, hour=12, rng=rng)
        assert set(s) == {
            "customer_id",
            "region",
            "ingest_gb_per_day",
            "cpu_pct",
            "concurrent_searches",
            "sim_day",
        }
        assert 0 <= s["cpu_pct"] <= 100
        assert s["concurrent_searches"] >= 0


def test_zero_capacity_does_not_crash():
    s = sample(STEADY, 0, sim_day=0, hour=12, rng=random.Random(1))
    assert s["cpu_pct"] <= 100


def test_growth_is_linear_and_capped_so_usage_never_runs_away():
    from simulator.usage import MAX_GROWTH, ingest_rate_gb

    c = {"ingest_gb_per_day": 100, "actual": {"start": 1.0, "growth_per_day": 0.10}}

    def at(day):
        return ingest_rate_gb(c, day, 12, random.Random(7))

    assert at(1) / at(0) == pytest.approx(1.10)
    assert at(365) / at(0) == pytest.approx(MAX_GROWTH)
