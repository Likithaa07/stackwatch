"""Run the usage simulator: one event per customer every interval, sent to Splunk via HEC.

    python -m simulator

Settings (environment variables, see .env.example):
    HEC_URL, HEC_TOKEN       where to send events (required)
    HEC_INSECURE=true        accept Splunk's self-signed certificate (local dev only)
    SIM_INTERVAL=60          real seconds between batches
    SIM_SPEED=240            simulated seconds per real second (240 => 1 simulated day every 6 minutes)
"""

import csv
import logging
import os
import random
import signal
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path

import urllib3
import yaml

from simulator.hec import HECClient
from simulator.usage import SECONDS_PER_DAY, sample

log = logging.getLogger("simulator")

ROOT = Path(__file__).resolve().parent.parent
CUSTOMERS = ROOT / "customers.yaml"
PLANS = ROOT / "splunk_app" / "stackwatch" / "lookups" / "stackwatch_plans.csv"


@dataclass(frozen=True)
class Config:
    hec_url: str
    hec_token: str
    insecure: bool
    interval: float
    speed: float


def load_config(env: dict) -> Config:
    """Read settings from environment variables, failing fast with a clear message."""
    missing = [k for k in ("HEC_URL", "HEC_TOKEN") if not env.get(k)]
    if missing:
        raise ValueError(f"missing settings: {', '.join(missing)}")
    interval = float(env.get("SIM_INTERVAL", "60"))
    speed = float(env.get("SIM_SPEED", "240"))
    if interval <= 0 or speed <= 0:
        raise ValueError("SIM_INTERVAL and SIM_SPEED must be positive")
    return Config(
        hec_url=env["HEC_URL"],
        hec_token=env["HEC_TOKEN"],
        insecure=env.get("HEC_INSECURE", "false").lower() == "true",
        interval=interval,
        speed=speed,
    )


def load_capacities(path: Path) -> dict[str, float]:
    """customer_id -> planned capacity (GB/day) from the plans lookup."""
    with path.open() as f:
        return {row["customer_id"]: float(row["planned_capacity_gb"]) for row in csv.DictReader(f)}


def sim_clock(elapsed_real_s: float, speed: float, start_hour: float = 8.0) -> tuple[float, float]:
    """Simulated (day, hour-of-day) after elapsed_real_s real seconds at the given speed."""
    sim_seconds = elapsed_real_s * speed
    day = sim_seconds / SECONDS_PER_DAY
    hour = (start_hour + sim_seconds / 3600) % 24
    return day, hour


def tick(customers: list[dict], capacities: dict[str, float], day: float, hour: float, rng) -> list[dict]:
    """One batch: a usage event for every customer that has a plan."""
    events = []
    for c in customers:
        cap = capacities.get(c["id"])
        if cap is None:
            log.warning("no plan for %s; run scripts.plan first", c["id"])
            continue
        events.append(sample(c, cap, day, hour, rng))
    return events


def run(cfg: Config, customers, capacities, client, stop: threading.Event, clock=time.monotonic) -> int:
    """Send a batch every interval until stop is set. Returns the number of batches sent."""
    rng = random.Random()
    start = clock()
    batches = 0
    while not stop.is_set():
        day, hour = sim_clock(clock() - start, cfg.speed)
        events = tick(customers, capacities, day, hour, rng)
        client.send(events)
        batches += 1
        log.info("batch %d: %d events, sim day %.2f %02d:00", batches, len(events), day, hour)
        stop.wait(cfg.interval)
    log.info("stopped cleanly after %d batches", batches)
    return batches


def warn_if_insecure(insecure: bool) -> None:
    """One clear startup warning instead of a urllib3 warning on every batch (SW-25)."""
    if insecure:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        logging.getLogger("simulator").warning("TLS verification OFF (HEC_INSECURE=true): local dev only")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    try:
        cfg = load_config(dict(os.environ))
    except ValueError as e:
        sys.exit(str(e))
    customers = yaml.safe_load(CUSTOMERS.read_text())["customers"]
    capacities = load_capacities(PLANS)
    warn_if_insecure(cfg.insecure)
    # gitleaks:allow below: false positive, hec_token is a variable name; the value comes from the env
    client = HECClient(
        cfg.hec_url,
        cfg.hec_token,
        verify_tls=not cfg.insecure,  # gitleaks:allow
    )

    stop = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())
    run(cfg, customers, capacities, client, stop)


if __name__ == "__main__":
    main()
