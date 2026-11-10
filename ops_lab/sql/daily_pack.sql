-- Northline daily pack. Each block runs on its own.
-- Metric rules match playbooks/daily_monitoring.md.
-- Times labeled start_pt / end_pt_exclusive are Pacific Time.
-- A bucket timestamp is the start of a 15-minute bucket. end_pt_exclusive is the end.
-- Use telemetry_dedup for every metric except duplicate_buckets.

-- [query: open_tickets]
-- Open customer work. Closed tickets stay closed.
SELECT
  ticket_id,
  opened_at_pt,
  facility_id,
  asset_id,
  channel,
  caller_name,
  caller_role,
  summary
FROM tickets
WHERE status = 'open'
ORDER BY opened_at_pt;

-- [query: recent_shift_logs]
-- What the previous analysts left. Verify claims against telemetry.
SELECT shift_date, author, body
FROM shift_logs
ORDER BY shift_date;

-- [query: recent_events]
-- Deploys, planned work, and unverified customer reports.
SELECT event_id, event_time_pt, facility_id, asset_id, event_type, summary
FROM asset_events
ORDER BY event_time_pt;

-- [query: estop_or_fault_islands]
-- Unplanned robot faults during scheduled time. Planned PM is excluded.
WITH bad AS (
  SELECT asset_id, bucket_epoch, fault_code, estop, robot_state
  FROM telemetry_dedup
  WHERE scheduled = 1
    AND COALESCE(fault_code, '') != 'PLANNED_PM'
    AND (
      estop = 1
      OR robot_state = 'fault'
      OR robot_state = 'offline'
    )
),
seq AS (
  SELECT
    *,
    bucket_epoch / 900 - ROW_NUMBER() OVER (
      PARTITION BY asset_id ORDER BY bucket_epoch
    ) AS grp
  FROM bad
)
SELECT
  asset_id,
  MAX(fault_code) AS fault_code,
  strftime('%Y-%m-%d %H:%M', datetime(MIN(bucket_epoch), 'unixepoch', '-8 hours')) AS start_pt,
  strftime('%Y-%m-%d %H:%M', datetime(MAX(bucket_epoch) + 900, 'unixepoch', '-8 hours')) AS end_pt_exclusive,
  COUNT(*) AS buckets,
  COUNT(*) * 15 AS minutes
FROM seq
GROUP BY asset_id, grp
HAVING COUNT(*) >= 2
ORDER BY start_pt, asset_id;

-- [query: off_target_islands]
-- Share of attempts that are not a target commodity. Threshold 8% for at least 60 minutes.
-- hits_protected_product = YES means the gripper is taking the commodity the line is supposed to keep.
WITH off AS (
  SELECT p.asset_id, p.bucket_epoch, p.commodity AS off_commodity
  FROM telemetry_picks p
  WHERE NOT EXISTS (
    SELECT 1
    FROM asset_targets g
    WHERE g.asset_id = p.asset_id AND g.commodity = p.commodity
  )
),
bad AS (
  SELECT
    t.asset_id,
    t.bucket_epoch,
    t.picks_attempted,
    t.picks_off_target,
    o.off_commodity,
    l.protected_commodity
  FROM telemetry_dedup t
  JOIN assets a ON a.asset_id = t.asset_id
  JOIN lines l ON l.line_id = a.line_id
  JOIN off o ON o.asset_id = t.asset_id AND o.bucket_epoch = t.bucket_epoch
  WHERE t.scheduled = 1
    AND t.belt_state = 'running'
    AND t.robot_state = 'picking'
    AND t.picks_attempted >= 30
    AND t.picks_off_target * 1.0 / t.picks_attempted >= 0.08
),
seq AS (
  SELECT
    *,
    bucket_epoch / 900 - ROW_NUMBER() OVER (
      PARTITION BY asset_id ORDER BY bucket_epoch
    ) AS grp
  FROM bad
)
SELECT
  asset_id,
  MAX(off_commodity) AS top_off_target,
  MAX(protected_commodity) AS protected_commodity,
  CASE
    WHEN MAX(off_commodity) = MAX(protected_commodity) THEN 'YES'
    ELSE 'NO'
  END AS hits_protected_product,
  strftime('%Y-%m-%d %H:%M', datetime(MIN(bucket_epoch), 'unixepoch', '-8 hours')) AS start_pt,
  strftime('%Y-%m-%d %H:%M', datetime(MAX(bucket_epoch) + 900, 'unixepoch', '-8 hours')) AS end_pt_exclusive,
  COUNT(*) AS buckets,
  ROUND(SUM(picks_off_target) * 1.0 / SUM(picks_attempted), 3) AS off_target_rate
