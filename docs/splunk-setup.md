# Local Splunk setup (SW-7)

How to run StackWatch against local Splunk Enterprise and prove data arrives (REQ-2, REQ-3).

## 1. Index
Settings > Indexes > New Index: `stackwatch`.

## 2. HEC token
Settings > Data inputs > HTTP Event Collector > New Token:
- Name `stackwatch`, source type `stackwatch:usage`
- Allowed index `stackwatch` only; default index `stackwatch`
- Global Settings: All Tokens Enabled, SSL on, port 8088

## 3. Configure and run
    cp .env.example .env              # put the token in HEC_TOKEN (.env is git-ignored)
    set -a; source .env; set +a
    SIM_INTERVAL=5 python -m simulator   # Ctrl+C to stop

## 4. Verify
    index=stackwatch sourcetype=stackwatch:usage | stats count by customer_id

## Evidence (2026-11-13)
- Simulator: 142 batches x 10 events, no HEC errors, ended with `stopped cleanly after 142 batches`.
- Splunk: 1,420 events, all 10 customers, 142 each: [evidence/sw-7-hec-counts.csv](evidence/sw-7-hec-counts.csv)
- Sent = received, so zero data loss.

## TLS note
`HEC_INSECURE=true` accepts Splunk's self-signed certificate (local dev only). The simulator logs one
`TLS verification OFF` warning at startup instead of a warning per batch (fixed in #25).
