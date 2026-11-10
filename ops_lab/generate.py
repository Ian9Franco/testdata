"""Build the practice database. Deterministic: no random noise."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ops_lab.catalog import (
    ASSETS,
    AUDITS,
    CAT_WINDOW_END,
    CAT_WINDOW_START,
    EVENTS,
    FACILITIES,
    LEAK_DOWNSTREAM,
    LEAK_INFEED,
    LINES,
    MIX,
    OBJECT_FACTOR,
    PT,
    RANGE_END,
    RANGE_START,
    RVB_ROBOT_METRICS,
    SCHEDULE,
    SHIFT_LOGS,
    TEAMS,
    TICKETS,
)
from ops_lab.queries import load_queries

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = Path(__file__).resolve().parent / "sql" / "schema.sql"
DB_PATH = ROOT / "data" / "glacier_ops.sqlite"

COMMODITIES = ("PET", "HDPE", "AL", "OCC", "FILM", "OTHER")
UTC = timezone.utc

LEAK_START = datetime(2026, 11, 5, 13, 0, tzinfo=PT)
LEAK_END = datetime(2026, 11, 5, 17, 0, tzinfo=PT)
AIR_START = datetime(2026, 11, 7, 5, 0, tzinfo=PT)
AIR_END = datetime(2026, 11, 7, 11, 0, tzinfo=PT)
MODEL_CUT = datetime(2026, 11, 6, 2, 0, tzinfo=PT)
DIRTY_START = datetime(2026, 11, 6, 8, 0, tzinfo=PT)
ESTOP_START = datetime(2026, 11, 9, 6, 45, tzinfo=PT)
PM_START = datetime(2026, 11, 4, 9, 0, tzinfo=PT)
PM_END = datetime(2026, 11, 4, 11, 0, tzinfo=PT)
OFFLINE_START = datetime(2026, 11, 6, 8, 0, tzinfo=PT)
OFFLINE_END = datetime(2026, 11, 6, 9, 0, tzinfo=PT)
BAD_START = datetime(2026, 11, 6, 14, 0, tzinfo=PT)
BAD_END = datetime(2026, 11, 6, 17, 0, tzinfo=PT)
SCAN_OFF_START = datetime(2026, 11, 7, 9, 0, tzinfo=PT)
SCAN_OFF_END = datetime(2026, 11, 7, 14, 0, tzinfo=PT)
EMPTY_START = datetime(2026, 11, 6, 10, 0, tzinfo=PT)
EMPTY_END = datetime(2026, 11, 6, 10, 45, tzinfo=PT)
STOP_START = datetime(2026, 11, 3, 13, 0, tzinfo=PT)
STOP_END = datetime(2026, 11, 3, 13, 30, tzinfo=PT)


def in_range(moment: datetime, start: datetime, end: datetime) -> bool:
    return start <= moment < end


def scheduled_hours(facility_id: str, moment: datetime) -> bool:
    if moment.weekday() == 6:
        return False
    key = "saturday" if moment.weekday() == 5 else "weekday"
    open_hour, close_hour = SCHEDULE[facility_id][key]
    return open_hour <= moment.hour < close_hour


def line_condition(line: dict, moment: datetime) -> dict:
    scheduled = 1 if scheduled_hours(line["facility_id"], moment) else 0
    if not scheduled:
        return {"scheduled": 0, "belt_state": "stopped", "burden": 0.0}
    if line["line_id"] == "LN-PAC-CON" and in_range(moment, EMPTY_START, EMPTY_END):
        return {"scheduled": 1, "belt_state": "empty", "burden": 1.2}
    if line["line_id"] == "LN-LKS-CON" and in_range(moment, STOP_START, STOP_END):
        return {"scheduled": 1, "belt_state": "stopped", "burden": 0.0}
    burden = 15.0 if 8 <= moment.hour < 15 else 11.0
    return {"scheduled": 1, "belt_state": "running", "burden": burden}


def detection_mix(asset_id: str, line_type: str, moment: datetime) -> dict:
    if asset_id in {"SCN-LKS-01", "RBT-LKS-01"} and in_range(moment, LEAK_START, LEAK_END):
        return LEAK_INFEED
    if asset_id == "SCN-LKS-02" and in_range(moment, LEAK_START, LEAK_END):
        return LEAK_DOWNSTREAM
    return MIX[line_type]


def split_counts(n: int, weights: dict) -> dict[str, int]:
    counts = {name: 0 for name in COMMODITIES}
    counts["unknown"] = 0
    if n <= 0:
        return counts
    total = sum(weights.values())
    raw = {name: n * weights.get(name, 0) / total for name in COMMODITIES}
    counts.update({name: int(raw[name]) for name in COMMODITIES})
    remainder = n - sum(counts[name] for name in COMMODITIES)
    order = sorted(COMMODITIES, key=lambda name: raw[name] - counts[name], reverse=True)
    for index in range(remainder):
        counts[order[index % len(order)]] += 1
    return counts


def move_unknown(counts: dict[str, int], fraction: float) -> dict[str, int]:
    out = dict(counts)
    moved = 0
    for name in COMMODITIES:
        take = min(out[name], int(round(out[name] * fraction)))
        out[name] -= take
        moved += take
    out["unknown"] += moved
    return out


def build_picks(attempts: int, targets: list[str], mix: dict, off_fraction: float, off_commodity: str, rate_for) -> list[tuple]:
    off_attempts = int(round(attempts * off_fraction))
    target_total = attempts - off_attempts
    weights = {name: mix[name] for name in targets}
    target_counts = split_counts(target_total, weights)
    rows = []
    for commodity in targets:
        attempted = target_counts[commodity]
        success = min(attempted, int(round(attempted * rate_for(commodity))))
        rows.append((commodity, attempted, success))
    if off_attempts:
        rows.append((off_commodity, off_attempts, off_attempts))
    return rows


def object_count(line_type: str, condition: dict) -> int:
    if condition["scheduled"] == 0 or condition["belt_state"] == "stopped":
        return 0
    if condition["belt_state"] == "empty":
        return int(round(condition["burden"] * 8))
    return int(round(condition["burden"] * OBJECT_FACTOR[line_type]))


def synthesize(asset: dict, line: dict, moment: datetime, condition: dict) -> tuple[dict, list[tuple]]:
    mix = detection_mix(asset["asset_id"], line["line_type"], moment)
    objects = object_count(line["line_type"], condition)
    counts = split_counts(objects, mix)
    camera = "ok"
    confidence = 0.94 if objects else None
    robot_state = None
    fault = None
    estop = 0
    air = None
    model = asset["model_version"]
    picks: list[tuple] = []
    attempted = success = off_target = 0
    asset_id = asset["asset_id"]

    if asset["asset_type"] == "scanner":
        if asset_id == "SCN-CDR-02" and moment >= DIRTY_START:
            camera = "dirty_lens"
            confidence = 0.61 if condition["scheduled"] else None
            counts = move_unknown(counts, 0.45)
        if asset_id == "SCN-RVB-03" and in_range(moment, SCAN_OFF_START, SCAN_OFF_END):
            camera = "offline"
            confidence = None
            objects = 0
            counts = split_counts(0, mix)
    else:
        if asset_id == "RBT-HBR-04" and moment >= MODEL_CUT:
            model = "v2.14.0"
        picking = condition["scheduled"] == 1 and condition["belt_state"] == "running"
        if asset_id == "RBT-PAC-01" and in_range(moment, PM_START, PM_END):
            robot_state = "maintenance"
            fault = "PLANNED_PM"
            picking = False
        elif asset_id == "RBT-CDR-01" and moment >= ESTOP_START and condition["scheduled"]:
            robot_state = "fault"
            fault = "ESTOP"
            estop = 1
            air = 96.0
            picking = False
        elif asset_id == "RBT-RVB-01" and in_range(moment, OFFLINE_START, OFFLINE_END):
            robot_state = "offline"
            fault = "OFFLINE"
            picking = False
        elif not condition["scheduled"]:
            robot_state = "offline"
        elif condition["belt_state"] != "running":
            robot_state = "idle"
        else:
            robot_state = "picking"

        if picking:
            low_air = asset_id == "RBT-HBR-02" and in_range(moment, AIR_START, AIR_END)
            air = 58.0 if low_air else 96.0
            ppm = 45 if asset_id == "RBT-LKS-01" and in_range(moment, LEAK_START, LEAK_END) else asset["base_ppm"]
            attempts = int(round(ppm * 15))
            regression = asset_id == "RBT-HBR-04" and moment >= MODEL_CUT
            off_fraction = 0.30 if regression else 0.02
            off_commodity = "OCC" if regression else "FILM"

            def rate_for(commodity: str, low_air: bool = low_air) -> float:
                if low_air:
                    return 0.62
                if asset_id == "RBT-RVB-01" and commodity == "AL":
                    return 0.71
                return 0.93

            picks = build_picks(attempts, asset["targets"], mix, off_fraction, off_commodity, rate_for)
            if asset_id == "RBT-PAC-03" and in_range(moment, BAD_START, BAD_END):
                picks = []
                attempted, success, off_target = 40, 620, 0
                objects = 20
                counts = split_counts(objects, mix)
                confidence = 0.94
            else:
                attempted = sum(row[1] for row in picks)
                off_target = sum(row[1] for row in picks if row[0] not in asset["targets"])
                success = sum(row[2] for row in picks if row[0] in asset["targets"])

    utc = moment.astimezone(UTC)
    label = utc.strftime("%Y-%m-%d %H:%M") if asset_id == "SCN-LKS-02" else moment.strftime("%Y-%m-%d %H:%M")
    row = {
        "asset_id": asset_id,
        "bucket_epoch": int(moment.timestamp()),
        "bucket_start_utc": utc.strftime("%Y-%m-%d %H:%M:%S"),
        "bucket_start_pt": label,
        "belt_state": condition["belt_state"],
        "objects_detected": objects,
        "picks_attempted": attempted,
        "picks_success": success,
        "picks_off_target": off_target,
        "avg_confidence": confidence,
        "camera_health": camera,
        "robot_state": robot_state,
        "fault_code": fault,
        "estop": estop,
        "air_psi": air,
        "burden_objects_per_frame": condition["burden"],
        "pet_count": counts["PET"],
        "hdpe_count": counts["HDPE"],
        "aluminum_count": counts["AL"],
        "occ_count": counts["OCC"],
        "film_count": counts["FILM"],
        "other_count": counts["OTHER"],
        "unknown_count": counts["unknown"],
        "scheduled": condition["scheduled"],
        "model_version": model,
    }
    return row, picks


def build(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA.read_text())
    conn.executemany(
        "INSERT INTO facilities VALUES (?, ?, ?, ?, ?, ?)",
        FACILITIES,
    )
    conn.executemany(
        "INSERT INTO lines VALUES (?, ?, ?, ?, ?)",
        LINES,
    )
    conn.executemany(
        """
        INSERT INTO assets (
          asset_id, facility_id, line_id, asset_type, name, status, position,
          installed_on, model_version, base_ppm, contract_ppm, contract_success, contract_uptime
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                asset["asset_id"],
                asset["facility_id"],
                asset["line_id"],
                asset["asset_type"],
                asset["name"],
                asset["status"],
                asset["position"],
                asset["installed_on"],
                asset["model_version"],
                asset["base_ppm"],
                asset["contract_ppm"],
                asset["contract_success"],
                asset["contract_uptime"],
            )
            for asset in ASSETS
        ],
    )
    conn.executemany(
        "INSERT INTO asset_targets VALUES (?, ?)",
        [(asset["asset_id"], commodity) for asset in ASSETS for commodity in asset["targets"]],
    )
    conn.executemany("INSERT INTO escalation_teams VALUES (?, ?, ?)", TEAMS)
    conn.executemany(
        "INSERT INTO asset_events VALUES (?, ?, ?, ?, ?, ?)",
        EVENTS,
    )
    conn.executemany(
        """
        INSERT INTO tickets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                ticket["ticket_id"],
                ticket["opened_at_pt"],
                ticket["facility_id"],
                ticket["asset_id"],
                ticket["channel"],
                ticket["caller_name"],
                ticket["caller_role"],
                ticket["status"],
                ticket["summary"],
                ticket["body"].strip(),
            )
            for ticket in TICKETS
        ],
    )
    conn.executemany("INSERT INTO shift_logs VALUES (?, ?, ?)", SHIFT_LOGS)
    audit_rows = []
    for audit_id, line_id, audit_date, hour_start, hour_end, shares, sample_size, note in AUDITS:
        for commodity, share in shares:
            audit_rows.append(
                (f"{audit_id}-{commodity}", line_id, audit_date, hour_start, hour_end, commodity, share, sample_size, note)
            )
    conn.executemany(
        "INSERT INTO manual_audits VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        audit_rows,
    )
    criteria = []
    for asset_id, metrics in RVB_ROBOT_METRICS.items():
        for metric, comparison, threshold in metrics:
            criteria.append((asset_id, metric, comparison, threshold))
    for asset in ASSETS:
        if asset["facility_id"] == "F-RVB" and asset["asset_type"] == "scanner":
            criteria.append((asset["asset_id"], "max_offline_min", "<=", 60))
    conn.executemany(
        "INSERT INTO acceptance_criteria VALUES (?, ?, ?, ?)",
        criteria,
    )

    lines = {line_id: {"line_id": line_id, "facility_id": facility_id, "line_type": line_type} for line_id, facility_id, _name, line_type, _protected in LINES}
    assets_by_line: dict[str, list] = {}
    for asset in ASSETS:
        assets_by_line.setdefault(asset["line_id"], []).append(asset)

    telemetry = []
    picks = []
    moment = RANGE_START
    while moment < RANGE_END:
        for line_id, line in lines.items():
            condition = line_condition(line, moment)
            for asset in assets_by_line[line_id]:
                row, pick_rows = synthesize(asset, line, moment, condition)
                telemetry.append(row)
                for commodity, attempted, success in pick_rows:
                    picks.append((asset["asset_id"], row["bucket_epoch"], commodity, attempted, success))
        moment += timedelta(minutes=15)

    duplicated = [
        dict(row)
        for row in telemetry
        if row["asset_id"] == "SCN-HBR-04" and row["bucket_start_pt"].startswith("2026-11-03")
    ]
    telemetry.extend(duplicated)

    columns = [
        "asset_id",
        "bucket_epoch",
        "bucket_start_utc",
        "bucket_start_pt",
        "belt_state",
        "objects_detected",
        "picks_attempted",
        "picks_success",
        "picks_off_target",
        "avg_confidence",
        "camera_health",
        "robot_state",
        "fault_code",
        "estop",
        "air_psi",
        "burden_objects_per_frame",
        "pet_count",
        "hdpe_count",
        "aluminum_count",
        "occ_count",
        "film_count",
        "other_count",
        "unknown_count",
        "scheduled",
        "model_version",
    ]
    conn.executemany(
        f"INSERT INTO telemetry ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})",
        [tuple(row[column] for column in columns) for row in telemetry],
    )
    conn.executemany(
        "INSERT INTO telemetry_picks VALUES (?, ?, ?, ?, ?)",
        picks,
    )
    conn.commit()


def share(conn: sqlite3.Connection, asset_id: str, start: str, end: str, commodity_column: str) -> float | None:
    row = conn.execute(
        f"""
        SELECT SUM({commodity_column}) * 1.0 / NULLIF(SUM(
          pet_count + hdpe_count + aluminum_count + occ_count + film_count + other_count + unknown_count
        ), 0)
        FROM telemetry_dedup
        WHERE asset_id = ?
          AND strftime('%Y-%m-%d %H:%M', bucket_start_utc, '-8 hours') >= ?
          AND strftime('%Y-%m-%d %H:%M', bucket_start_utc, '-8 hours') < ?
        """,
        (asset_id, start, end),
    ).fetchone()
    return None if row[0] is None else float(row[0])


def write_inbox_and_snapshot(conn: sqlite3.Connection) -> None:
    inbox = ROOT / "inbox"
    inbox.mkdir(exist_ok=True)
    for ticket in TICKETS:
        (inbox / f"{ticket['ticket_id']}.md").write_text(
            f"# {ticket['ticket_id']}\n\n"
            f"- Opened: {ticket['opened_at_pt']} PT\n"
            f"- Status: {ticket['status']}\n"
            f"- Facility: {ticket['facility_id']}\n"
            f"- Asset recorded: {ticket['asset_id'] or 'not specified'}\n"
            f"- Channel: {ticket['channel']}\n"
            f"- Caller: {ticket['caller_name']}, {ticket['caller_role']}\n\n"
            f"{ticket['body'].strip()}\n"
        )
    for shift_date, author, body in SHIFT_LOGS:
        (inbox / f"shift_log_{shift_date}.md").write_text(
            f"# Shift log {shift_date}\n\nAuthor: {author}\n\n{body}\n"
        )

    qc_raw = conn.execute(
        """
        SELECT SUM(pet_count)
        FROM telemetry
        WHERE asset_id = 'SCN-HBR-04'
          AND bucket_start_pt >= '2026-11-03'
          AND bucket_start_pt < '2026-11-04'
        """
    ).fetchone()[0]
    container_pet = conn.execute(
        """
        SELECT SUM(pet_count)
        FROM telemetry_dedup
        WHERE asset_id = 'SCN-HBR-01'
          AND bucket_start_pt >= '2026-11-03'
          AND bucket_start_pt < '2026-11-04'
        """
    ).fetchone()[0]
    filtered = conn.execute(
        """
        SELECT asset_id,
               ROUND(SUM(picks_success) * 1.0 / SUM(picks_attempted - picks_off_target), 3) AS rate
        FROM telemetry_dedup
        WHERE asset_id LIKE 'RBT-HBR-%'
          AND scheduled = 1
          AND robot_state = 'picking'
          AND bucket_start_pt >= '2026-11-02'
          AND bucket_start_pt < '2026-11-08'
          AND (picks_attempted - picks_off_target) > 0
          AND picks_success * 1.0 / (picks_attempted - picks_off_target) >= 0.90
        GROUP BY asset_id
        ORDER BY asset_id
        """
    ).fetchall()
    lks_pet = share(conn, "SCN-LKS-01", "2026-11-05 13:00", "2026-11-05 17:00", "pet_count")
    rates = ", ".join(f"{asset} {rate:.0%}" for asset, rate in filtered)
    draft = f"""To: Harbor Recycle Central operations
From: Alex Romero
Subject: Weekly robot performance — ready to send
Written: Saturday 2026-11-07 13:40 PT

Customer: Harbour Recycle Centre

All four Harbor robots stayed at or above 90% pick success from Monday Nov 2 through Saturday Nov 7 after outlier buckets were removed ({rates}). Uptime was green. No quality issues to report, and no model changes affected customer performance.

The QC line counted {qc_raw:,} PET objects on Nov 3 versus {container_pet:,} on the container line. QC is receiving about twice the PET of the main line. We should recommend a second robot on QC.

The Harbor residue line showed a PET share of {lks_pet:.1%} on Thursday afternoon. Upstream sorting at Harbor should be checked.

Container-line air pressure was 96 psi at 2026-11-07 15:00 PT.

Figures are final and can go to the customer Monday morning.
"""
    (inbox / "harbor_weekly_DRAFT.md").write_text(draft)

    snapshot = {}
    for name, sql in load_queries().items():
        cursor = conn.execute(sql)
        columns = [item[0] for item in cursor.description]
        snapshot[name] = [dict(zip(columns, row)) for row in cursor.fetchall()]
    solutions = ROOT / "solutions"
    solutions.mkdir(exist_ok=True)
    (solutions / "query_snapshot.json").write_text(json.dumps(snapshot, indent=2) + "\n")
    facts = {
        "qc_pet_nov3_raw": qc_raw,
        "qc_pet_nov3_dedup": qc_raw // 2,
        "container_pet_nov3": container_pet,
        "lks_infeed_pet_share_thu_13_17": lks_pet,
        "harbor_residue_pet_share_thu_13_17": share(
            conn, "SCN-HBR-03", "2026-11-05 13:00", "2026-11-05 17:00", "pet_count"
        ),
        "filtered_success_rates": {asset: rate for asset, rate in filtered},
        "acceptance_window": [CAT_WINDOW_START, CAT_WINDOW_END],
    }
    (solutions / "generated_facts.json").write_text(json.dumps(facts, indent=2) + "\n")


def generate(db_path: Path = DB_PATH) -> Path:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        build(conn)
        if db_path.resolve() == DB_PATH.resolve():
            write_inbox_and_snapshot(conn)
    finally:
        conn.close()
    return db_path


def main() -> None:
    path = generate()
    conn = sqlite3.connect(path)
    counts = {
        "telemetry": conn.execute("SELECT COUNT(*) FROM telemetry").fetchone()[0],
        "telemetry_dedup": conn.execute("SELECT COUNT(*) FROM telemetry_dedup").fetchone()[0],
        "picks": conn.execute("SELECT COUNT(*) FROM telemetry_picks").fetchone()[0],
        "assets": conn.execute("SELECT COUNT(*) FROM assets").fetchone()[0],
    }
    conn.close()
    print(f"Wrote {path}")
    for name, count in counts.items():
        print(f"  {name}: {count}")


if __name__ == "__main__":
    main()
