"""Locks the planted fleet story to the daily-pack queries."""

from __future__ import annotations

import sqlite3
import unittest

from ops_lab.generate import build
from ops_lab.queries import BRIEFING, load_queries


def rows(conn, name, queries):
    return conn.execute(queries[name]).fetchall()


class DailyPackTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn = sqlite3.connect(":memory:")
        cls.conn.row_factory = sqlite3.Row
        build(cls.conn)
        cls.queries = load_queries()

    def test_every_briefing_query_runs(self):
        for name in BRIEFING:
            rows(self.conn, name, self.queries)

    def test_duplicates_are_only_the_qc_scanner_on_nov_3(self):
        found = rows(self.conn, "duplicate_buckets", self.queries)
        self.assertEqual([dict(row)["asset_id"] for row in found], ["SCN-HBR-04"])
        self.assertEqual(found[0]["duplicated_buckets"], 96)
        raw = self.conn.execute("SELECT COUNT(*) FROM telemetry").fetchone()[0]
        dedup = self.conn.execute("SELECT COUNT(*) FROM telemetry_dedup").fetchone()[0]
        self.assertEqual(raw - dedup, 96)

    def test_timezone_label_is_only_the_downstream_lakeshore_scanner(self):
        found = rows(self.conn, "timezone_mismatches", self.queries)
        self.assertEqual([row["asset_id"] for row in found], ["SCN-LKS-02"])

    def test_air_and_low_success_are_the_same_saturday_window(self):
        air = rows(self.conn, "low_air_islands", self.queries)
        success = rows(self.conn, "low_target_success_islands", self.queries)
        self.assertEqual([(row["asset_id"], row["start_pt"], row["end_pt_exclusive"]) for row in air], [
            ("RBT-HBR-02", "2026-11-07 05:00", "2026-11-07 11:00")
        ])
        self.assertEqual(
            [(row["asset_id"], row["start_pt"], row["end_pt_exclusive"]) for row in success],
            [(row["asset_id"], row["start_pt"], row["end_pt_exclusive"]) for row in air],
        )
        self.assertLess(air[0]["avg_air_psi"], 70)
        self.assertLess(air[0]["target_success_rate"], 0.70)
        sibling = self.conn.execute(
            """
            SELECT picks_success * 1.0 / (picks_attempted - picks_off_target) AS rate,
                   air_psi,
                   objects_detected
            FROM telemetry_dedup
            WHERE asset_id = 'RBT-HBR-01'
              AND bucket_start_pt = '2026-11-07 07:00'
            """
        ).fetchone()
        broken = self.conn.execute(
            """
            SELECT picks_success * 1.0 / (picks_attempted - picks_off_target) AS rate,
                   air_psi,
                   objects_detected
            FROM telemetry_dedup
            WHERE asset_id = 'RBT-HBR-02'
              AND bucket_start_pt = '2026-11-07 07:00'
            """
        ).fetchone()
        self.assertGreater(sibling["rate"], 0.90)
        self.assertEqual(sibling["air_psi"], 96)
        self.assertLess(broken["rate"], 0.70)
        self.assertEqual(broken["air_psi"], 58)
        self.assertEqual(sibling["objects_detected"], broken["objects_detected"])

    def test_blended_rate_hides_riverbend_aluminum(self):
        blended = self.conn.execute(
            """
            SELECT SUM(picks_success) * 1.0 / SUM(picks_attempted - picks_off_target)
            FROM telemetry_dedup
            WHERE asset_id = 'RBT-RVB-01'
              AND scheduled = 1
              AND robot_state = 'picking'
              AND bucket_start_pt >= '2026-11-04'
              AND bucket_start_pt < '2026-11-08'
            """
        ).fetchone()[0]
        self.assertGreater(blended, 0.85)
        self.assertLess(blended, 0.90)
        commodities = {
            (row["asset_id"], row["commodity"])
            for row in rows(self.conn, "low_commodity_success_islands", self.queries)
        }
        # Air loss drops every class together. Aluminum-only is the model miss.
        self.assertEqual(
            commodities,
            {
                ("RBT-RVB-01", "AL"),
                ("RBT-HBR-02", "PET"),
                ("RBT-HBR-02", "HDPE"),
                ("RBT-HBR-02", "AL"),
            },
        )

    def test_fiber_regression_hits_protected_occ(self):
        found = rows(self.conn, "off_target_islands", self.queries)
        self.assertTrue(found)
        self.assertTrue(all(row["asset_id"] == "RBT-HBR-04" for row in found))
        self.assertTrue(all(row["top_off_target"] == "OCC" for row in found))
        self.assertTrue(all(row["hits_protected_product"] == "YES" for row in found))
        self.assertGreaterEqual(min(row["off_target_rate"] for row in found), 0.25)
        versions = rows(self.conn, "model_versions", self.queries)
        self.assertEqual(
            [(row["model_version"], row["first_bucket_pt_label"]) for row in versions],
            [("v2.13.4", "2026-11-02 00:00"), ("v2.14.0", "2026-11-06 02:00")],
        )

    def test_commodity_shift_is_the_lakeshore_residue_event(self):
        found = rows(self.conn, "commodity_shifts", self.queries)
        pairs = {(row["asset_id"], row["commodity"]) for row in found}
        self.assertEqual(
            pairs,
            {("SCN-LKS-01", "PET"), ("SCN-LKS-01", "AL"), ("SCN-LKS-02", "PET")},
        )
        self.assertTrue(all(row["pt_date"] == "2026-11-05" for row in found))
        capacity = rows(self.conn, "robots_at_capacity", self.queries)
        self.assertEqual(
            [(row["asset_id"], row["start_pt"], row["end_pt_exclusive"]) for row in capacity],
            [("RBT-LKS-01", "2026-11-05 13:00", "2026-11-05 17:00")],
        )
        self.assertGreater(capacity[0]["target_success_rate"], 0.90)

    def test_camera_split_between_dirty_lens_and_outage(self):
        found = {
            (row["asset_id"], row["camera_health"]): row
            for row in rows(self.conn, "camera_issues", self.queries)
        }
        self.assertEqual(set(found), {("SCN-CDR-02", "dirty_lens"), ("SCN-RVB-03", "offline")})
        self.assertEqual(found[("SCN-CDR-02", "dirty_lens")]["first_scheduled_pt"], "2026-11-06 08:00")
        self.assertEqual(found[("SCN-CDR-02", "dirty_lens")]["last_scheduled_pt"], "2026-11-09 08:15")
        self.assertGreater(found[("SCN-CDR-02", "dirty_lens")]["unknown_share"], 0.30)
        self.assertEqual(found[("SCN-RVB-03", "offline")]["first_scheduled_pt"], "2026-11-07 09:00")
        self.assertEqual(found[("SCN-RVB-03", "offline")]["scheduled_buckets"], 20)

    def test_invalid_picks_are_quarantined(self):
        found = rows(self.conn, "invalid_pick_rows", self.queries)
        self.assertEqual(len(found), 1)
        row = found[0]
        self.assertEqual(row["asset_id"], "RBT-PAC-03")
        self.assertEqual(row["start_pt"], "2026-11-06 14:00")
        self.assertEqual(row["end_pt_exclusive"], "2026-11-06 17:00")
        self.assertGreater(row["max_success"], row["max_attempted"])

    def test_faults_are_estop_and_known_blip_only(self):
        found = {(row["asset_id"], row["fault_code"], row["start_pt"], row["end_pt_exclusive"]) for row in rows(self.conn, "estop_or_fault_islands", self.queries)}
        self.assertEqual(
            found,
            {
                ("RBT-CDR-01", "ESTOP", "2026-11-09 06:45", "2026-11-09 08:30"),
                ("RBT-RVB-01", "OFFLINE", "2026-11-06 08:00", "2026-11-06 09:00"),
            },
        )

    def test_scorecard_fails_only_the_known_acceptance_gaps(self):
        found = rows(self.conn, "commissioning_scorecard", self.queries)
        failed = {(row["asset_id"], row["metric"]) for row in found if row["result"] == "FAIL"}
        self.assertEqual(
            failed,
            {
                ("RBT-RVB-01", "picks_per_min"),
                ("RBT-RVB-01", "success_AL"),
                ("SCN-RVB-03", "max_offline_min"),
            },
        )
        passed = {(row["asset_id"], row["metric"]) for row in found if row["result"] == "PASS"}
        self.assertIn(("RBT-RVB-01", "uptime"), passed)
        self.assertIn(("RBT-RVB-01", "success_PET"), passed)
        self.assertIn(("RBT-RVB-01", "success_HDPE"), passed)
        self.assertIn(("RBT-RVB-02", "uptime"), passed)
        self.assertIn(("RBT-RVB-02", "picks_per_min"), passed)
        self.assertIn(("RBT-RVB-02", "success_AL"), passed)

    def test_audits_agree_with_the_infeed_scanners(self):
        found = rows(self.conn, "scanner_audit_deltas", self.queries)
        self.assertTrue(found)
        self.assertTrue(all(row["within_5_points"] == "WITHIN" for row in found))
        lakeshore_pet = next(
            row for row in found if row["asset_id"] == "SCN-LKS-01" and row["commodity"] == "PET"
        )
        self.assertGreater(abs(lakeshore_pet["delta"]), 0.005)
        self.assertLess(abs(lakeshore_pet["delta"]), 0.05)

    def test_benign_flow_stays_under_the_thresholds(self):
        found = rows(self.conn, "benign_flow", self.queries)
        self.assertEqual(
            [(row["line_id"], row["belt_state"], row["minutes"], row["escalation"]) for row in found],
            [
                ("LN-LKS-CON", "stopped", 30, "BELOW THRESHOLD"),
                ("LN-PAC-CON", "empty", 45, "BELOW THRESHOLD"),
            ],
        )

    def test_open_tickets_exclude_the_closed_one(self):
        found = [row["ticket_id"] for row in rows(self.conn, "open_tickets", self.queries)]
        self.assertEqual(found, ["TCK-1042", "TCK-1044"])


if __name__ == "__main__":
    unittest.main()
