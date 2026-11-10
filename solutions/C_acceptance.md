# C — Riverbend acceptance (model)

Window: 2026-11-04 through the end of 2026-11-07. Source query: `commissioning_scorecard`, plus `scanner_audit_deltas` for the hand sort. Burn-in is excluded.

## Scorecard

| Asset | Metric | Actual | Contract | Result |
| --- | --- | --- | --- | --- |
| RBT-RVB-01 | Uptime | 0.967 | ≥ 0.95 | PASS |
| RBT-RVB-01 | Picks per minute | 31 | ≥ 40 | FAIL |
| RBT-RVB-01 | PET success | 0.928 | ≥ 0.90 | PASS |
| RBT-RVB-01 | HDPE success | 0.926 | ≥ 0.90 | PASS |
| RBT-RVB-01 | Aluminum success | 0.712 | ≥ 0.90 | FAIL |
| RBT-RVB-01 | E-stop buckets | 0 | ≤ 0 | PASS |
| RBT-RVB-02 | Uptime | 1.000 | ≥ 0.95 | PASS |
| RBT-RVB-02 | Picks per minute | 39 | ≥ 36 | PASS |
| RBT-RVB-02 | PET / HDPE / AL success | 0.928 / 0.927 / 0.930 | ≥ 0.90 | PASS |
| RBT-RVB-02 | E-stop buckets | 0 | ≤ 0 | PASS |
| SCN-RVB-01 | Scheduled offline minutes | 0 | ≤ 60 | PASS |
| SCN-RVB-02 | Scheduled offline minutes | 0 | ≤ 60 | PASS |
| SCN-RVB-03 | Scheduled offline minutes | 300 | ≤ 60 | FAIL |

Hand sort on the container infeed, Fri Nov 6, n=480, versus SCN-RVB-01: every commodity is within about 1 point (`WITHIN`). That supports the infeed scanner. It does not cover SCN-RVB-03, which was offline Saturday 09:00–14:00 PT.

RBT-RVB-01 also has a logged network blip Wednesday 08:00–09:00 (60 minutes). It is already in the event log, it is the reason uptime is 0.967 rather than 1, and it still passes. It is not a new page.

The blended success rate for RBT-RVB-01 sits between 0.85 and 0.90. The contract is per commodity, so aluminum still fails.

Hold RBT-RVB-01 and SCN-RVB-03. Accept RBT-RVB-02, SCN-RVB-02, and SCN-RVB-01.

Routes, both P2 because this is acceptance and nothing is a safety fault: Deployment Engineering for the 31 picks/min, Perception for aluminum only, Field Service for the downstream scanner.

## Email

Subject: Riverbend acceptance — not the whole site today

Renee,

We cannot sign the whole site today. We can accept three assets and we need to hold two.

Ready to accept: the residue robot (RBT-RVB-02), the residue infeed scanner (SCN-RVB-02), and the container infeed scanner (SCN-RVB-01). From Wednesday through Saturday the residue robot met uptime, pick rate, and pick success on PET, HDPE, and aluminum. Friday's hand sort (480 items) matched the container infeed scanner within about one point on each material.

Holding the container robot (RBT-RVB-01). Over the same four days it ran 31 picks per minute against a contract of 40. Aluminum pick success was 71%, against 90%. PET and HDPE were above 90%, and uptime was 96.7%, so this is not a down robot. We need a throughput tune and an aluminum-recognition pass before that asset can be signed.

Holding the container downstream scanner (SCN-RVB-03). It was offline for 300 scheduled minutes on Saturday, from 9:00 AM to 2:00 PM Pacific. The limit in the packet is 60 minutes.

The crew is right that the machines look like they are running. The gaps are rate, aluminum, and one dark camera, not a stopped plant. We will book the scanner visit and the container-robot tune and send you a revised signature list when those three numbers pass. Please do not sign the container robot this afternoon.
