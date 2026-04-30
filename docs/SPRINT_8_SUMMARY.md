# Sprint 8 Summary — Workflow & Alerts

**Dates:** 2026-04-30  
**Points delivered:** 11 pts (US-031: 2, US-032: 3, US-033: 4, US-034: 2)  
**Tests:** 783 passing — 0 regressions  
**Tag:** `v2-sprint8`

---

## What Was Built

### US-031 — Patient List Search + Filter + Sort (2 pts)

Service layer (`src/services/patients.py`):
- `list_patients(conn, search, sort_by, sort_dir, phase_filter)` — SQL query with dynamic WHERE clauses for search (LIKE on patient_id + name), phase filter (AC/T/Completed via subqueries on cycle counts), sort direction, soft-delete exclusion.

UI (`src/views/patient_list.py`):
- Search box with 150ms debounce — substring match on patient_id and name, case-insensitive
- Phase filter dropdown: All / AC / T / Completed
- Sortable column headings (name, patient_id, status, risk)
- No-match state: "No patients match" with "Clear filters" link
- Status column (3rd column) showing cycle status dot + text with tooltip

Tests: 18 tests covering search, sort, filter combinations and empty-result state.

---

### US-032 — Next-Cycle-Due / Overdue Status (3 pts)

Clinical rules layer (`src/clinical/scheduling.py`):
- `expected_cycle_date(last_cycle_date, dose_density, config)` — adds cadence days (q3w=21d, q2w=14d) from config
- `cycle_status(last_cycle_date, dose_density, today, config)` — returns `(status_code, day_delta)` where status is `on_schedule`, `due_soon`, `overdue`, or `no_cycles`

Service (`src/services/cycles.py`):
- `last_completed_cycle_date(conn, patient_id)` — queries most recent completed cycle's actual_date

View (`src/views/components/cycle_status_indicator.py`):
- `get_status_for_patient(conn, patient_db_id, today)` — returns `(code, text, tooltip)`
- `status_sort_key(code)` and `status_color(code)` helpers for patient list integration
- Tooltip format: "Last cycle YYYY-MM-DD · expected YYYY-MM-DD · N days overdue/away"

Config:
```yaml
scheduling:
  cadence_days:
    standard_q3w: 21
    dose_dense_q2w: 14
  due_within_days: 7
```

Tests: 27 tests (12 clinical scheduling + 15 status indicator integration).

---

### US-033 — Pre-Cycle Safety Checklist (4 pts)

Clinical rules layer (`src/clinical/precycle.py`):
- Dataclasses: `RuleResult`, `ChecklistResult`, `ChecklistInputs`
- 9 independent rule functions, each returning `RuleResult`:

| # | Rule ID | Phase | Default Mode |
|---|---------|-------|-------------|
| 1 | `anc_below_threshold` | both | soft_block |
| 2 | `platelets_below_threshold` | both | soft_block |
| 3 | `labs_stale` | both | advisory |
| 4 | `active_infection` | both | soft_block |
| 5 | `cumulative_red` | AC | soft_block |
| 6 | `cumulative_hard_stop` | AC | hard_block |
| 7 | `lvef_abnormal` | AC | soft_block |
| 8 | `neuropathy_t_above_max` | T | soft_block |
| 9 | `symptoms_grade_3_or_higher` | both | advisory |

- `run_checklist(inputs, config)` — aggregator calling all rules, computing `worst_status` and `can_save_without_override`
- Phase gating: rules 5/6/7 skip in T phase, rule 8 skips in AC phase
- `_clamp_status` ensures rule severity never exceeds configured blocking mode
- ANC thresholds: AC/T = 1500/uL, dose-dense from cycle 2 = 1000/uL

Service (`src/services/checklist.py`):
- `gather_inputs(conn, patient_db_id, cycle_number, planned_admin_date, nurse_attests)` — assembles ChecklistInputs from labs, cumulative dose, LVEF, neuropathy, symptoms
- `evaluate(conn, ...)` — one-call convenience wrapper

