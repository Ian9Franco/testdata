# E — Shift handoff (model)

# Shift handoff — 2026-11-09 08:30 PT

Author: Monday analyst

## P1 now

- RBT-CDR-01, Cedar fiber robot 1. E-stop latched 06:45–08:30 PT. Belt running, air 96 psi, siblings still picking. Mike Delaney is on TCK-1042 and has a tour at 09:00. I stayed on the script. I do not know whether a reset was attempted. Last bucket is still fault. Field Service owns it until a later bucket shows picks. Do not tell the site it is fixed.
- RBT-HBR-04, Harbor fiber robot. 30% of attempts are OCC since the Friday 06:00 production buckets. v2.14.0 deployed 02:00, changelog said film recall. OCC is the protected commodity on LN-HBR-FIB. I am asking the site to pause that robot. Perception owns the model. Customer Success needs to know the pause is recommended. Target-success charts will keep saying 93%.

## P2 today

- RBT-HBR-02, air 58 psi and target success 0.619, Sat 05:00–11:00 PT. Ended. Saturday log said the shift was quiet. Field Service should inspect before next Saturday. Do not stop RBT-HBR-01.
- SCN-LKS-01, Thu 13:00–17:00 PT, PET 21.0% and AL 13.1% at the infeed. Hand sort agrees. RBT-LKS-01 was at 45 picks/min and healthy. Downstream PET still 16.1%. Friday 13:00 is back to 6.9%, which matches the voicemail that OPT-PET-2 was reset at 07:20. Customer Success gets the quantification. About 1,400 extra infeed PET detections, ~31 kg at 22 g each, stated as an assumption.
- SCN-CDR-02 dirty lens since Fri 08:00, still dirty at 08:15 Monday. Field Service. Do not publish Cedar fiber composition from that camera. SCN-CDR-01 is the control.
- Riverbend reply is due by 11:00 PT. Accept RBT-RVB-02, SCN-RVB-02, SCN-RVB-01. Hold RBT-RVB-01 (31 ppm, aluminum 71.2%) and SCN-RVB-03 (300 min offline Saturday). Deployment, Perception, and Field Service as in the scorecard. The Wednesday 60-minute blip is already logged and uptime still passes.

## P3 before any customer number

- SCN-HBR-04 duplicates on Nov 3. Dedup before any QC count. 30,472 raw PET is 2× 15,236.
- SCN-LKS-02 PT label is UTC on all 706 buckets. Correct with `bucket_start_utc - 8 hours`.
- RBT-PAC-03 Fri 14:00–17:00 is impossible pick math (620 successes, 40 attempts, 20 objects). Quarantine. Friday's analyst never opened Pacific.

## Explicitly not paged

- RBT-PAC-01 planned maintenance Wed 09:00–11:00.
- Pacific empty belt 45 min Friday. Lakeshore container stop 30 min Tuesday.
- TCK-1019 stays closed.

## For the next analyst

Harbor weekly draft is on HOLD. The Saturday "quiet" note is not usable. If you only have time for two checks after this handoff: the next Cedar buckets after the e-stop, and whether Harbor actually paused RBT-HBR-04.