FROM seq
GROUP BY asset_id, grp
HAVING COUNT(*) >= 4
ORDER BY start_pt, asset_id;

-- [query: low_target_success_islands]
-- Target success = target successes / target attempts. Not an average of bucket rates.
-- Off-target attempts are excluded. Invalid pick math is excluded.
-- Threshold 85% for at least 60 minutes. A weekly average can hide this.
WITH bad AS (
  SELECT
    asset_id,
    bucket_epoch,
    picks_attempted,
    picks_success,
    picks_off_target
  FROM telemetry_dedup
  WHERE scheduled = 1
    AND belt_state = 'running'
    AND burden_objects_per_frame >= 8
    AND robot_state = 'picking'
    AND (picks_attempted - picks_off_target) > 0
    AND picks_success * 1.0 / (picks_attempted - picks_off_target) < 0.85
    AND NOT (
      picks_success > picks_attempted
      OR (picks_attempted >= 30 AND objects_detected < 50)
    )
),
seq AS (
  SELECT
    *,
    bucket_epoch / 900 - ROW_NUMBER() OVER (
      PARTITION BY asset_id ORDER BY bucket_epoch
    ) AS grp
  FROM bad
)
SELECT
  asset_id,
  strftime('%Y-%m-%d %H:%M', datetime(MIN(bucket_epoch), 'unixepoch', '-8 hours')) AS start_pt,
  strftime('%Y-%m-%d %H:%M', datetime(MAX(bucket_epoch) + 900, 'unixepoch', '-8 hours')) AS end_pt_exclusive,
  COUNT(*) AS buckets,
  ROUND(SUM(picks_success) * 1.0 / SUM(picks_attempted - picks_off_target), 3) AS target_success_rate
FROM seq
GROUP BY asset_id, grp
HAVING COUNT(*) >= 4
ORDER BY start_pt, asset_id;

-- [query: low_commodity_success_islands]
-- Same threshold, per target commodity. The blended rate can pass while one class fails.
WITH bad AS (
  SELECT
    p.asset_id,
    p.commodity,
    p.bucket_epoch,
    p.attempted,
    p.success
  FROM telemetry_picks p
  JOIN telemetry_dedup t
    ON t.asset_id = p.asset_id AND t.bucket_epoch = p.bucket_epoch
  JOIN asset_targets g
    ON g.asset_id = p.asset_id AND g.commodity = p.commodity
  WHERE t.scheduled = 1
    AND t.belt_state = 'running'
    AND t.burden_objects_per_frame >= 8
    AND t.robot_state = 'picking'
    AND p.attempted >= 10
    AND p.success * 1.0 / p.attempted < 0.85
    AND NOT (
      t.picks_success > t.picks_attempted
      OR (t.picks_attempted >= 30 AND t.objects_detected < 50)
    )
),
seq AS (
  SELECT
    *,
    bucket_epoch / 900 - ROW_NUMBER() OVER (
      PARTITION BY asset_id, commodity ORDER BY bucket_epoch
    ) AS grp
  FROM bad
)
SELECT
  asset_id,
  commodity,
  strftime('%Y-%m-%d %H:%M', datetime(MIN(bucket_epoch), 'unixepoch', '-8 hours')) AS start_pt,
  strftime('%Y-%m-%d %H:%M', datetime(MAX(bucket_epoch) + 900, 'unixepoch', '-8 hours')) AS end_pt_exclusive,
  COUNT(*) AS buckets,
  ROUND(SUM(success) * 1.0 / SUM(attempted), 3) AS success_rate
