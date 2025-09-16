#!/usr/bin/env bash
# T-003.H runtime probe (low-risk). Run with a local server running.
set -euo pipefail
BASE_URL=${BASE_URL:-http://localhost:8000}
TEOCOIN_SYSTEM=${TEOCOIN_SYSTEM:-database}

echo "Running T-003.H runtime probe against ${BASE_URL} (TEOCOIN_SYSTEM=${TEOCOIN_SYSTEM})"
echo
echo "# GATE/OFF probes (expect 410 when OFF)"
curl -is -X POST "${BASE_URL}/api/v1/rewards/wallet/mint/" | sed -n '1,12p'
curl -is -X POST "${BASE_URL}/api/v1/rewards/wallet/burn/" | sed -n '1,12p'
curl -is -X POST "${BASE_URL}/api/v1/teocoin/withdraw/" | sed -n '1,12p'
curl -is -X POST "${BASE_URL}/api/v1/teocoin/withdrawals/admin/process-pending/" | sed -n '1,12p'
curl -is -X POST "${BASE_URL}/api/v1/teocoin/withdrawals/admin/mint/" | sed -n '1,12p'

echo
echo "# KEEP probes (expect !=410)"
curl -is "${BASE_URL}/api/v1/health/" | sed -n '1,8p'
curl -is "${BASE_URL}/api/v1/rewards/wallet/transactions/" | sed -n '1,12p'

echo
echo "Probe complete. To append results to the evidence log run:" 
echo "  ./scripts/t003h_probe.sh | tee /tmp/t003h_output.txt"
echo "  tail -n +1 /tmp/t003h_output.txt >> docs/EVIDENCE_LOG.md && git add docs/EVIDENCE_LOG.md && git commit -m \"docs(evidence): T-003.H runtime probe\""
