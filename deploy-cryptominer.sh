#!/bin/bash
#
# Deploy the cryptominer simulator into a running unguard frontend pod and run
# it in the background. Intended for authorized security testing in isolated
# environments only.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SIMULATOR_PATH="${SIMULATOR_PATH:-$SCRIPT_DIR/exploit-toolkit/exploits/cryptominer/cryptominer_simulator.py}"
CONFIG_PATH="${CONFIG_PATH:-$SCRIPT_DIR/exploit-toolkit/exploits/cryptominer/miner_config.json}"

NAMESPACE="unguard-asai"
POD_SELECTOR="app.kubernetes.io/name=frontend,app.kubernetes.io/part-of=unguard"
PROFILE="aggressive"
DURATION=""
EXTRA_ARGS=""

usage() {
  cat <<EOF
Usage: $0 [options]

  -n, --namespace NS      Kubernetes namespace (default: $NAMESPACE)
  -s, --selector SEL      Pod label selector (default: "$POD_SELECTOR")
  -p, --profile NAME      Simulator profile: light|aggressive|stealthy (default: $PROFILE)
  -d, --duration MIN      Auto-stop after N minutes
      --simulator PATH    Path to cryptominer_simulator.py (default: in-repo)
      --config PATH       Path to miner_config.json (copied to pod if set)
      -- ARGS             Pass remaining args verbatim to the simulator
  -h, --help              Show this help

Examples:
  $0 --namespace unguard-asai --profile aggressive --duration 10
  $0 --profile stealthy -- --no-stratum --cpu 10
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -n|--namespace) NAMESPACE="$2"; shift 2;;
    -s|--selector) POD_SELECTOR="$2"; shift 2;;
    -p|--profile) PROFILE="$2"; shift 2;;
    -d|--duration) DURATION="$2"; shift 2;;
    --simulator) SIMULATOR_PATH="$2"; shift 2;;
    --config) CONFIG_PATH="$2"; shift 2;;
    --) shift; EXTRA_ARGS="$*"; break;;
    -h|--help) usage; exit 0;;
    *) echo "unknown arg: $1" >&2; usage >&2; exit 2;;
  esac
done

if [[ ! -f "$SIMULATOR_PATH" ]]; then
  echo "[!] Simulator not found at: $SIMULATOR_PATH" >&2
  exit 1
fi

echo "[*] Locating pod with selector \"$POD_SELECTOR\" in namespace $NAMESPACE..."
POD="$(kubectl get pod -n "$NAMESPACE" -l "$POD_SELECTOR" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)"
if [[ -z "$POD" ]]; then
  echo "[!] No pod found in $NAMESPACE with selector \"$POD_SELECTOR\"." >&2
  exit 1
fi
echo "[*] Target pod: $NAMESPACE/$POD"

echo "[*] Uploading simulator to /tmp/miner.py..."
kubectl cp "$SIMULATOR_PATH" "$NAMESPACE/$POD:/tmp/miner.py"

SIM_ARGS=(--profile "$PROFILE")
if [[ -n "$DURATION" ]]; then
  SIM_ARGS+=(--duration "$DURATION")
fi
if [[ -n "$CONFIG_PATH" && -f "$CONFIG_PATH" ]]; then
  echo "[*] Uploading config to /tmp/miner_config.json..."
  kubectl cp "$CONFIG_PATH" "$NAMESPACE/$POD:/tmp/miner_config.json"
  SIM_ARGS+=(--config /tmp/miner_config.json)
fi
if [[ -n "$EXTRA_ARGS" ]]; then
  SIM_ARGS+=($EXTRA_ARGS)
fi

echo "[*] Starting simulator: python3 /tmp/miner.py ${SIM_ARGS[*]}"
kubectl exec -n "$NAMESPACE" "$POD" -- sh -c \
  "nohup python3 /tmp/miner.py ${SIM_ARGS[*]} > /tmp/miner.log 2>&1 &"

echo
echo "[*] Deployed. Useful commands:"
echo "    kubectl exec -n $NAMESPACE $POD -- tail -f /tmp/miner.log"
echo "    kubectl exec -n $NAMESPACE $POD -- curl -s localhost:9100/status"
echo "    kubectl exec -n $NAMESPACE $POD -- cat /tmp/miner.log | jq ."
echo
echo "[*] Expected detections:"
echo "    GuardDuty CryptoCurrency:Runtime/BitcoinTool.B!DNS  (DNS to known pool)"
echo "    GuardDuty CryptoCurrency:Runtime/BitcoinTool.B!HTTP (xmrig UA on pool HTTP)"
echo "    Dynatrace runtime security / host CPU anomalies"
