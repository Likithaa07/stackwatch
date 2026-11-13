# Failure drills (SW-13, 2026-11-13)

Four planning-failure drills on local Splunk with the simulator running. Each one: inject, measure
time-to-detect (TTD) and time-to-fix (TTF), review, raise follow-ups. Raw log: [evidence/sw-13-drills.txt](evidence/sw-13-drills.txt)

| Drill | Injected | Detected | TTD | TTF | Result |
|---|---|---|---|---|---|
| D1 Wrong rule (hooli capacity cut to 1/3) | 17:56:53 | dashboard 17:56:54, alert 18:00:00 | 1 s / 3 m 7 s | 5 s | Pass |
| D2 Missing region (stark) | 17:56:17 | not detected by the system | none | 5 s | Gap: #37 |
| D3 Broken SizeRight output (truncated JSON) | 17:44:39 | 17:44:45, plan.py exit 1 | 6 s | 0 (lookup protected) | Pass, minor: #36 |
| D4 Silent rule change (acme plan says v2) | 17:56:17 | dashboard flag only, no alert | on view only | 5 s | Gap: #38 |

Fix for D1, D2, D4: reinstall the app, which restores the reviewed plans (runbook, Stale plans). Started 18:02:23, verified 18:02:28.

## D1 Wrong rule
**What happened:** hooli's plan under-sized by 3x, as if a SizeRight rule had a bug.
**What worked:** plans apply at search time, so the last 15 min were re-judged at once; UNDERSIZED alert caught only hooli on the next 5-min run.
**Follow-up:** none.

## D2 Missing region
**What happened:** stark's plan lost its region. Dashboard Region=All filters on `region="*"`, which excludes empty values, so stark vanished (9/10 shown). Status and alerts still covered stark, since they do not filter on region.
**Root cause:** filter semantics plus no validation of required plan fields.
**Follow-up:** #37.

## D3 Broken output
**What happened:** fake SizeRight returned truncated JSON. plan.py failed with "planning failed, lookup NOT updated" and exit 1; lookup md5 unchanged (atomic write held).
**Also found:** the runbook said `python scripts/plan.py`, which crashes with ModuleNotFoundError. Fixed in this PR (`python -m scripts.plan`). Parse errors were retried 3x: #36.

## D4 Silent rule change
**What happened:** acme's plan switched to rules v2. Dashboard showed MISMATCH (v2) immediately, but no alert, so nobody is told unless they look.
**Follow-up:** #38.
