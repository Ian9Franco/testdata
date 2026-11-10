"""Run the Monday morning query pack."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

from ops_lab.catalog import SCENARIO_AS_OF
from ops_lab.generate import DB_PATH
from ops_lab.queries import BRIEFING, load_queries


def connect(path: Path) -> sqlite3.Connection:
    if not path.exists():
        raise SystemExit(f"Missing {path}. Run: python3 -m ops_lab.generate")
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def render(rows: list[sqlite3.Row], limit: int = 40) -> str:
    if not rows:
        return "(no rows)\n"
    columns = rows[0].keys()
    shown = rows[:limit]
    widths = []
    for column in columns:
        width = len(column)
        for row in shown:
            text = "" if row[column] is None else str(row[column]).replace("\n", " ")
            width = max(width, min(len(text), 88))
        widths.append(width)

    def format_row(row) -> str:
        cells = []
        for column, width in zip(columns, widths):
            text = "" if row[column] is None else str(row[column]).replace("\n", " ")
            if len(text) > width:
                text = text[: width - 1] + "…"
            cells.append(text.ljust(width))
        return "  ".join(cells)

    header = "  ".join(name.ljust(width) for name, width in zip(columns, widths))
    lines = [header, "  ".join("-" * width for width in widths)]
    lines.extend(format_row(row) for row in shown)
    if len(rows) > limit:
        lines.append(f"... {len(rows) - limit} more rows")
    lines.append(f"({len(rows)} rows)")
    return "\n".join(lines) + "\n"


def run_query(conn: sqlite3.Connection, name: str, sql: str) -> str:
    description = ""
    for line in sql.splitlines():
        stripped = line.strip()
        if stripped.startswith("-- ") and not stripped.startswith("-- [query:"):
            description = stripped[3:]
            break
    cursor = conn.execute(sql)
    rows = cursor.fetchall()
    title = f"## {name}"
    if description:
        title += f"\n{description}"
    return title + "\n" + render(rows)


def briefing(conn: sqlite3.Connection, queries: dict[str, str]) -> str:
    parts = [
        f"# Northline daily pack\nScenario clock: {SCENARIO_AS_OF}\n",
        "Run the playbook before you route anything. A green uptime chart is not a result.\n",
    ]
    for name in BRIEFING:
        parts.append(run_query(conn, name, queries[name]))
    return "\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description="Northline fleet daily pack")
    parser.add_argument("command", choices=["briefing", "query", "list"])
    parser.add_argument("name", nargs="?")
    parser.add_argument("--db", type=Path, default=DB_PATH)
    args = parser.parse_args()
    queries = load_queries()
    if args.command == "list":
        print("\n".join(queries))
        return
    conn = connect(args.db)
    try:
        if args.command == "briefing":
            print(briefing(conn, queries))
        else:
            if args.name not in queries:
                raise SystemExit(f"Unknown query {args.name}. Use: python3 -m ops_lab.console list")
            print(run_query(conn, args.name, queries[args.name]))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
