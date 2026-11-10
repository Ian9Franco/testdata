# D — Harbor draft (model)

HOLD. Do not send `inbox/harbor_weekly_DRAFT.md`.

| # | Draft | What is wrong | Correct |
| --- | --- | --- | --- |
| 1 | "Harbour Recycle Centre" | Name | Harbor Recycle Central, as stored on the facility. |
| 2 | All four robots at 93% "after outlier buckets were removed" | The 93% figures are real only after dropping every bucket under 90%. That filter deletes the failure. | RBT-HBR-02, Sat 05:00–11:00 PT, 24 buckets, target success 0.619, air 58 psi. The unfiltered week for that robot is 0.903, which still hides a six-hour loss. RBT-HBR-01 on the same belt stayed near 0.93 at 96 psi. |
| 3 | "No model changes affected customer performance" | A deploy is sitting unread in Friday's log. | RBT-HBR-04 moved to v2.14.0 at Fri 02:00 PT. From Fri 06:00 onward, 30% of attempts are OCC, the commodity that line is supposed to keep. Target success stays 0.93, which is why the draft's chart looks fine. The Monday 06:00–08:30 island is still open. |
| 4 | QC counted 30,472 PET vs 15,236 on the container line, so buy another robot | Nov 3 QC rows are duplicated, 96 extra buckets. | Deduped QC PET is 15,236, the same as SCN-HBR-01. There is no volume gap. |
| 5 | Harbor residue PET was 21.0% on Thursday afternoon | That share is the Lakeshore infeed scanner, pasted onto the wrong site. | SCN-HBR-03 over the same hours is 0.070. SCN-LKS-01 Thu 13:00–17:00 is 0.210. Harbor does not get a sorter-fault email. |
| 6 | Air was 96 psi at 2026-11-07 15:00 PT on the container line | Harbor's Saturday window ends at 13:00. At 15:00 PT both container robots are offline and air is null. | 15:00 UTC is 07:00 PT. At that minute RBT-HBR-01 is 96 psi and RBT-HBR-02 is 58 psi. The sentence kept the healthy robot and mislabeled the clock. |
| 7 | "Figures are final" | No peer check, and three of the four claims above are customer-visible errors. | Hold the send. Field Service on the air loss and Perception on the fiber robot come before any weekly number. |

Internal only, the PET mass note belongs to Lakeshore, not this draft: about 1,400 extra PET detections at SCN-LKS-01 versus that scanner's baseline, roughly 31 kg if you assume 22 grams per detection. Downstream was still about 900 detections above baseline. That assumption is not a scale weight, and it does not go in the Harbor email.
