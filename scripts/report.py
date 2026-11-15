"""Weekly plan-accuracy report (REQ-8): one command, worst customers first, with an action each."""

import datetime as dt
import json
import os
import sys
from pathlib import Path

import requests
import urllib3

SEARCH = (
    "search index=stackwatch sourcetype=stackwatch:usage earliest=-7d"
    " | lookup stackwatch_plans customer_id OUTPUT planned_capacity_gb region | fillnull value=unknown region"
    " | eval util_pct=100*ingest_gb_per_day/planned_capacity_gb | `stackwatch_thresholds`"
    " | stats avg(util_pct) as avg_util perc95(util_pct) as p95_util max(util_pct) as peak_util"
    " first(under_pct) as under_pct first(over_pct) as over_pct by customer_id region"
)
OUT_DIR = Path("docs/reports")


def fetch(session, base_url: str, user: str, password: str, verify: bool = True) -> list[dict]:
    r = session.post(
        f"{base_url}/servicesNS/{user}/stackwatch/search/jobs/export",
        data={"search": SEARCH, "output_mode": "json"},
        auth=(user, password),
        verify=verify,
        timeout=60,
    )
    r.raise_for_status()
    rows = [json.loads(line).get("result") for line in r.text.splitlines() if line.strip()]
    return [row for row in rows if row]


def action(row: dict) -> tuple[float, str]:
    """(how far outside the healthy band, what to do). Thresholds come from the Splunk macro."""
    p95, avg = float(row["p95_util"]), float(row["avg_util"])
    under, over = float(row["under_pct"]), float(row["over_pct"])
    if p95 > under:
        return p95 - under, "Re-size UP in SizeRight (p95 above the undersized line)"
    if avg < over:
        return over - avg, "Downsize (average below the oversized line)"
    return 0.0, "No action"


def render(rows: list[dict], today: str) -> str:
    ranked = sorted(rows, key=lambda r: action(r)[0], reverse=True)
    lines = [
        f"# StackWatch weekly report ({today})",
        "",
        "Worst first. Utilisation = actual ingest / planned capacity, last 7 days.",
        "Actions use p95 (the busiest 5% of the week) for capacity planning. Alerts use the sustained"
        " 15-minute rule for incidents, so a customer can be OK on the dashboard"
        " and still need re-sizing here.",
        "",
        "| # | Customer | Region | Avg % | p95 % | Peak % | Action |",
        "|---|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(ranked, 1):
        u = [round(float(r[k])) for k in ("avg_util", "p95_util", "peak_util")]
        lines.append(
            f"| {i} | {r['customer_id']} | {r['region']} | {u[0]} | {u[1]} | {u[2]} | {action(r)[1]} |"
        )
    needs = sum(1 for r in ranked if action(r)[0] > 0)
    return "\n".join([*lines, "", f"**{needs} of {len(ranked)} customers need action.**", ""])


def main() -> None:
    password = os.environ.get("SPLUNK_PASSWORD")
    if not password:
        sys.exit("missing settings: SPLUNK_PASSWORD")
    insecure = os.environ.get("HEC_INSECURE", "").lower() == "true"
    if insecure:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    url = os.environ.get("SPLUNK_MGMT_URL", "https://localhost:8089")
    user = os.environ.get("SPLUNK_USER", "admin")
    try:
        rows = fetch(requests.Session(), url, user, password, verify=not insecure)
    except requests.RequestException as e:
        sys.exit(f"report failed: {e}")
    if not rows:
        sys.exit("report failed: no usage data in the last 7 days")
    today = dt.date.today().isoformat()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"weekly-{today}.md"
    out.write_text(render(rows, today))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
