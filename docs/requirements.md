# StackWatch: requirements

Status: **DRAFT, awaiting client sign-off**
Owner: Likitha Vankadoth (engineering) · Client: PSP Provisioning (Splunk Cloud)

Every requirement has an ID and acceptance criteria (AC). A requirement is met only when
every AC is demonstrated, with evidence linked in the PR that closes it.

## Functional requirements

### REQ-1: Planned capacity from SizeRight
The system must obtain the planned stack size for every customer from the SizeRight API (not hard-coded).
- AC1: For each customer in `customers.yaml`, a sizing is created through `POST /v1/sizings`.
- AC2: Results are stored as a Splunk lookup with customer, sizing ID, rules version, indexers, search heads and planned capacity (GB/day).
- AC3: If SizeRight is unavailable, the job retries (3 attempts, backoff) and then fails with a clear error. It never writes a partial lookup.

### REQ-2: Usage telemetry
The system must produce per-customer usage every interval and deliver it to Splunk.
- AC1: One event per customer per interval (default 60 s) with ingest rate, CPU %, concurrent searches.
- AC2: Usage follows a daily pattern and per-customer growth defined in `customers.yaml`.
- AC3: Events reach index `stackwatch` via HEC; a Splunk outage must not crash the producer (retry with backoff, then drop and log).
- AC4: A bad HEC token is reported once and not retried.

### REQ-3: Stack health classification
The system must classify each stack as OK, UNDERSIZED, OVERSIZED or NO DATA.
- AC1: Utilisation = actual ingest ÷ planned capacity.
- AC2: UNDERSIZED when utilisation > 90% for 15 consecutive minutes.
- AC3: OVERSIZED when utilisation < 40% for 60 consecutive minutes.
- AC4: NO DATA when no events for 10 minutes.
- AC5: Thresholds are configurable in one place (Splunk macro), not repeated in searches.

### REQ-4: Dashboard
A Splunk dashboard must show fleet health at a glance.
- AC1: Table of all customers with status, utilisation %, planned vs actual GB/day, region.
- AC2: Utilisation over time per customer, with the 90% and 40% lines drawn.
- AC3: Region filter and time picker.
- AC4: Clicking a customer opens their detail view (drilldown).
- AC5: Loads in under 5 seconds for 24 hours of data.

### REQ-5: Alerting
On-call must be alerted before a customer is affected.
- AC1: Alert when any stack is UNDERSIZED (severity High), including customer, utilisation and a runbook link.
- AC2: Alert when any customer has NO DATA (severity Medium).
- AC3: Each alert fires at most once per customer per hour (throttling).

### REQ-6: Packaged Splunk app
- AC1: All searches, macros, lookups, dashboards and alerts ship as one installable app (`stackwatch.tgz`).
- AC2: Installing it on a clean Splunk works with no manual edits.

### REQ-7: Operability
- AC1: Runbook for every alert (meaning, first 3 steps, escalation).
- AC2: Four failure drills run and written up as incident reviews.
- AC3: The whole stack runs on Kubernetes (kind) with one command.

## Non-functional requirements
| ID | Requirement | Target |
|---|---|---|
| NFR-1 | Detection time: from a stack crossing 90% to the alert firing | ≤ 20 minutes |
| NFR-2 | Producer availability: survives Splunk restarts without manual action | 100% of drills |
| NFR-3 | Test coverage of Python code | ≥ 85% |
| NFR-4 | Secrets never committed; scanned in CI | 0 findings |
| NFR-5 | Every change via reviewed PR with green CI | 100% |

## Out of scope
Real Splunk Cloud customer data, billing, a UI outside Splunk.

## Sign-off
| Role | Name | Date | Decision |
|---|---|---|---|
| Client | | | |
| Engineering | Likitha Vankadoth | | |
