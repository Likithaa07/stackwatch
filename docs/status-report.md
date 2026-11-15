# StackWatch: final status report (v1.0.0, 2026-11-16)

**Overall: GREEN.** All 22 tickets across 5 sprints are closed. Every requirement has live evidence in `docs/evidence/`.

## Done
| Sprint | Delivered |
|---|---|
| 0 Foundations | signed-off requirements, CI (ruff, pytest 85% gate, gitleaks), branch protection, PR template, Definition of Done |
| 1 Data pipeline | planner (SizeRight to plans lookup), usage model, HEC client with retries, simulator; 1,420 events sent = received |
| 2 Splunk app | packaged app, status macros, dashboard (< 1 s load), alerts with per-customer throttle; detection 12.1 min |
| 3 Operations | runbook, 4 failure drills with TTD/TTF and incident reviews, weekly report; 3 drill gaps fixed (#36-#38) |
| 4 Delivery | Helm chart for SizeRight, Postgres, Redis and simulator on kind, one command; README, customer explainer |

## Quality
56 tests, 93% coverage. Every PR: lint, tests, Helm lint, secret scan. 0 secrets committed.

## Next (proposed, not started)
- Store plans with a real `planned_at` by re-planning against SizeRight (current demo plans count as stale by design).
- Persistent Postgres volume and TLS verification for anything beyond local dev.
- Email/Slack alert actions (alerts currently go to Splunk's triggered-alerts list).

## Risks
| Risk | Impact | Mitigation |
|---|---|---|
| Demo data is simulated | real customers behave differently | thresholds live in one macro; tune after a week of real data |
| Report uses p95, alerts use 15-min rule | a customer can be OK yet flagged in the report | explained in the report header and customer explainer |
| Local Splunk uses a self-signed cert | TLS checks are off locally | one startup warning; `HEC_INSECURE` must be false in production |

## Evidence
Drills: [docs/drills.md](drills.md). Alerts: [evidence/sw-11-detection.txt](evidence/sw-11-detection.txt).
Kubernetes: [evidence/sw-15.txt](evidence/sw-15.txt). Weekly report: [reports/weekly-2026-11-15.md](reports/weekly-2026-11-15.md).