FROM seq
GROUP BY asset_id, commodity, grp
HAVING COUNT(*) >= 4
ORDER BY asset_id, commodity, start_pt;

-- [query: low_air_islands]
-- Gripper supply below 70 psi while the arm is still picking. Status can stay green.
WITH bad AS (
  SELECT asset_id, bucket_epoch, air_psi, picks_attempted, picks_success, picks_off_target
  FROM telemetry_dedup
  WHERE scheduled = 1
    AND robot_state = 'picking'
    AND air_psi < 70
),
seq AS (
  SELECT
    *,
    bucket_epoch / 900 - ROW_NUMBER() OVER (
      PARTITION BY asset_id ORDER BY bucket_epoch
    ) AS grp
  FROM bad
)
SELECT
  asset_id,
  strftime('%Y-%m-%d %H:%M', datetime(MIN(bucket_epoch), 'unixepoch', '-8 hours')) AS start_pt,
  strftime('%Y-%m-%d %H:%M', datetime(MAX(bucket_epoch) + 900, 'unixepoch', '-8 hours')) AS end_pt_exclusive,
  COUNT(*) AS buckets,
  ROUND(AVG(air_psi), 1) AS avg_air_psi,
  ROUND(SUM(picks_success) * 1.0 / NULLIF(SUM(picks_attempted - picks_off_target), 0), 3) AS target_success_rate
FROM seq
GROUP BY asset_id, grp
HAVING COUNT(*) >= 4
ORDER BY start_pt, asset_id;

-- [query: camera_issues]
-- Anything other than camera_health = ok during scheduled time.
-- Nights are excluded, so a min/max that brackets several shifts is an ongoing issue
-- if the bad state is present at each start of shift through the latest bucket.
SELECT
  t.asset_id,
  a.position,
  t.camera_health,
  MIN(strftime('%Y-%m-%d %H:%M', datetime(t.bucket_epoch, 'unixepoch', '-8 hours'))) AS first_scheduled_pt,
  MAX(strftime('%Y-%m-%d %H:%M', datetime(t.bucket_epoch, 'unixepoch', '-8 hours'))) AS last_scheduled_pt,
  COUNT(*) AS scheduled_buckets,
  ROUND(AVG(t.avg_confidence), 3) AS avg_confidence,
  ROUND(SUM(t.unknown_count) * 1.0 / NULLIF(SUM(
    t.pet_count + t.hdpe_count + t.aluminum_count + t.occ_count
    + t.film_count + t.other_count + t.unknown_count
  ), 0), 3) AS unknown_share
FROM telemetry_dedup t
JOIN assets a ON a.asset_id = t.asset_id
WHERE t.scheduled = 1
  AND t.camera_health != 'ok'
GROUP BY t.asset_id, a.position, t.camera_health
ORDER BY first_scheduled_pt, t.asset_id;

