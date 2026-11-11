"""Ask SizeRight to size every customer and save the plans as a Splunk lookup CSV.

Usage:
    SIZERIGHT_URL=https://sizeright.onrender.com SIZERIGHT_TOKEN=... python -m scripts.plan
"""

import csv
import logging
import os
import sys
import time
from pathlib import Path

import requests
import yaml

from simulator.capacity import gb_per_indexer, planned_capacity_gb

log = logging.getLogger("plan")

ROOT = Path(__file__).resolve().parent.parent
CUSTOMERS = ROOT / "customers.yaml"
OUT = ROOT / "splunk_app" / "stackwatch" / "lookups" / "stackwatch_plans.csv"
FIELDS = [
    "customer_id",
    "region",
    "sizing_id",
    "rules_version",
    "indexers",
    "core_search_heads",
    "premium_search_heads",
    "gb_per_indexer",
    "planned_capacity_gb",
    "declared_ingest_gb",
]
SIZERIGHT_FIELDS = [
    "region",
    "ingest_gb_per_day",
    "retention_days",
    "search_profile",
    "concurrent_users",
    "premium_apps",
    "smartstore",
    "high_availability",
]


def build_request(customer: dict) -> dict:
    """Only the fields SizeRight accepts (it rejects unknown fields)."""
    body = {k: customer[k] for k in SIZERIGHT_FIELDS}
    body["customer_id"] = customer["id"]
    body["cloud"] = "aws"
    return body


def plan_row(customer: dict, sizing_id: int, result: dict) -> dict:
    """One lookup row: what SizeRight planned and how much ingest it can take."""
    return {
        "customer_id": customer["id"],
        "region": customer["region"],
        "sizing_id": sizing_id,
        "rules_version": result["rules_version"],
        "indexers": result["indexers"],
        "core_search_heads": result["core_search_heads"],
        "premium_search_heads": result["premium_search_heads"],
        "gb_per_indexer": gb_per_indexer(customer["search_profile"], customer["premium_apps"]),
        "planned_capacity_gb": planned_capacity_gb(
            result["indexers"], customer["search_profile"], customer["premium_apps"]
        ),
        "declared_ingest_gb": customer["ingest_gb_per_day"],
    }


def size(session: requests.Session, url: str, body: dict, tries: int = 3) -> dict:
    """POST to SizeRight with retries. The first call may wait ~1 min while Render wakes up."""
    for attempt in range(1, tries + 1):
        try:
            r = session.post(f"{url}/v1/sizings", json=body, timeout=90)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            if attempt == tries:
                raise
            wait = 2**attempt
            log.warning("sizing %s failed (%s), retrying in %ss", body["customer_id"], e, wait)
            time.sleep(wait)
    raise RuntimeError("unreachable")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    url = os.environ.get("SIZERIGHT_URL", "https://sizeright.onrender.com").rstrip("/")
    token = os.environ.get("SIZERIGHT_TOKEN")
    if not token:
        sys.exit("SIZERIGHT_TOKEN is not set")

    customers = yaml.safe_load(CUSTOMERS.read_text())["customers"]
    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {token}"

    rows = []
    for c in customers:
        resp = size(session, url, build_request(c))
        row = plan_row(c, resp["id"], resp["result"])
        log.info(
            "%-10s indexers=%-3s capacity=%s GB/day (declared %s)",
            c["id"],
            row["indexers"],
            row["planned_capacity_gb"],
            row["declared_ingest_gb"],
        )
        rows.append(row)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    log.info("wrote %d plans to %s", len(rows), OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
