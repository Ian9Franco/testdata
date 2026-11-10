"""Score exercises/escalations.csv against the practice answer key."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEY_PATH = ROOT / "solutions" / "answer_key.json"

ALLOWED_ROUTES = {
    "field service": "Field Service",
    "perception": "Perception",
    "data engineering": "Data Engineering",
    "deployment engineering": "Deployment Engineering",
    "customer success": "Customer Success",
}


def canon_route(value: str) -> str | None:
    return ALLOWED_ROUTES.get(value.strip().lower())


def canon_priority(value: str) -> str | None:
    text = value.strip().upper()
    return text if text in {"P1", "P2", "P3"} else None


def load_rows(path: Path) -> list[dict]:
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise SystemExit("El CSV no tiene encabezado.")
        fields = {name.strip().lower(): name for name in reader.fieldnames}
        for required in ("asset_id", "route_to", "priority"):
            if required not in fields:
                raise SystemExit(
                    "El CSV necesita las columnas asset_id, route_to, priority. "
                    "Copiá exercises/escalations_template.csv."
                )
        rows = []
        for raw in reader:
            asset = (raw[fields["asset_id"]] or "").strip()
            if not asset:
                continue
            route = canon_route(raw[fields["route_to"]] or "")
            priority = canon_priority(raw[fields["priority"]] or "")
            rows.append(
                {
                    "asset_id": asset,
                    "route_to": route,
                    "route_raw": (raw[fields["route_to"]] or "").strip(),
                    "priority": priority,
                    "priority_raw": (raw[fields["priority"]] or "").strip(),
                }
            )
        return rows


def matches(row: dict, spec: dict) -> bool:
    return (
        row["asset_id"] == spec["asset_id"]
        and row["route_to"] == spec["route_to"]
        and row["priority"] == spec["priority"]
    )


def grade(path: Path) -> int:
    key = json.loads(KEY_PATH.read_text())
    rows = load_rows(path)
    print(f"Archivo: {path}")
    print(f"Filas leídas: {len(rows)}\n")
    hits = []
    for spec in key["required"]:
        if any(matches(row, spec) for row in rows):
            hits.append(spec)
            print(f"  OK   {spec['id']:16} {spec['asset_id']:12} {spec['route_to']} {spec['priority']}")
        else:
            print(f"  MISS {spec['id']:16} {spec['asset_id']:12} falta {spec['route_to']} {spec['priority']}")

    penalties = []
    for spec in key["penalties"]:
        asset_rows = [row for row in rows if row["asset_id"] == spec["asset_id"]]
        triggered = False
        for row in asset_rows:
            if "unless_route" in spec and row["route_to"] == spec["unless_route"]:
                continue
            if "bad_routes" in spec:
                if row["route_to"] in spec["bad_routes"]:
                    triggered = True
            else:
                triggered = True
        if triggered:
            penalties.append(spec)
            print(f"  PENALTY {spec['asset_id']:12} {spec['reason']}")

    unknown = [row for row in rows if row["route_to"] is None or row["priority"] is None]
    for row in unknown:
        print(
            f"  WARN fila inválida {row['asset_id']}: "
            f"route '{row['route_raw']}' priority '{row['priority_raw']}'. "
            "Los equipos y P1/P2/P3 tienen que coincidir con el playbook."
        )

    triage = round(40 * len(hits) / len(key["required"]) - 4 * len(penalties))
    triage = max(0, triage)
    print(
        f"\nTriage: {len(hits)}/{len(key['required'])} hallazgos, "
        f"{len(penalties)} penalizaciones → {triage}/40 puntos."
    )
    print("El CSV es solo la parte de triage. El resto se corrige con solutions/RUBRIC.md.")
    return 0 if len(hits) == len(key["required"]) and not penalties else 1


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "my_work" / "escalations.csv"
    if not path.exists():
        raise SystemExit(
            f"No está {path}. Copiá exercises/escalations_template.csv a my_work/escalations.csv "
            "después de correr el daily pack."
        )
    raise SystemExit(grade(path))


if __name__ == "__main__":
    main()