-- [query: commodity_shifts]
-- Hourly scanner composition versus the same hour on other days.
-- Daily averages hide a short spike. Camera must be ok or the share is not evidence.
-- Threshold: absolute share change of 8 points, at least 4 running buckets in the hour.
WITH counts AS (
  SELECT
    t.asset_id,
    strftime('%Y-%m-%d', t.bucket_start_utc, '-8 hours') AS pt_date,
    CAST(strftime('%H', t.bucket_start_utc, '-8 hours') AS INTEGER) AS hr,
    COUNT(*) AS buckets,
    SUM(t.pet_count) AS pet,
    SUM(t.hdpe_count) AS hdpe,
    SUM(t.aluminum_count) AS aluminum,
    SUM(t.occ_count) AS occ,
    SUM(t.film_count) AS film,
    SUM(t.other_count) AS other,
    SUM(
      t.pet_count + t.hdpe_count + t.aluminum_count + t.occ_count
      + t.film_count + t.other_count + t.unknown_count
    ) AS objs
  FROM telemetry_dedup t
  JOIN assets a ON a.asset_id = t.asset_id
  WHERE a.asset_type = 'scanner'
    AND t.camera_health = 'ok'
    AND t.scheduled = 1
    AND t.belt_state = 'running'
  GROUP BY t.asset_id, pt_date, hr
  HAVING buckets >= 4 AND objs > 0
),
long AS (
  SELECT asset_id, pt_date, hr, buckets, objs, 'PET' AS commodity, pet AS cnt FROM counts
  UNION ALL
  SELECT asset_id, pt_date, hr, buckets, objs, 'HDPE', hdpe FROM counts
  UNION ALL
  SELECT asset_id, pt_date, hr, buckets, objs, 'AL', aluminum FROM counts
  UNION ALL
  SELECT asset_id, pt_date, hr, buckets, objs, 'OCC', occ FROM counts
  UNION ALL
  SELECT asset_id, pt_date, hr, buckets, objs, 'FILM', film FROM counts
  UNION ALL
  SELECT asset_id, pt_date, hr, buckets, objs, 'OTHER', other FROM counts
),
rated AS (
  SELECT
    asset_id,
    pt_date,
    hr,
    commodity,
    cnt * 1.0 / objs AS share,
    (
      SELECT AVG(o.cnt * 1.0 / o.objs)
      FROM long o
      WHERE o.asset_id = long.asset_id
        AND o.hr = long.hr
        AND o.commodity = long.commodity
        AND o.pt_date != long.pt_date
    ) AS baseline
  FROM long
)
SELECT
  asset_id,
  pt_date,
  printf('%02d:00', hr) AS hour_pt,
  commodity,
  ROUND(share, 3) AS share,
  ROUND(baseline, 3) AS baseline_same_hour,
  ROUND(share - baseline, 3) AS delta
FROM rated
WHERE baseline IS NOT NULL
  AND ABS(share - baseline) >= 0.08
ORDER BY pt_date, hour_pt, asset_id, commodity;

-- [query: robots_at_capacity]
-- At or above 45 picks per minute for at least 60 minutes, with healthy target success.
-- This is saturation, not a robot failure.
WITH hot AS (
  SELECT
    asset_id,
    bucket_epoch,
    picks_attempted,
    picks_success,
    picks_off_target
  FROM telemetry_dedup
  WHERE scheduled = 1
    AND belt_state = 'running'
    AND burden_objects_per_frame >= 8
    AND robot_state = 'picking'
    AND picks_attempted / 15.0 >= 44.5
    AND (picks_attempted - picks_off_target) > 0
    AND picks_success * 1.0 / (picks_attempted - picks_off_target) >= 0.90
),
seq AS (
  SELECT
    *,
    bucket_epoch / 900 - ROW_NUMBER() OVER (
      PARTITION BY asset_id ORDER BY bucket_epoch
    ) AS grp
  FROM hot
)
SELECT
  asset_id,
  strftime('%Y-%m-%d %H:%M', datetime(MIN(bucket_epoch), 'unixepoch', '-8 hours')) AS start_pt,
  strftime('%Y-%m-%d %H:%M', datetime(MAX(bucket_epoch) + 900, 'unixepoch', '-8 hours')) AS end_pt_exclusive,
  COUNT(*) AS buckets,
  ROUND(SUM(picks_attempted) * 1.0 / (COUNT(*) * 15.0), 1) AS picks_per_min,
  ROUND(SUM(picks_success) * 1.0 / SUM(picks_attempted - picks_off_target), 3) AS target_success_rate
FROM seq
GROUP BY asset_id, grp
HAVING COUNT(*) >= 4
ORDER BY start_pt;

