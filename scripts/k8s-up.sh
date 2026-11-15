#!/usr/bin/env bash
# One command to start StackWatch on a local kind cluster (SW-15). Safe to re-run.
set -euo pipefail
cd "$(dirname "$0")/.."
SIZERIGHT_DIR="${SIZERIGHT_DIR:-$HOME/projects/sizeright}"
CLUSTER=stackwatch
HEC_TOKEN=$(grep '^HEC_TOKEN=' .env 2>/dev/null | cut -d= -f2- || true)
[ -n "$HEC_TOKEN" ] || { echo "HEC_TOKEN missing: copy .env.example to .env and set it"; exit 1; }

kind get clusters | grep -qx "$CLUSTER" || kind create cluster --name "$CLUSTER"
kubectl config use-context "kind-$CLUSTER" >/dev/null
docker build -q -t stackwatch-simulator:local .
docker build -q -t sizeright:local "$SIZERIGHT_DIR"
kind load docker-image --name "$CLUSTER" stackwatch-simulator:local sizeright:local
kubectl create configmap stackwatch-sizeright-migrations --from-file="$SIZERIGHT_DIR/migrations" \
  --dry-run=client -o yaml | kubectl apply -f - >/dev/null

existing() { kubectl get secret stackwatch-secrets -o go-template="{{index .data \"$1\"}}" 2>/dev/null | base64 -d 2>/dev/null || true; }
DB_PASSWORD=$(existing db-password); DB_PASSWORD=${DB_PASSWORD:-$(openssl rand -hex 16)}
JWT_SECRET=$(existing jwt-secret); JWT_SECRET=${JWT_SECRET:-$(openssl rand -hex 32)}

helm upgrade --install stackwatch deploy/helm/stackwatch --wait --timeout 5m \
  --set secrets.dbPassword="$DB_PASSWORD" --set secrets.jwtSecret="$JWT_SECRET" --set secrets.hecToken="$HEC_TOKEN"
kubectl get pods
echo "StackWatch is up. Simulator logs: kubectl logs deploy/stackwatch-simulator -f"
