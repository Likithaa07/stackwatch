"""Simulated usage for one customer stack at a point in (simulated) time."""

import math
import random

SECONDS_PER_DAY = 86_400


def daily_curve(hour: float) -> float:
    """Busier in the working day, quieter at night: 0.7x at midnight, 1.3x at noon."""
    return 1 + 0.3 * math.sin(2 * math.pi * (hour - 6) / 24)


MAX_GROWTH = 1.5  # SW-28: linear growth, capped; real customers do not compound 30%/day


def ingest_rate_gb(customer: dict, sim_day: float, hour: float, rng: random.Random) -> float:
    """Current ingest, expressed as a GB/day rate so it compares directly with capacity."""
    actual = customer["actual"]
    growth = min(1 + actual["growth_per_day"] * sim_day, MAX_GROWTH)
    base = customer["ingest_gb_per_day"] * actual["start"] * growth
    noise = rng.gauss(1.0, 0.05)
    return max(0.0, base * daily_curve(hour) * noise)


def sample(customer: dict, capacity_gb: float, sim_day: float, hour: float, rng: random.Random) -> dict:
    """One usage event for one customer."""
    ingest = ingest_rate_gb(customer, sim_day, hour, rng)
    utilisation = ingest / capacity_gb if capacity_gb else 0.0
    cpu = min(100.0, max(0.0, 20 + 75 * utilisation + rng.gauss(0, 3)))
    searches = max(0, round(customer["concurrent_users"] * 0.3 * daily_curve(hour) * rng.gauss(1.0, 0.1)))
    return {
        "customer_id": customer["id"],
        "region": customer["region"],
        "ingest_gb_per_day": round(ingest, 1),
        "cpu_pct": round(cpu, 1),
        "concurrent_searches": searches,
        "sim_day": round(sim_day, 3),
    }