-- [query: invalid_pick_rows]
-- Do not report performance from these buckets. One bucket is enough to quarantine the asset's afternoon.
WITH bad AS (
  SELECT asset_id, bucket_epoch, objects_detected, picks_attempted, picks_success
  FROM telemetry_dedup
  WHERE picks_success > picks_attempted
     OR (picks_attempted >= 30 AND objects_detected < 50)
),
seq AS (
  SELECT
    *,
    bucket_epoch / 900 - ROW_NUMBER() OVER (
      PARTITION BY asset_id ORDER BY bucket_epoch
    ) AS grp
  FROM bad
)
SELECT
  asset_id,
  strftime('%Y-%m-%d %H:%M', datetime(MIN(bucket_epoch), 'unixepoch', '-8 hours')) AS start_pt,
  strftime('%Y-%m-%d %H:%M', datetime(MAX(bucket_epoch) + 900, 'unixepoch', '-8 hours')) AS end_pt_exclusive,
  COUNT(*) AS buckets,
  MIN(objects_detected) AS min_objects,
  MAX(picks_attempted) AS max_attempted,
  MAX(picks_success) AS max_success
FROM seq
GROUP BY asset_id, grp
ORDER BY start_pt;

-- [query: duplicate_buckets]
-- Raw telemetry only. Dedup before this and the query goes empty.
SELECT
  asset_id,
  COUNT(*) AS duplicated_buckets,
  MIN(bucket_start_pt) AS first_pt_label,
  MAX(bucket_start_pt) AS last_pt_label
FROM (
  SELECT asset_id, bucket_epoch, MIN(bucket_start_pt) AS bucket_start_pt, COUNT(*) AS copies
  FROM telemetry
  GROUP BY asset_id, bucket_epoch
  HAVING copies > 1
)
GROUP BY asset_id
ORDER BY asset_id;

-- [query: timezone_mismatches]
-- bucket_start_pt is a label. Correct PT is bucket_start_utc minus 8 hours.
-- Do not move an incident onto the bad label.
SELECT
  asset_id,
  COUNT(*) AS buckets,
  MIN(bucket_start_pt) AS example_stored_label,
  MIN(strftime('%Y-%m-%d %H:%M', bucket_start_utc, '-8 hours')) AS example_correct_pt
FROM telemetry_dedup
WHERE bucket_start_pt != strftime('%Y-%m-%d %H:%M', bucket_start_utc, '-8 hours')
GROUP BY asset_id
ORDER BY asset_id;

-- [query: model_versions]
-- A version can change while the plant is closed. Compare first production behavior after it.
SELECT
  asset_id,
  model_version,
  MIN(bucket_start_pt) AS first_bucket_pt_label,
  MAX(bucket_start_pt) AS last_bucket_pt_label,
  COUNT(*) AS buckets
FROM telemetry_dedup
WHERE asset_id IN (
  SELECT asset_id
  FROM telemetry_dedup
  GROUP BY asset_id
  HAVING COUNT(DISTINCT model_version) > 1
)
GROUP BY asset_id, model_version
ORDER BY asset_id, first_bucket_pt_label;

