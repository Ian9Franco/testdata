"""The answer key scores a perfect CSV at full marks and catches a bad page."""

from __future__ import annotations

import csv
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from ops_lab.grade import KEY_PATH, grade


class GradeTest(unittest.TestCase):
    def test_required_rows_score_full_marks(self):
        key = json.loads(KEY_PATH.read_text())
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "escalations.csv"
            with path.open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["asset_id", "route_to", "priority", "note"])
                writer.writeheader()
                for spec in key["required"]:
                    writer.writerow(
                        {
                            "asset_id": spec["asset_id"],
                            "route_to": spec["route_to"],
                            "priority": spec["priority"],
                            "note": spec["id"],
                        }
                    )
            with contextlib.redirect_stdout(io.StringIO()):
                result = grade(path)
            self.assertEqual(result, 0)

    def test_paging_planned_maintenance_is_penalized(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "escalations.csv"
            path.write_text(
                "asset_id,route_to,priority,note\n"
                "RBT-PAC-01,Field Service,P1,the wednesday gap\n"
            )
            with contextlib.redirect_stdout(io.StringIO()):
                result = grade(path)
            self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
