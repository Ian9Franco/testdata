# Take-home — Monday 2026-11-09, 08:30 PT

You are the operations analyst starting the Monday shift. The Saturday log says the fleet was quiet and that a Harbor weekly is ready to send. Check that. Two customers are already waiting.

Time box: 150 minutes. Write in English. The queries and the playbooks are the process; use them.

Do not open `solutions/`, and do not read `tests/`, until you have finished.

## Setup

```bash
python3 -m ops_lab.console briefing
python3 -m ops_lab.console query low_air_islands
```

Database: `data/glacier_ops.sqlite`. Queries: `ops_lab/sql/daily_pack.sql`. Process: `playbooks/`. Inbox: `inbox/`.

Copy `exercises/escalations_template.csv` to `my_work/escalations.csv`.

Allowed `route_to`: Field Service, Perception, Deployment Engineering, Customer Success, Data Engineering.

Allowed `priority`: P1, P2, P3.

One row per asset and team. A note column is for you; the grader ignores it.

## Deliverables

### A — Triage (45 min) — 40 points

`my_work/escalations.csv`

Page what the playbook says to page. Do not page what it says to leave. Merge adjacent hours into one row.

### B — Live call (30 min) — 15 points

`inbox/TCK-1042.md` is still open.

- `my_work/TCK-1042_call_notes.md` — internal note
- `my_work/TCK-1042_customer_email.md` — short note Mike can forward to his manager

Use `playbooks/call_scripts.md`. The feed ends at 08:15 PT. Do not invent a reset that you cannot see.

### C — Acceptance (40 min) — 20 points

`inbox/TCK-1044.md` asks for a yes or no by 11:00 PT.

- `my_work/riverbend_scorecard.md` — one row per acceptance metric, actual, threshold, pass/fail, the query you used
- `my_work/riverbend_email.md` — the reply to Renee Holt

Acceptance is per asset. The window is Wed Nov 4 through Sat Nov 7. Nov 2–3 are burn-in.

### D — Redline (25 min) — 15 points

`inbox/harbor_weekly_DRAFT.md` is marked ready to send.

`my_work/harbor_draft_redline.md` — each error, the correct figure, and where it came from. End with `SEND` or `HOLD`.

### E — Handoff (10 min) — 10 points

`my_work/shift_handoff.md` for the next analyst. Use the template. Include what is still unknown.

## Stretch

If you finish, rewrite `low_air_islands` from memory in `my_work/stretch.sql` without the daily pack open. It is not graded.

## Afterward

```bash
python3 -m ops_lab.grade my_work/escalations.csv
```

Then read `solutions/RUBRIC.md` and score B–E yourself. Rewrite the weakest piece once, from a blank file, before you look at the model text a second time.