Dialog (`src/views/dialogs/precycle_checklist_dialog.py`):
- Infection attestation checkbox (default unchecked)
- Rule list with status icons: ✓ pass, ℹ advisory, ⚠ soft_block, ⛔ hard_block
- Soft block: requires 20-char override reason, writes `checklist_override` audit row
- Hard block: Proceed button disabled
- Wired into `timeline.py._on_cycle_click()` — runs before CycleCompletionDialog

Tests: 51 tests (32 clinical precycle + 6 checklist service + 13 dialog integration).

---

### US-034 — Low-ANC Alert Banner (2 pts)

View (`src/views/components/low_anc_banner.py`):
- `LowAncBanner(tk.Frame)` with `load_patient()` and `refresh()` API
- Red banner (#B71C1C) for ANC < 500/uL, orange (#E65100) for 500-999/uL, hidden >= 1000/uL
- Dismiss button stores dismissal in session-scoped dict keyed by patient_id
- `until_next_lab` scope: dismissal cleared when lab.id changes
- Mounted above patient header in dashboard

Config:
```yaml
alerts:
  low_anc_banner:
    red_below_per_uL: 500
    orange_below_per_uL: 1000
    dismiss_scope: session
```

Tests: 14 tests covering threshold boundaries, dismiss/restore, and DB integration.

---

## Architecture Decisions

1. **No new schema migrations.** All data sourced from existing Sprint 5/6/7 tables. Checklist overrides recorded via audit log only — no `cycle.checklist_overrides_json` column.

2. **Checklist before completion.** The checklist dialog gates the cycle-completion dialog via a callback chain in `timeline.py._on_cycle_click()`. The existing Sprint 6 override flow (cumulative dose, LVEF) runs after the checklist clears — not replaced, not duplicated.

3. **Two override prompts on same save.** When a cycle triggers both a checklist soft-block and a Sprint 6 cumulative-red block, the user sees two separate override dialogs. Two audit rows are written (`checklist_override` + `override_red`). Collapsing into one dialog is deferred to V2.1.

4. **Rules delegate, not reimplement.** Cumulative dose and LVEF rules call Sprint 6 services (`cumulative_dose`, `lvef_status`). Neuropathy rule calls Sprint 7 `effective_grade()`. No logic duplication.

5. **Phase gating is positional.** Cycles 1-4 = AC, 5-8 = T. This matches Sprint 7's convention.

---

## Config Additions

Sprint 8 added four new config sections to `config/institution.defaults.yaml`:
- `scheduling:` — cadence days, due-within window
- `labs:` — freshness hours
- `precycle:` — ANC/platelet thresholds, blocking modes for all 9 rules, neuropathy max grade, symptom advisory grade
- `alerts:` — low-ANC banner thresholds and dismiss scope

All thresholds configurable via YAML. Zero magic numbers in code.

---

## Test Summary

| Test File | Tests | Scope |
|-----------|-------|-------|
| `test_clinical_scheduling.py` | 12 | Scheduling pure functions |
| `test_clinical_precycle.py` | 32 | All 9 rules + aggregator |
| `test_checklist_service.py` | 6 | gather_inputs + evaluate |
| `test_patient_list_search.py` | 18 | Search/sort/filter |
| `test_cycle_status_indicator.py` | 15 | Status states, sort, color |
| `test_precycle_checklist_dialog.py` | 13 | 4 paths + phase gating + LVEF |
| `test_low_anc_banner.py` | 14 | Thresholds, dismiss, DB |
| `test_sprint8_e2e.py` | 25 | Cross-story integration |
| **Total new** | **135** | |

Full suite: 783 tests, 0 regressions.

---

## Carry-Over

None. All four stories complete.

---

## What's Next

Sprint 9: Reporting — PDF generation summarizing patient safety state, leveraging the `RuleResult` shape finalized in this sprint.
