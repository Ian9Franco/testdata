# Daily monitoring

Work in Pacific Time. In this lab every facility clock is already PT. Say so when you write a time. A bucket time is the start of 15 minutes. Report the end as `end_pt_exclusive` ("through 11:00"), not as the last bucket start ("10:45").

Scenario clock: Monday 2026-11-09 08:30 PT. The feed stops at the 08:15 bucket.

## Definitions

- Use `telemetry_dedup` for every customer number. `duplicate_buckets` is the only query that reads raw `telemetry`.
- Correct PT is `bucket_start_utc` minus 8 hours. `bucket_start_pt` is a label. If they disagree, the label is wrong. Do not move an incident onto the wrong label.
- Scheduled time is the denominator for uptime. Closed hours are not uptime.
- Uptime = scheduled buckets where `robot_state` is `picking` or `idle` and `estop = 0`, divided by scheduled buckets.
- Target success = sum of successes on target commodities / sum of attempts on target commodities. Do not average bucket rates. Do not count off-target grabs as success.
- Off-target rate = off-target attempts / all attempts.
- Picks per minute = attempts / 15 on running buckets with burden ≥ 8.
- A weekly average is not a clearance. Keep any island the daily pack returns.

## Sequence

Run `python3 -m ops_lab.console briefing` or the queries in `ops_lab/sql/daily_pack.sql` in the briefing order. Then:

1. Read open tickets, shift logs, and events before you interpret a chart.
2. Page anything still happening that is safety or damage to a protected commodity.
3. Merge adjacent hours and islands on the same asset into one finding.
4. Compare a bad asset with the healthy sibling on the same line before you name a cause.
5. Check the manual audit before you call a composition shift a model failure.
6. Write the escalation row only after the route rules below fit. One asset can have two rows when two teams own two different failures.

## Thresholds

| Signal | Rule | Not an incident when |
| --- | --- | --- |
| Target success | < 85% for ≥ 60 min | Invalid pick math (exclude those buckets) |
| One commodity | < 85% for ≥ 60 min | The blended rate passed. The class did not. |
| Air | < 70 psi while picking, ≥ 60 min | The HMI is green. Ignore the HMI. |
| Off-target | ≥ 8% for ≥ 60 min | |
| Protected product | off-target commodity equals `lines.protected_commodity` | |
| Camera | `camera_health` other than `ok` | |
| Composition | hourly share moves ≥ 8 points vs the same hour on other days, scanner, camera ok, ≥ 4 running buckets | Daily average. Dirty or offline camera. |
| Capacity | ≥ 45 picks/min for ≥ 60 min with target success ≥ 90% | This is saturation, not a broken robot |
| Empty belt | one episode ≥ 60 min | 45 minutes is below the line |
| Unplanned stop | one episode ≥ 45 min | 30 minutes is below the line |
| Invalid picks | successes > attempts, or ≥ 30 attempts while the camera saw < 50 objects | Any length. Quarantine before reporting. |
| Duplicates | any duplicated bucket | |
| Clock label | any mismatch | |

Invalid, duplicate, and mislabeled rows are Data Engineering. Fix them before an external number uses that asset.

## How to tell causes apart

- All target classes drop together and air is low: one Field Service incident. Do not open one Perception ticket per class. The sibling robot on the same belt is the control.
- One class drops, air is normal, camera is ok, the other classes pass: Perception.
- Camera is `dirty_lens` or `offline`: Field Service. Composition from that camera is invalid until the hardware is back. Compare the other scanner on the line before you tell the customer the material changed.
- High confidence does not mean the class is right. A confident model can pick the protected commodity.
- A model deploy timestamp is not the start of customer impact. Impact starts at the first picking bucket.
- Scanner share moves, camera ok, hand sort agrees, robot success stays ≥ 90% and the robot is at the 45 pick cap: the plant changed, the robot did not. Customer Success. Say the robot was saturated if picks per minute hit 45.
- `status = commissioning`: put the finding on the acceptance scorecard. Do not open a production incident unless it is safety. Two failures on one robot can be two teams.
- `PLANNED_PM` and a known blip already in `asset_events`: do not page it again. You may cite it in the scorecard.
- `hits_protected_product = YES` and the island is still open this morning: P1. Recommend the site pause that robot. You do not pause it yourself. Notify Customer Success in the handoff. The CSV route is Perception.

## Priority

- P1 — happening now: safety, a customer on a down robot, or the arm is taking the protected commodity.
- P2 — acceptance is due today, a sensor is making composition unusable, or a real incident ended and nobody logged it.
- P3 — data is wrong and must be fixed before a customer sees a number. The plant is not in immediate danger.

An ended Saturday failure is not P1 on Monday. It is P2 if nobody logged it.

## Routes

Use these names exactly: Field Service, Perception, Deployment Engineering, Customer Success, Data Engineering.

There is no separate safety team. An unresolved e-stop goes to Field Service. Never tell the caller to bypass it.
