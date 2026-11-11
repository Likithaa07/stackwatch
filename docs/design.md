# StackWatch: design

## Problem
SizeRight recommends how big a customer's Splunk stack should be. Nobody checks afterwards
whether that size was right. Customers grow, and an undersized stack gets slow before anyone notices.

## Goal
Watch every customer stack, compare **planned capacity** (from SizeRight) with **actual usage**,
and alert the on-call engineer before a customer feels it.

## How it works
1. `customers.yaml` lists ~10 demo customers (region, ingest, search profile, premium apps).
2. `scripts/plan.py` calls the SizeRight API for each customer and saves the plan
   (indexers, search heads) as a Splunk lookup (`stackwatch_plans.csv`).
3. `simulator/` generates realistic usage every minute per customer (GB ingested,
   concurrent searches, CPU %), with daily peaks, noise and growth, and sends it to Splunk via HEC.
4. The Splunk app `stackwatch` joins usage with the plan and labels each stack.
5. Alerts fire on undersized stacks, missing data and SizeRight errors.

## Definitions
- **Planned ingest capacity** = indexers × GB/day each indexer handles (from SizeRight's rules,
  e.g. 200 GB/day for a moderate profile, 100 with Enterprise Security).
- **Utilisation** = actual ingest (GB/day rate) ÷ planned ingest capacity.
- **Status**
  - `UNDERSIZED`: utilisation > 90% for 15 minutes
  - `OVERSIZED`: utilisation < 40% for 1 hour (wasting money)
  - `OK`: everything else
  - `NO DATA`: no events for 10 minutes

## Non-goals
- Not a real Splunk Cloud integration; usage is simulated.
- No customer-facing UI outside Splunk.

## Risks
- Splunk Enterprise trial ends in ~60 days; Splunk Free has no alerts. Screenshots are kept in `docs/screenshots/`.
- Simulator numbers are made up; the point is the pipeline and the on-call workflow, not the numbers.