-- [query: commissioning_scorecard]
-- Riverbend window is 2026-11-04 inclusive through 2026-11-08 exclusive.
-- Thresholds are the contract rows in acceptance_criteria. Burn-in is excluded.
WITH robot_window AS (
  SELECT t.*
  FROM telemetry_dedup t
  WHERE t.asset_id IN (SELECT asset_id FROM acceptance_criteria)
    AND t.scheduled = 1
    AND t.bucket_start_pt >= '2026-11-04'
    AND t.bucket_start_pt < '2026-11-08'
),
uptime AS (
  SELECT
    asset_id,
    SUM(CASE WHEN robot_state IN ('picking', 'idle') AND estop = 0 THEN 1 ELSE 0 END) * 1.0
      / COUNT(*) AS actual
  FROM robot_window
  WHERE asset_id LIKE 'RBT-%'
  GROUP BY asset_id
),
ppm AS (
  SELECT
    asset_id,
    SUM(picks_attempted) * 1.0 / (COUNT(*) * 15.0) AS actual
  FROM robot_window
  WHERE robot_state = 'picking'
    AND belt_state = 'running'
    AND burden_objects_per_frame >= 8
    AND NOT (
      picks_success > picks_attempted
      OR (picks_attempted >= 30 AND objects_detected < 50)
    )
  GROUP BY asset_id
),
commodity AS (
  SELECT
    p.asset_id,
    'success_' || p.commodity AS metric,
    SUM(p.success) * 1.0 / SUM(p.attempted) AS actual
  FROM telemetry_picks p
  JOIN robot_window t ON t.asset_id = p.asset_id AND t.bucket_epoch = p.bucket_epoch
  JOIN asset_targets g ON g.asset_id = p.asset_id AND g.commodity = p.commodity
  WHERE t.robot_state = 'picking'
    AND t.belt_state = 'running'
    AND t.burden_objects_per_frame >= 8
    AND p.attempted > 0
  GROUP BY p.asset_id, p.commodity
),
safety AS (
  SELECT
    a.asset_id,
    COALESCE(SUM(CASE WHEN t.estop = 1 THEN 1 ELSE 0 END), 0) * 1.0 AS actual
  FROM assets a
  LEFT JOIN robot_window t ON t.asset_id = a.asset_id
  WHERE a.asset_id IN ('RBT-RVB-01', 'RBT-RVB-02')
  GROUP BY a.asset_id
),
offline_min AS (
  SELECT
    asset_id,
    SUM(CASE WHEN camera_health = 'offline' THEN 15 ELSE 0 END) * 1.0 AS actual
  FROM robot_window
  WHERE asset_id LIKE 'SCN-%'
  GROUP BY asset_id
),
actuals AS (
  SELECT asset_id, 'uptime' AS metric, actual FROM uptime
  UNION ALL
  SELECT asset_id, 'picks_per_min', actual FROM ppm
  UNION ALL
  SELECT asset_id, metric, actual FROM commodity
  UNION ALL
  SELECT asset_id, 'safety_estop_buckets', actual FROM safety
  UNION ALL
  SELECT asset_id, 'max_offline_min', actual FROM offline_min
)
SELECT
  c.asset_id,
  c.metric,
  ROUND(a.actual, 3) AS actual,
  c.comparison,
  c.threshold,
  CASE c.comparison
    WHEN '>=' THEN CASE WHEN a.actual >= c.threshold THEN 'PASS' ELSE 'FAIL' END
    WHEN '<=' THEN CASE WHEN a.actual <= c.threshold THEN 'PASS' ELSE 'FAIL' END
    ELSE 'UNKNOWN'
  END AS result
FROM acceptance_criteria c
JOIN actuals a ON a.asset_id = c.asset_id AND a.metric = c.metric
ORDER BY c.asset_id, c.metric;

-- [query: scanner_audit_deltas]
-- Hand sort versus the infeed scanner over the audit's own hours.
-- WITHIN means the shares agree within 5 points. It is not an acceptance decision.
WITH counts AS (
  SELECT
    t.asset_id,
    a.line_id,
    strftime('%Y-%m-%d', t.bucket_start_utc, '-8 hours') AS pt_date,
    CAST(strftime('%H', t.bucket_start_utc, '-8 hours') AS INTEGER) AS hr,
    SUM(t.pet_count) AS pet,
    SUM(t.hdpe_count) AS hdpe,
    SUM(t.aluminum_count) AS aluminum,
    SUM(t.occ_count) AS occ,
    SUM(t.film_count) AS film,
    SUM(t.other_count) AS other,
    SUM(t.unknown_count) AS unknown
  FROM telemetry_dedup t
  JOIN assets a ON a.asset_id = t.asset_id
  WHERE a.asset_type = 'scanner'
    AND a.position = 'infeed'
    AND t.camera_health = 'ok'
    AND t.scheduled = 1
    AND t.belt_state = 'running'
  GROUP BY t.asset_id, a.line_id, pt_date, hr
),
long AS (
  SELECT asset_id, line_id, pt_date, hr, 'PET' AS commodity, pet AS cnt,
         (pet + hdpe + aluminum + occ + film + other + unknown) AS objs FROM counts
  UNION ALL
  SELECT asset_id, line_id, pt_date, hr, 'HDPE', hdpe,
         (pet + hdpe + aluminum + occ + film + other + unknown) FROM counts
  UNION ALL
  SELECT asset_id, line_id, pt_date, hr, 'AL', aluminum,
         (pet + hdpe + aluminum + occ + film + other + unknown) FROM counts
  UNION ALL
  SELECT asset_id, line_id, pt_date, hr, 'OCC', occ,
         (pet + hdpe + aluminum + occ + film + other + unknown) FROM counts
  UNION ALL
  SELECT asset_id, line_id, pt_date, hr, 'FILM', film,
         (pet + hdpe + aluminum + occ + film + other + unknown) FROM counts
  UNION ALL
  SELECT asset_id, line_id, pt_date, hr, 'OTHER', other,
         (pet + hdpe + aluminum + occ + film + other + unknown) FROM counts
)
SELECT
  m.audit_date,
  m.line_id,
  l.asset_id,
  m.commodity,
  m.sample_size,
  ROUND(SUM(l.cnt) * 1.0 / SUM(l.objs), 3) AS scanner_share,
  m.share AS audit_share,
  ROUND(SUM(l.cnt) * 1.0 / SUM(l.objs) - m.share, 3) AS delta,
  CASE
    WHEN ABS(SUM(l.cnt) * 1.0 / SUM(l.objs) - m.share) <= 0.05 THEN 'WITHIN'
    ELSE 'OUTSIDE'
  END AS within_5_points,
  m.note
