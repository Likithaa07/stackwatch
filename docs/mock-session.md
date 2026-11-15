# Mock customer session (about 3 minutes)

**Scenario:** Globex says "our Splunk searches got slow this week". Recording: _link added after recording_.

**Setup:** simulator running for 15+ minutes (`./scripts/k8s-up.sh`), dashboard open, Time = Last 60 minutes.

| Time | Show | Say |
|---|---|---|
| 0:00 | Dashboard, full table | "Thanks for raising this. This is StackWatch: every stack we sized for you, compared with what it really uses." |
| 0:20 | Point at globex row (red) | "Your stack is UNDERSIZED: above 90% of the capacity we planned, for more than 15 minutes. That matches the slow searches." |
| 0:45 | Click globex row; chart filters | "Here is your usage over time. The red dashed line is 90%. You are above it at peak hours, so searches queue behind indexing." |
| 1:15 | Open customer explainer, sizing section | "When we sized you, you told us 1,200 GB a day with heavy searching. At 150 GB per indexer that gave your indexer count. Actual ingest is higher than declared." |
| 1:45 | Show weekly report row for globex | "The weekly report already ranked you first, with the action: re-size up in SizeRight." |
| 2:10 | Show runbook UNDERSIZED section | "Our on-call followed this runbook: confirm the trend, compare actual with declared, re-size." |
| 2:30 | Back to dashboard | "Next step: we re-run sizing with your real ingest, add indexers, and you will see this row turn green. I will send the new plan today." |
| 2:50 | End | "Any questions?" |

**Record:** QuickTime Player, then File, New Screen Recording, choose the Chrome window, with microphone on.
