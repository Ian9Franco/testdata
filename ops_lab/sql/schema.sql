PRAGMA foreign_keys = ON;

-- Practice schema for a recycling-robotics fleet.
-- telemetry has no UNIQUE(asset_id, bucket_epoch) on purpose: a duplicate-row
-- bug is part of the scenario. Use the telemetry_dedup view for every
-- metric except the duplicate audit.

CREATE TABLE facilities (
  facility_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  city TEXT NOT NULL,
  state TEXT NOT NULL,
  customer_type TEXT NOT NULL,
  tons_per_day INTEGER NOT NULL
);

CREATE TABLE lines (
  line_id TEXT PRIMARY KEY,
  facility_id TEXT NOT NULL REFERENCES facilities(facility_id),
  name TEXT NOT NULL,
  line_type TEXT NOT NULL,
  protected_commodity TEXT
);

CREATE TABLE assets (
  asset_id TEXT PRIMARY KEY,
  facility_id TEXT NOT NULL REFERENCES facilities(facility_id),
  line_id TEXT NOT NULL REFERENCES lines(line_id),
  asset_type TEXT NOT NULL CHECK (asset_type IN ('robot', 'scanner')),
  name TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('production', 'commissioning')),
  position TEXT NOT NULL,
  installed_on TEXT NOT NULL,
  model_version TEXT NOT NULL,
  base_ppm REAL,
  contract_ppm REAL,
  contract_success REAL,
  contract_uptime REAL
);

CREATE TABLE asset_targets (
  asset_id TEXT NOT NULL REFERENCES assets(asset_id),
  commodity TEXT NOT NULL,
  PRIMARY KEY (asset_id, commodity)
);

CREATE TABLE telemetry (
  asset_id TEXT NOT NULL REFERENCES assets(asset_id),
  bucket_epoch INTEGER NOT NULL,
  bucket_start_utc TEXT NOT NULL,
  bucket_start_pt TEXT NOT NULL,
  belt_state TEXT NOT NULL,
  objects_detected INTEGER NOT NULL,
  picks_attempted INTEGER NOT NULL,
  picks_success INTEGER NOT NULL,
  picks_off_target INTEGER NOT NULL,
  avg_confidence REAL,
  camera_health TEXT NOT NULL,
  robot_state TEXT,
  fault_code TEXT,
  estop INTEGER NOT NULL,
  air_psi REAL,
  burden_objects_per_frame REAL NOT NULL,
  pet_count INTEGER NOT NULL,
  hdpe_count INTEGER NOT NULL,
  aluminum_count INTEGER NOT NULL,
  occ_count INTEGER NOT NULL,
  film_count INTEGER NOT NULL,
  other_count INTEGER NOT NULL,
  unknown_count INTEGER NOT NULL,
  scheduled INTEGER NOT NULL,
  model_version TEXT NOT NULL
);

CREATE TABLE telemetry_picks (
  asset_id TEXT NOT NULL REFERENCES assets(asset_id),
  bucket_epoch INTEGER NOT NULL,
  commodity TEXT NOT NULL,
  attempted INTEGER NOT NULL,
  success INTEGER NOT NULL,
  PRIMARY KEY (asset_id, bucket_epoch, commodity)
);

CREATE TABLE asset_events (
  event_id TEXT PRIMARY KEY,
  facility_id TEXT NOT NULL REFERENCES facilities(facility_id),
  asset_id TEXT REFERENCES assets(asset_id),
  event_time_pt TEXT NOT NULL,
  event_type TEXT NOT NULL,
  summary TEXT NOT NULL
);

CREATE TABLE tickets (
  ticket_id TEXT PRIMARY KEY,
  opened_at_pt TEXT NOT NULL,
  facility_id TEXT NOT NULL REFERENCES facilities(facility_id),
  asset_id TEXT REFERENCES assets(asset_id),
  channel TEXT NOT NULL,
  caller_name TEXT NOT NULL,
  caller_role TEXT NOT NULL,
  status TEXT NOT NULL,
  summary TEXT NOT NULL,
  body TEXT NOT NULL
);

CREATE TABLE shift_logs (
  shift_date TEXT PRIMARY KEY,
  author TEXT NOT NULL,
  body TEXT NOT NULL
);

CREATE TABLE manual_audits (
  audit_id TEXT PRIMARY KEY,
  line_id TEXT NOT NULL REFERENCES lines(line_id),
  audit_date TEXT NOT NULL,
  hour_start INTEGER NOT NULL,
  hour_end INTEGER NOT NULL,
  commodity TEXT NOT NULL,
  share REAL NOT NULL,
  sample_size INTEGER NOT NULL,
  note TEXT NOT NULL
);

CREATE TABLE acceptance_criteria (
  asset_id TEXT NOT NULL REFERENCES assets(asset_id),
  metric TEXT NOT NULL,
  comparison TEXT NOT NULL CHECK (comparison IN ('>=', '<=')),
  threshold REAL NOT NULL,
  PRIMARY KEY (asset_id, metric)
);

CREATE TABLE escalation_teams (
  team TEXT PRIMARY KEY,
  owns TEXT NOT NULL,
  sla TEXT NOT NULL
);

CREATE INDEX idx_telemetry_asset_epoch ON telemetry(asset_id, bucket_epoch);
CREATE INDEX idx_picks_asset_epoch ON telemetry_picks(asset_id, bucket_epoch);

CREATE VIEW telemetry_dedup AS
WITH ranked AS (
  SELECT
    asset_id,
    bucket_epoch,
    bucket_start_utc,
    bucket_start_pt,
    belt_state,
    objects_detected,
    picks_attempted,
    picks_success,
    picks_off_target,
    avg_confidence,
    camera_health,
    robot_state,
    fault_code,
    estop,
    air_psi,
    burden_objects_per_frame,
    pet_count,
    hdpe_count,
    aluminum_count,
    occ_count,
    film_count,
    other_count,
    unknown_count,
    scheduled,
    model_version,
    ROW_NUMBER() OVER (
      PARTITION BY asset_id, bucket_epoch
      ORDER BY rowid
    ) AS rn
  FROM telemetry
)
SELECT
  asset_id,
  bucket_epoch,
  bucket_start_utc,
  bucket_start_pt,
  belt_state,
  objects_detected,
  picks_attempted,
  picks_success,
  picks_off_target,
  avg_confidence,
  camera_health,
  robot_state,
  fault_code,
  estop,
  air_psi,
  burden_objects_per_frame,
  pet_count,
  hdpe_count,
  aluminum_count,
  occ_count,
  film_count,
  other_count,
  unknown_count,
  scheduled,
  model_version
FROM ranked
WHERE rn = 1;