FROM manual_audits m
JOIN long l
  ON l.line_id = m.line_id
 AND l.pt_date = m.audit_date
 AND l.commodity = m.commodity
 AND l.hr >= m.hour_start
 AND l.hr < m.hour_end
GROUP BY m.audit_id, m.audit_date, m.line_id, l.asset_id, m.commodity, m.sample_size, m.share, m.note
ORDER BY m.audit_date, m.line_id, m.commodity;

-- [query: planned_maintenance]
-- Context only. Do not open a production incident.
SELECT
  asset_id,
  strftime('%Y-%m-%d %H:%M', datetime(MIN(bucket_epoch), 'unixepoch', '-8 hours')) AS start_pt,
  strftime('%Y-%m-%d %H:%M', datetime(MAX(bucket_epoch) + 900, 'unixepoch', '-8 hours')) AS end_pt_exclusive,
  COUNT(*) * 15 AS minutes,
  MAX(fault_code) AS fault_code
FROM telemetry_dedup
WHERE fault_code = 'PLANNED_PM'
GROUP BY asset_id
ORDER BY start_pt;

-- [query: benign_flow]
-- Empty belts and stopped belts, collapsed to the line.
-- Empty: Customer Success only if one episode is 60 minutes or longer.
-- Stopped: unplanned downtime only if one episode is 45 minutes or longer.
WITH line_buckets AS (
  SELECT
    a.line_id,
    t.belt_state,
    t.bucket_epoch
  FROM telemetry_dedup t
  JOIN assets a ON a.asset_id = t.asset_id
  WHERE t.scheduled = 1
    AND t.belt_state IN ('empty', 'stopped')
  GROUP BY a.line_id, t.belt_state, t.bucket_epoch
),
seq AS (
  SELECT
    *,
    bucket_epoch / 900 - ROW_NUMBER() OVER (
      PARTITION BY line_id, belt_state ORDER BY bucket_epoch
    ) AS grp
  FROM line_buckets
)
SELECT
  line_id,
  belt_state,
  strftime('%Y-%m-%d %H:%M', datetime(MIN(bucket_epoch), 'unixepoch', '-8 hours')) AS start_pt,
  strftime('%Y-%m-%d %H:%M', datetime(MAX(bucket_epoch) + 900, 'unixepoch', '-8 hours')) AS end_pt_exclusive,
  COUNT(*) * 15 AS minutes,
  CASE
    WHEN belt_state = 'empty' AND COUNT(*) * 15 >= 60 THEN 'REVIEW'
    WHEN belt_state = 'stopped' AND COUNT(*) * 15 >= 45 THEN 'REVIEW'
    ELSE 'BELOW THRESHOLD'
  END AS escalation
FROM seq
GROUP BY line_id, belt_state, grp
ORDER BY start_pt, line_id;
