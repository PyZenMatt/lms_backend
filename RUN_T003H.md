# Run T-003.H runtime probe

This repository contains a small runtime probe `scripts/t003h_probe.sh` that queries a list of endpoints marked as GATE/OFF and records their HTTP status codes. Use this file to run the probe locally and append the results to the evidence log.

Usage

1. Ensure your application is running locally and accessible at `$BASE_URL` (default `http://localhost:8000`).

2. Run the probe and save output:

   ```bash
   cd lms_backend
   BASE_URL="http://localhost:8000" ./scripts/t003h_probe.sh > /tmp/t003h_probe_output.txt
   ```

3. Review the output and append to the evidence log:

   ```bash
   cat /tmp/t003h_probe_output.txt >> docs/EVIDENCE_LOG.md
   git add docs/EVIDENCE_LOG.md
   git commit -m "evidence(T-003.H): runtime probe output"
   git push origin <branch>
   ```

Notes

- The probe performs unauthenticated GET requests. If any gated endpoint requires authentication in production, run the probe against a test instance configured the same way the gate will be deployed.
- The script returns a non-zero exit code if curl fails to contact the server; examine the output for details.
