# A — Triage (model)

Monday 08:30 PT. Eleven rows. Anything not listed here stays off the escalation log.

| Priority | Asset | Route | Why |
| --- | --- | --- | --- |
| P1 | RBT-CDR-01 | Field Service | E-stop still set. 06:45–08:30 PT, 7 buckets, belt running, 0 picks, air 96 psi. Sibling robots still picking. Caller is on the line and has a tour at 09:00. |
| P1 | RBT-HBR-04 | Perception | Off-target rate 0.300 on OCC, which is the fiber line's protected commodity. Islands Fri 06:00–18:00, Sat 05:00–13:00, and Mon 06:00–08:30. Still happening. Model v2.14.0 is on the asset from Fri 02:00; first picking bucket is Fri 06:00. Target success stays 0.93, so a success chart will not show this. |
| P2 | RBT-HBR-02 | Field Service | Sat 05:00–11:00 PT, 24 buckets, air 58 psi, target success 0.619. All three target classes drop together. RBT-HBR-01 on the same belt stays at 96 psi and about 0.93. Saturday log missed it. It has ended, so it is not P1, and it was never logged, so it is not closed. |
| P2 | SCN-LKS-01 | Customer Success | Thu 13:00–17:00 PT. Infeed PET share 0.210 versus about 0.070 on other hours. AL share 0.131 versus 0.040. Hand sort (n=300) is within 1 point of the scanner. Downstream SCN-LKS-02 still shows PET at 0.161, so material got past the robot. RBT-LKS-01 ran at 45 picks/min with target success 0.929. The robot was saturated, not broken. Voicemail says OPT-PET-2 was reset Fri 07:20. Fri 13:00 PET share is 0.069. The loss is historical and the reset checks out. |
| P2 | SCN-CDR-02 | Field Service | `dirty_lens` from Fri 08:00 through the Mon 08:15 bucket. Confidence 0.61, unknown share 0.45. At Mon 08:00 the healthy infeed scanner sees the same 1,200 objects and 888 OCC; the dirty camera reports 488 OCC and 540 unknown. Paper did not vanish. |
| P2 | RBT-RVB-01 | Deployment Engineering | Acceptance window, 31 picks/min versus a contract of 40. Uptime 0.967 passes. This is tune, not a production outage. |
| P2 | RBT-RVB-01 | Perception | Same robot, aluminum success 0.712 versus 0.90. PET 0.928 and HDPE 0.926 pass. Blended target success for the window is above 0.85 and below 0.90, so the blended number hides the miss. |
| P2 | SCN-RVB-03 | Field Service | Offline Sat 09:00–14:00 PT, 20 scheduled buckets, 300 minutes, contract limit 60. |
| P3 | RBT-PAC-03 | Data Engineering | Fri 14:00–17:00 PT, 12 buckets. 620 successes, 40 attempts, 20 objects. Do not report it as a good hour. |
| P3 | SCN-HBR-04 | Data Engineering | 96 duplicated buckets on Nov 3. Raw PET sum 30,472 is exactly twice the deduped 15,236, which matches the container scanner. |
| P3 | SCN-LKS-02 | Data Engineering | 706 buckets whose PT label is the UTC clock. Thu 13:00 PT is stored as 21:00. The composition finding above uses the corrected clock. The label bug is a second row, not a reason to drop the leak. |

## Left alone

- RBT-PAC-01, Wed 09:00–11:00, `PLANNED_PM`, 120 minutes. Already in events.
- LN-PAC-CON empty belt, Fri 10:00–10:45, 45 minutes. Under 60.
- LN-LKS-CON stopped, Tue 13:00–13:30, 30 minutes. Under 45. RBT-LKS-02 idled, which is what it should do.
- RBT-RVB-01 offline Wed 08:00–09:00. Already logged as a network blip. Uptime still passes. Cite it in the scorecard; do not page it.
- RBT-HBR-01 during the air loss. It is the control, not a second failure.
- RBT-CDR-02 and RBT-CDR-03 during the e-stop. They kept picking.
- SCN-CDR-01. Healthy comparison camera.
- TCK-1019. Closed.
- RBT-RVB-02, SCN-RVB-01, SCN-RVB-02. They pass. They do not need an escalation row. They do need a "yes" in the acceptance email.

## Shift order

Answer Mike first. While you are on the phone, the e-stop row is already P1 to Field Service because the 08:15 bucket is still latched and you have not seen a recovery. Second, ask Harbor to pause RBT-HBR-04 until Perception looks at v2.14.0; OCC is the product on that line. Then the Riverbend email, because Renee asked for an answer by 11:00. The Saturday air loss and the Lakeshore note can follow. Block the Harbor draft until the duplicate rows and the two Harbor findings are dealt with.
