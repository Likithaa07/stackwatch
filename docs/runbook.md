# StackWatch runbook

On-call guide for StackWatch alerts. Every alert links to its section here.
Dashboard: StackWatch app > "StackWatch: plan vs actual".

## UNDERSIZED
**Severity:** High. **Meaning:** the customer has been above 90% of planned capacity for 15+ minutes; ingest delays and search slowdowns are likely.

**First 3 steps**
1. Open the dashboard, filter to the customer, and check the trend: a steady climb means real growth, a spike means a one-off burst.
2. Compare `util_pct` with `declared_ingest_gb` in the plans lookup: if actual ingest is well above what the customer declared, the plan was built on wrong inputs.
3. Re-size in SizeRight with the actual ingest (`python -m scripts.plan`) and note the new indexer count.

**Escalation:** if still UNDERSIZED after 1 hour, or utilisation is above 120%, page the customer's TAM and the capacity lead with the dashboard link and the new SizeRight plan.

## NO DATA
**Severity:** Medium. **Meaning:** no usage events from the customer for 10+ minutes. Either the customer stopped sending or our pipeline broke.

**First 3 steps**
1. Check whether it is one customer or all: if all customers are NO DATA, it is our pipeline, not the customer.
2. Pipeline checks: is the simulator/forwarder running, does `index=_internal sourcetype=splunkd component=HttpInputDataHandler` show HEC errors, has the HEC token been disabled or rotated?
3. If only one customer is affected, confirm with the customer's admin whether ingestion was paused on purpose.

**Escalation:** all customers affected for 30+ minutes goes to the platform on-call. A single customer affected for 2+ hours goes to the customer's TAM.

## Stale plans
**Severity:** Medium. **Meaning:** a sizing plan is more than 24 hours old, or has no `planned_at` timestamp, so StackWatch may be comparing against outdated capacity.

**First 3 steps**
1. Run `python -m scripts.plan` (needs `SIZERIGHT_TOKEN`) to refresh all plans from SizeRight.
2. Rebuild and reinstall the app (`python scripts/package.py`, then `splunk install app ... -update 1`).
3. Confirm with `| inputlookup stackwatch_plans | table customer_id planned_at rules_version`; the next alert run should clear it.

**Escalation:** if SizeRight is down or refresh fails twice, raise a ticket with the SizeRight owner; plans stay stale until it is fixed.
