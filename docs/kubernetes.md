# Running StackWatch on Kubernetes (SW-15)

One command starts SizeRight, Postgres, Redis and the simulator on a local kind cluster:

    ./scripts/k8s-up.sh      # needs docker, kind, helm, kubectl; HEC_TOKEN in .env; SizeRight repo at ~/projects/sizeright
    ./scripts/k8s-down.sh    # deletes the cluster

| Component | Probes | Limits | Secrets |
|---|---|---|---|
| Postgres | pg_isready | 500m / 256Mi | db-password |
| Redis | redis-cli ping, TCP | 250m / 128Mi | - |
| SizeRight | /readyz, /healthz; migrations run as an init container | 500m / 256Mi | db-password, jwt-secret |
| Simulator | heartbeat file (stale after 3 intervals = restart) | 250m / 128Mi | hec-token |

- Secrets are a Kubernetes Secret; the chart refuses to install without them (`required`). DB and JWT secrets are random per cluster and reused on re-run; the HEC token comes from `.env`. Nothing secret is committed or baked into images.
- Containers run as non-root. SizeRight sets `runAsUser: 65532` because its distroless image names its user (`nonroot`), which Kubernetes cannot verify (found on first deploy).
- Postgres uses `emptyDir`: local dev only, data resets with the pod.
- Evidence: [evidence/sw-15.txt](evidence/sw-15.txt)
