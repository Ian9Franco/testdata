"""Load the named queries in the daily pack."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DAILY_PACK = Path(__file__).resolve().parent / "sql" / "daily_pack.sql"
SPLIT = re.compile(r"(?m)^-- \[query: ([a-z0-9_]+)\]\s*$")

# Order used by the Monday morning briefing.
BRIEFING = [
    "open_tickets",
    "recent_shift_logs",
    "recent_events",
    "estop_or_fault_islands",
    "off_target_islands",
    "low_target_success_islands",
    "low_commodity_success_islands",
    "low_air_islands",
    "camera_issues",
    "commodity_shifts",
    "robots_at_capacity",
    "invalid_pick_rows",
    "duplicate_buckets",
    "timezone_mismatches",
    "model_versions",
    "commissioning_scorecard",
    "scanner_audit_deltas",
    "planned_maintenance",
    "benign_flow",
]


def load_queries(path: Path | None = None) -> dict[str, str]:
    text = (path or DAILY_PACK).read_text()
    parts = SPLIT.split(text)
    if len(parts) < 3:
        raise RuntimeError(f"No named queries in {path or DAILY_PACK}")
    queries: dict[str, str] = {}
    iterator = iter(parts[1:])
    for name, body in zip(iterator, iterator):
        queries[name] = body.strip().rstrip(";")
    return queries
