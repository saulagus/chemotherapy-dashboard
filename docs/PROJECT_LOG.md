# Project Log — AC-T Chemotherapy Dashboard

---

## 2026-05-18 — Sprint 10 V2 Close-out Planning

### Completed
- Reconciled `docs/V2_PLAN_SUMMARY.txt` against completed Sprint 5-9 work.
- Identified `[N12] Hospitalization / ER visit capture` as the remaining V2 scope item missing from the old Sprint 10 plan.
- Expanded `docs/SPRINT_10_PLAN.md` into the canonical V2 close-out plan.
- Added `US-043 Hospitalization / ER visit capture` to Sprint 10.
- Corrected the backup config plan to preserve the existing `backup.reminder_interval_days` key.
- Added the Sprint 10 decision to use pinned coverage tooling so the `>=85%` clinical/services coverage target is measurable.

### Decisions
- Sprint 10 now contains one final clinical surface: hospitalization / ER visit capture.
- US-043 is intentionally narrow: capture, view, audit, and test events; no hospitalization reports or decision-support rules in V2.
- `docs/SPRINT_10_PLAN.md` remains the canonical Sprint 10 planning artifact.

### Next
- Implement US-043 first, then backup/restore, shortcuts/settings, performance/coverage, and release docs in the order defined by `docs/SPRINT_10_PLAN.md`.

---

## 2026-05-17 — Sprint 9 Restart + Close-out

### Completed
- Resumed from `ecd97a5` (`Added dose modification history view`) and audited Sprint 9 against `docs/SPRINT_9_PLAN.md`.
- Confirmed Sprint 8 was closed and tagged; Sprint 10 remains blocked until Sprint 9 close-out.
- Finished Sprint 9 verification gaps:
  - `PatientReportData` now carries lab history so oncologist PDF ANC chart embeds real report data.
  - CSV lab export handles config-driven soft-delete behavior when a `deleted_at` column exists.
  - Print-friendly dashboard PDF generation and `print_dashboard` audit logging moved into `services/exports.py`.
  - Added focused tests for report data, CSV export, PDF templates, export audit rows, and print-dashboard export.
- Added `docs/THIRD_PARTY_LICENSES.md` with the ReportLab 4.2.5 license.
- Wrote `docs/SPRINT_9_SUMMARY.md`.

### Test Count
834 tests — 0 regressions

### Verification
- Import check: Sprint 9 report/export imports OK
- Logic check: report lab history flows into oncologist chart helper
- Focused Sprint 9 tests: 43 passed
- Broad non-GUI regression suite: 580 passed
- Full suite with GUI access: 834 passed, 1 ReportLab deprecation warning
- Warm report timing: oncologist 67.9 ms, print 0.7 ms, CSV 0.2 ms

### Sprint 9 Final Status
All four user stories delivered:
- US-035 PDF patient summary export (4 pts) — DONE
- US-036 Dose modification history view (2 pts) — DONE
- US-037 CSV lab export (1 pt) — DONE
- US-038 Print-friendly dashboard view (2 pts) — DONE

### Decisions
- ReportLab PDFs use deterministic `invariant=1` rendering for byte-stable tests.
- `reports/data.py` is the single data assembler for all report templates.
- Dashboard print uses the export service for PDF bytes and audit logging; dashboard remains responsible for OS print/open fallback.
- Current labs schema hard-deletes labs; CSV exporter also supports a future `deleted_at` column without requiring a Sprint 9 migration.

---

## 2026-04-30 — Sprint 8 Day 41 (Close-out)

### Completed
- Day 32: US-031 — patient list search, filter, sort (18 tests)
- Day 33: US-034 — low-ANC alert banner with red/orange thresholds and dismissible session state (14 tests)
- Day 34–35: US-032 — cycle scheduling rules, last-cycle helper, status column in patient list (27 tests)
- Day 36–39: US-033 — 9 pre-cycle checklist rules, aggregator, checklist service, dialog wired into timeline (51 tests)
- Day 40: Sprint 8 e2e integration tests — 9 cross-story scenarios (25 tests)
- Day 41: Summary doc, project log close-out, tag v2-sprint8

### Test Count
783 tests — 0 regressions

### Sprint 8 Final Status
All four user stories delivered:
- US-031 Patient list search + filter + sort (2 pts) — DONE
- US-032 Next-cycle-due / overdue status (3 pts) — DONE
- US-033 Pre-cycle safety checklist (4 pts) — DONE
- US-034 Low-ANC alert banner (2 pts) — DONE

### Decisions
- Checklist dialog runs before cycle-completion dialog; existing Sprint 6 override flow unchanged
- No new schema migrations — all data sourced from existing tables
- Audit log is the sole record of checklist overrides (no `cycle.checklist_overrides_json` column)
- Two override prompts may fire on the same save (checklist + Sprint 6 cumulative/LVEF); two audit rows acceptable

---

## 2026-04-30 — Sprint 8 Day 31 (Planning + Scaffolding)

### Specialist YAML Review
- All defaults accepted (no specialist overrides on Day 31); shipping config defaults as-is per plan.
- Defaults committed: scheduling cadence (q3w=21d, q2w=14d), lab freshness (72h), pre-cycle ANC thresholds (AC/T=1500, dose-dense C2+=1000), platelets (100000), blocking modes for all 9 rules, low-ANC banner thresholds (red<500, orange<1000).

### Plan
- Added `scheduling:`, `labs:`, `precycle:`, `alerts:` blocks to `config/institution.defaults.yaml`
- Extended Pydantic schema with `SchedulingSection`, `LabsSection`, `PrecycleSection`, `AlertsSection`
- Created `src/clinical/scheduling.py` — `expected_cycle_date()`, `cycle_status()` pure functions
- Created `src/clinical/precycle.py` — 9 rule functions, `RuleResult`/`ChecklistResult`/`ChecklistInputs` dataclasses, `run_checklist()` aggregator
- Created `src/services/checklist.py` — `gather_inputs()`, `evaluate()` wiring
- Added `last_completed_cycle_date()` to `services/cycles.py`
- Created `src/views/components/low_anc_banner.py` — dismissible ANC alert banner
- Created `src/views/components/cycle_status_indicator.py` — status dot + tooltip helper
- Created `src/views/dialogs/precycle_checklist_dialog.py` — full checklist dialog
- Added `checklist_override` to audit ACTIONS set
- Created 6 test files; 62 new tests passing

### Test Count
698 tests — 0 regressions

---

## 2026-04-28 — Sprint 7 Day 30 (Close-out)

### Completed
- Day 28: Hooked `SymptomQuickEntryDialog` into cycle-completion save flow; wired symptoms section in `ToxicityPanel`; added `_SymptomHistoryWindow`
- Day 29: Wrote 23-test suite for `ToxicityPanel` covering all four sections, history windows, add-symptoms guard, and empty-state rendering
- Day 30: `docs/SPRINT_7_SUMMARY.md` written; `PROJECT_LOG.md` closed; tagged `v2-sprint7`

### Test Count
636 tests — 0 regressions

### Sprint 7 Final Status
All four user stories delivered:
- US-027 Neuropathy (CTCAE v5): grade + action rules, service, dialog, panel section — DONE
- US-028 Infusion Reactions: rechallenge advisory, dialog, panel section — DONE
- US-029 G-CSF Administration: agent vocab, stimulated-window chart markers — DONE
- US-030 Symptom Quick-Entry: phase-adaptive set, batch insert, cycle-completion hook, panel section — DONE

---

## 2026-04-27 — Sprint 7 Day 21 (Planning + Scaffolding)

### Specialist YAML Review
- All defaults accepted (no specialist overrides on Day 21); shipping config defaults as-is per plan.
- Defaults committed: neuropathy grade→action, infusion rechallenge policy, CTCAE v5.0, symptom set, G-CSF vocab.

### Plan
- 11 pts across US-027 (neuropathy), US-028 (infusion reactions), US-029 (G-CSF), US-030 (symptom quick-entry)
- Day-by-day: 22–23 US-027, 24–25 US-028, 26 US-029, 27–28 US-030, 29 toxicity panel + e2e, 30 close-out

### Completed
- Added `toxicity:` block to `config/institution.defaults.yaml`
- Scaffolded `src/clinical/neuropathy.py`, `src/clinical/infusion_reactions.py`, `src/clinical/symptoms.py` (signatures only)
- Created empty migrations 0007–0010 (up/down stubs)
- Created empty test files for all 8 new modules
- Verified migration runner picks up all 4 new migrations

### Test Count
473 tests — 0 regressions

### Next
- Day 22: `0007_neuropathy_assessment.py` migration + `clinical/neuropathy.py` rules + `services/neuropathy.py`

---

## 2026-04-27 — Sprint 6 Day 20 (Close-out)

### Completed
- Wrote `docs/SPRINT_6_SUMMARY.md` — all 11 pts delivered, 473 tests, decisions, carry-over (none)
- Tagged `v2-sprint6`
- Sprint 7 preview documented (US-027–030)

### Test Count
473 tests — 0 regressions

### Next
- Sprint 7: Toxicity Tracking — US-027 Neuropathy, US-028 Infusion reactions, US-029 G-CSF log, US-030 Symptom quick-entry

---

## 2026-04-27 — Sprint 6 Day 19 (US-026 Finish — LVEF Blocking + E2E Tests)

### Completed
- Added `override_lvef` to audit ACTIONS set in `src/services/audit.py`
- Added LVEF soft-block to `CycleCompletionDialog` (`src/views/dialogs/cycle_completion_dialog.py`)
  - `_check_lvef_block()`: reads latest LVEF + baseline from DB, calls `lvef_status()`, applies `lvef_absolute` / `lvef_delta` blocking modes from config
  - `_lvef_block_dialog(reason, hard)`: single parameterised dialog — soft path requires non-empty reason; hard path requires ≥20 chars + attending override button
  - Block applied only for AC cycles (cycle_number ≤ 4), consistent with Sprint 8 pre-cycle checklist design
  - Edit path fix: `create_cycle()` return value now captured as `saved_cycle` so override audit rows have the correct entity_id
  - Multiple overrides (cumulative + LVEF) both written in a single loop after save
- Expanded `tests/test_cycle_blocking.py` — 9 new LVEF tests (24 total):
  - `override_lvef` in ACTIONS; write_audit accepts it
  - No-assessment path; ok/review paths → (None, None) without dialog
  - Absolute hold triggers dialog; delta hold triggers dialog; cancel → None
  - T-phase guard assertion
- Added Phase 9 cardiotoxicity e2e tests to `tests/test_e2e_integration.py` — 11 new tests:
  - Fresh patient → green; 4 cycles → green; prior exposure → yellow → red
  - override_red and override_lvef audit rows visible via get_audit_for_entity
  - Double-block (cumulative + LVEF) writes two audit rows
  - LVEF hold detected from absolute and from delta
  - CardiotoxicityPanel renders with both cycle and LVEF data

### Test Count
473 tests — 19 new tests, 0 regressions

### Decisions
- LVEF block is AC-only at the `_on_save()` guard level; `_check_lvef_block()` itself is phase-agnostic so it remains testable without coupling it to `cycle_number`
- Soft and hard LVEF block share one `_lvef_block_dialog(hard=True/False)` method — same UI pattern, different accent color and minimum character requirement
- `override_lvef` is a single action regardless of whether the hold was absolute or delta — the reason text entered by the user captures which

### Next
- Day 20: summary doc + tag (done in same session)

---

## 2026-04-26 — Sprint 6 Day 18 (US-026 — Risk Badges, Tooltip, Cycle Blocking)

### Completed

- Added cumulative dose risk badge to `PatientHeader` (`src/views/components/patient_header.py`)
  - `_badge_label` placed in a `name_row` Frame alongside the patient name label
  - `update_cumulative_badge(summary)` method sets text + color from `CumulativeSummary`
  - Badge text: `● Green`, `⚠ Yellow`, `⛔ Red`, `⛔ STOP`
  - Dashboard calls `update_cumulative_badge` on load and after every cycle save
- Added Dose Risk column to `PatientListView` (`src/views/patient_list.py`)
  - 7th Treeview column (90 px, centre-aligned, heading "Dose Risk")
  - Per-patient `cumulative_dose()` called on list load; results cached in `_patient_summaries`
  - Row tags `(patient_id, dose_tag, stripe)` — dose tag foreground takes priority over stripe background
  - Hover restores both dose_tag + stripe via `_restore_row_tags()`
  - Motion-based tooltip on Risk column: `"240.0 mg/m² dox-equiv · 60.0 mg/m² to advisory threshold"`
- Added `on_cycle_save` callback hook to `TimelineComponent` (`src/views/components/timeline.py`)
  - `_on_cycle_click` defines `_on_save()` that calls `self.refresh()` then `on_cycle_save()` if set
  - Passed to both `CycleCompletionDialog` and `CycleDetailDialog` as `on_save`
- Wired dashboard cascade refresh (`src/views/dashboard.py`)
  - `timeline.on_cycle_save = self._on_cycle_saved` after construction
  - `_refresh_header_badge()` computes cumulative dose and updates header badge
  - `_on_cycle_saved()` triggers both cardiotoxicity panel refresh and header badge refresh
- Added prospective cumulative-dose blocking to `CycleCompletionDialog`
  - `_check_cumulative_block(height_cm, weight_kg, agent, dose_mg_total)` computes prospective total
  - Edit path subtracts the old cycle's dox-equiv before adding the new value
  - Advisory mode → no blocking, returns `(None, None)`
  - Soft-block (red zone) → `_soft_block_dialog()`: red-accented Toplevel, requires non-empty reason, logs `override_red` audit action
  - Hard-block (hard_stop zone) → `_hard_stop_dialog()`: purple-accented Toplevel, requires ≥20-char attending reason with live char counter, logs `override_hard_stop` audit action
  - Added `override_red` and `override_hard_stop` to `services/audit.py` ACTIONS set
- Created `tests/test_cycle_blocking.py` — 15 tests:
  - Both override actions present in ACTIONS set
  - `write_audit` accepts both actions; stores override reason in after-JSON
  - Prospective math: new cycle adds; edit path subtracts old dox-equiv; epirubicin factor halved
  - Green and yellow-advisory paths return `(None, None)` without opening any dialog
  - Invalid height (zero BSA) skips block silently
  - Red soft-block path: `_soft_block_dialog` called; cancel returns `None`
  - Hard-stop path: `_hard_stop_dialog` called; cancel returns `None`

### Test Count
454 tests — 15 new tests, 0 regressions

### Decisions
- Treeview dose tag listed first in tag tuple so its `foreground` wins over stripe `background` — avoids needing per-cell style which Treeview does not support natively
- Prospective edit-path subtraction uses `cycle.dose_mg_per_m2` (stored field) not a re-computation — avoids BSA drift between cycles
- Soft-block dialog requires any non-empty reason; hard-stop dialog requires ≥20 chars — proportional friction to severity
- Override audit rows written after the cycle save succeeds, inside a try/except — DB failure logs but does not roll back the clinical save

### Next
- Day 19: Next V2 sprint story per plan

---

## 2026-04-26 — Sprint 6 Day 18 (US-026 Finish — Cumulative Dose Meter)

### Completed

- Added `_draw_meter()` method to `CardiotoxicityPanel` in `src/views/components/cardiotoxicity_panel.py`
  - `tk.Canvas` (height=26) packed `fill='x'` below the dose value row
  - Three zone tint backgrounds: dark green (0→300), dark yellow (300→400), dark red (400→450)
  - Filled bar in status color from 0 to current dose (clamped to max display range)
  - Tick marks + numeric labels at each threshold (300, 400, 450)
  - Fully responsive — redraws via `<Configure>` binding whenever the panel width changes
- Added `self._meter_canvas` reference to `__init__` (None until a patient is loaded)
- Updated class docstring to reflect complete feature set
- Created `tests/test_cardiotoxicity_panel.py` — 13 tests:
  - Panel loads without error, no patient, with patient no data, refresh
  - Meter canvas exists after load; is None before load (no patient)
  - Renders correctly at green / yellow / red / hard_stop dose levels
  - LVEF section still renders alongside cumulative dose section
  - `_draw_meter` called with width=0 and width=1 is a silent no-op
  - `_draw_meter` called at width=400 for all four statuses

### Test Count
439 tests — 13 new tests, 0 regressions

### Decisions
- Zone tint backgrounds use dark hex values (`#1a2e1a`, `#2e2810`, `#2e1010`) not palette constants — these are meter-specific and don't belong in the global palette
- `hard_stop` fill color reuses the red entry from `_CUMULATIVE_COLOR` — same visual severity
- Canvas height fixed at 26px (10px bar + tick gap + label space) — no need for dynamic height

### Next
- Day 19: US-026 follow-up or US-027 (next planned story per V2 sprint plan)

---

## 2026-04-26 — Sprint 6 Day 17 (US-024 Finish + US-026 Start — Cumulative Dose Badge)

### Completed

- Added `cumulative_status` tests (8 tests) to `tests/test_clinical_cardiotoxicity.py`
  - Green/yellow/red/hard_stop at exact threshold boundaries (300/400/450 mg/m²)
  - Zero dose → green; above hard_stop → hard_stop
- Added `cumulative_dose` service tests (7 tests) to `tests/test_cycle_service.py`
  - No cycles → green 0.0; no anthracycline data → green 0.0
  - Single dox cycle → ~60 mg/m² green; four cycles → ~240 mg/m² green
  - Prior exposure adds to total; yellow threshold test; agent breakdown populated
- Wired `cumulative_dose(conn, patient_id)` into `CardiotoxicityPanel.refresh()` (US-024)
  - Imported `cumulative_dose` from `services.cycles`
  - Called alongside LVEF queries; `CumulativeSummary` passed to new display method
- Added cumulative dose display to `CardiotoxicityPanel` (US-026 start)
  - `_show_cumulative(summary, thresholds)` renders above LVEF section
  - Total displayed as `X.X mg/m² dox-equiv` in status color (green/yellow/red)
  - Badge `[ADVISORY]` / `[HOLD]` / `[HARD STOP]` shown when status is not green
  - Threshold hint line: `300 advisory · 400 hold · 450 hard stop mg/m²`
  - Separator line between cumulative dose and LVEF sections
- Added `_CUMULATIVE_COLOR` and `_CUMULATIVE_BADGE` dicts to panel module

### Test Count
426 tests — 15 new tests, 0 regressions

### Decisions
- Cumulative section always renders when a patient is selected (even 0.0 green) — makes it clear dose data is being tracked, not absent
- `_CUMULATIVE_COLOR` maps `hard_stop` to the same red as `red` — hard_stop is the most severe red state
- Badge label uses "ADVISORY" (not "YELLOW") and "HOLD" (not "RED") — clinical language, not threshold names

### Next
- Day 18: US-026 finish — cumulative meter (visual progress bar against thresholds) in `CardiotoxicityPanel`

---

## 2026-04-26 — Sprint 6 Day 16 (US-025 Finish — LVEF Tracking)

### Completed

- Implemented `lvef_status(current_pct, baseline_pct, config)` pure function in `src/clinical/cardiotoxicity.py`
  - Absolute hold: `current < absolute_hold_pct` (50%)
  - Delta hold: `drop ≥ delta_hold_pct` (10pp) AND `current < delta_hold_absolute_ceiling_pct` (55%)
  - Review flag: `drop ≥ review_flag_delta_pct` (16pp)
  - All thresholds read from config dict — no magic numbers
- Created `src/views/dialogs/lvef_dialog.py` — `LvefDialog` (add) + `EditLvefDialog` (edit)
  - Fields: Assessment Date, LVEF %, Modality (echo/muga), Context (baseline/end_of_ac/ad_hoc), Notes
  - Validation: date required + valid, LVEF 10–85 required
  - Edit dialog pre-populates and routes through `update_lvef` with audit trail
- Created `src/views/components/cardiotoxicity_panel.py`
  - Shows latest LVEF + Δ from baseline colored by `lvef_status()` (green/yellow/red)
  - Status badge on hold/review state
  - History list with edit/delete per row (audit trail on delete)
  - Empty state with inline "+ Add LVEF" link
- Wired `CardiotoxicityPanel` into `DashboardView` as row 2 below labs/chart
- Added 15 `lvef_status` tests to `test_clinical_cardiotoxicity.py`

### Test Count
411 tests — 15 new tests, 0 regressions

### Decisions
- `cardiotoxicity_panel.py` created now (not Day 17) so LVEF history has a proper home; Day 17 will add the cumulative dose badge to the same component
- Status priority: absolute hold evaluated before delta hold before review — highest severity wins
- `delta_hold_absolute_ceiling_pct` boundary is exclusive (current must be strictly `<` ceiling to trigger delta hold)

### Next
- Day 17: US-024 finish (wire cumulative summary into dashboard data layer) + US-026 start (badge + cumulative meter in `cardiotoxicity_panel.py`)

---

## 2026-04-15 — Sprint 4 Day 40 (Stakeholder Demo #2 + Project Wrap-Up)

### Pre-Demo Setup
- Reset demo data via `python3 generate_demo_data.py` — clean state for Demo #2
- Demo data confirmed: DEMO-001 (mid-treatment), DEMO-002 (early, for live completion), DEMO-003 (complete)

### Demo #2 Results

**Stakeholder:** _______________________________________________

**Overall Reception:** ☐ Very Positive  ☐ Positive  ☐ Mixed  ☐ Needs Work

**30-Second Review:** ___ seconds  ☐ Passed  ☐ Close  ☐ Failed

**Key Positive Feedback:**
1.
2.
3.

**Suggestions / Requests:**
1.
2.

**Approval:** ☐ Approved  ☐ Conditional  ☐ Changes needed

### MVP Approval Status

| Demo | Stakeholder | Approval |
|------|-------------|---------|
| Demo #1 | _______________ | ☐ Approved  ☐ Conditional  ☐ Not approved |
| Demo #2 | _______________ | ☐ Approved  ☐ Conditional  ☐ Not approved |

**Overall MVP Status:** ☐ APPROVED  ☐ NEEDS WORK

### Sprint 4 Story Verification

| Story | Title | Points | Status |
|-------|-------|--------|--------|
| US-017 | View Patient Dashboard | 5 | ✅ Done |
| US-018 | Patient Header Display | 1 | ✅ Done |

**Sprint 4: 6/6 points delivered.**

### Sprint 4 Retrospective

**What went well:**
- Layout architecture decision (two-row grid, fixed header/timeline, expandable bottom) was correct from the start — no backtracking
- PatientHeader extraction into its own component was clean; no rework needed
- Integration testing (Day 34–35) caught two real bugs before demo (patient list 0/8, timeline status label)
- Performance targets beaten by wide margins on every metric

**What could be improved:**
- Some dialogs retained hardcoded colors from earlier sprints — a visual consistency audit at the end of Sprint 3 would have caught these before Sprint 4
- Demo data generation was added in Day 39 — earlier creation would have allowed more time to rehearse with realistic patient states

**What to do differently next sprint:**
- Add a demo data script at the start of any sprint with a stakeholder-facing output
- Run a grep audit for hardcoded colors and fonts at the end of every sprint, not just Sprint 4

### Deliverables
- `docs/PROJECT_SUMMARY.md` — project record: timeline, milestones, velocity, test coverage, performance, sign-off
- `docs/BACKLOG_V1_1.md` — prioritized feature backlog compiled from demo feedback and pre-identified gaps
- `v1.0.0` — release tag pushed to GitHub

---

## 2026-04-14 — Sprint 4 Day 39 (Stakeholder Demo #1)

### Pre-Demo Setup
- Created `generate_demo_data.py` — deterministic demo data script replacing random test data
- Three dedicated demo patients with fixed, predictable state:
  - **DEMO-001 A. Rivera** — 5/8 cycles, Cycle 3 @ 75% dose reduction (Neutropenia), 5 lab draws spanning all four ANC colors
  - **DEMO-002 M. Chen** — 1/8 cycles, Cycle 2 current (used for live cycle completion during demo)
  - **DEMO-003 P. Wallace** — 8/8 cycles complete, 8 lab draws across full treatment
- Database backed up to `chemo_dashboard_demo_backup.db` before demo

### Demo #1 Results

**Stakeholder:** _______________________________________________

**Overall Reception:** ☐ Very Positive  ☐ Positive  ☐ Mixed  ☐ Needs Work

**30-Second Review:** ___ seconds  ☐ Passed  ☐ Close  ☐ Failed

**Key Positive Feedback:**
1.
2.
3.

**Suggestions / Requests:**
1.
2.

**Approval:** ☐ Approved  ☐ Conditional  ☐ Changes needed

**Required Changes (if any):**
1.

### Post-Demo Actions
- Feedback categorized into: positive / quick fixes / v1.1 features / concerns
- Demo script adjustments for Demo #2: _______________________________________________

---

## 2026-04-14 — Sprint 4 Day 38 (Documentation & Demo Prep)

### Deliverables
- **README.md** — full rewrite: updated features list, added ANC color key table, fixed setup instructions, updated project structure with all Sprint 3+4 files, updated test count to 214
- **docs/DEMO_SCRIPT.md** — created: timed 15–20 min script with pre-demo checklist, segment talking points, anticipated Q&A table, and failure recovery plan
- **docs/FEEDBACK_FORM.md** — created: stakeholder form with overall impression, usability rating, 30-second review test table, value assessment, feature feedback, concerns, and MVP approval block with signature
- **docs/USER_GUIDE.md** — Sprint 4 updates: fixed "+ Add Labs" location reference (header, not nav bar), added Dashboard Overview section, added Patient Header section, added 30-Second Review tips section

### Test Count
214 tests — no new tests for documentation day

### Decisions
- Demo script structured as timed segments so presenter can pace without checking a clock
- Q&A table includes honest answers about EHR integration, multi-user, and other v1.0 limitations
- Feedback form MVP approval block has three tiers: Approved / Conditionally approved / Not approved

---

## 2026-04-13 — Sprint 4 Day 37 (UI Polish)

### Polish Actions
- Fixed `main.py` root window background: `'#1e1e1e'` → `BG` constant — now consistent with palette
- Grep audit confirmed zero hardcoded font sizes or hex colors in Sprint 4 files (`dashboard.py`, `patient_header.py`)
- 214 tests passing — no regression from polish changes

### Visual Consistency Audit — Sprint 4 Files
| File | Hardcoded fonts | Hardcoded colors | Result |
|------|----------------|-----------------|--------|
| `dashboard.py` | None | None | ✅ Clean |
| `patient_header.py` | None | None | ✅ Clean |

### Performance Status (from Day 35 — no changes needed)
| Operation | Target | Actual |
|-----------|--------|--------|
| `get_all_patients()` 20 patients | < 100ms | 0.1ms |
| `get_latest_lab()` | < 100ms | 0.0ms |
| `chart.refresh()` 20 labs | < 500ms | 26.4ms |

### Manual Visual Inspection Checklist
Items requiring live app verification (`python src/main.py`):

- [ ] Empty state "No patients" message centered and readable
- [ ] New patient shows `0/8` in Current Cycle column
- [ ] New patient dashboard: `Current: Cycle 1 (AC Phase)` shown
- [ ] Completed cycle: green box with ✓
- [ ] Current cycle: navy box with blue border
- [ ] Dose-modified cycle: orange ⚠ badge visible
- [ ] ANC value color-coded with dot + status label
- [ ] Dashed threshold line at 1.5 visible on chart
- [ ] All dialogs open centered on parent
- [ ] Window resize: components scale, nothing clips

### Decisions
- Pre-Sprint 4 hardcoded colors in dialogs and labs panel left as-is — out of Sprint 4 scope, no functional impact
- No performance optimization needed — all targets already beaten by wide margins

### Next
- Day 38: Documentation completion + demo preparation

---

## 2026-04-10 — Sprint 4 Day 31 (Sprint Planning)

### Sprint 4 Kickoff
- Sprint 3 complete — M3: Labs Working ✅, 145 tests passing, tagged v0.3-sprint3
- Sprint 4 goal: All components fully integrated into unified dashboard, end-to-end workflows tested, stakeholder demos completed, MVP validated for approval
- 6 story points across US-017 (5 pts) and US-018 (1 pt); significant non-story work (testing, demos, docs)
- Created `docs/SPRINT_4_PLAN.md` — full day-by-day plan, test checklists, demo script, feedback form

### Sprint 4 Stories Reviewed
- **US-017 View Patient Dashboard (5 pts):** All components on one screen, no scroll at 1920×1080, loads < 1 second, updates on data change
- **US-018 Patient Header Display (1 pt):** Name prominent, ID/Protocol/Start Date visible, header stays visible, correct patient shown

### Non-Story Work Planned

| Activity | Days |
|----------|------|
| End-to-end integration testing | 34–35 |
| Bug fixes | 36 |
| UI polish + performance | 37 |
| Documentation + demo prep | 38 |
| Stakeholder demo #1 | 39 |
| Stakeholder demo #2 + wrap-up | 40 |

### Layout Decision
- Two-row grid layout chosen (Option A): header row 0 fixed, timeline row 1 fixed, Labs+Chart row 2 expandable
- Bottom section: Labs 35% / Chart 65%
- `grid` geometry manager (not `pack`) for main dashboard

### Decisions
- `PatientHeader` will be a dedicated component in `src/views/components/patient_header.py`
- Header typography: FONT_TITLE for name, FONT_LABEL for details row — no hardcoded sizes
- Header colors: FG for name, FG_MUTED for details, BG_ALT background

### Next
- Day 32: Implement dashboard grid structure and place all components
- Day 33: Build PatientHeader component, finalize integration, mark US-017 and US-018 Done

---

## 2026-04-09 — Sprint 3 Days 28–30 (Testing, Polish, Review)

### Day 28 — Comprehensive Acceptance Testing
- Ran baseline: 118 tests passing
- Wrote acceptance-criteria tests for US-013: multiple labs saved separately, error label shown, ANC=50 triggers warning
- Wrote acceptance-criteria tests for US-014: two-patient isolation, yesterday label logic, panel updates after second lab
- Wrote acceptance-criteria tests for US-015: boundary values (1.49, 1.51, 0.5), all statuses have labels, color constants consistent, panel and chart use same `get_anc_status` function
- Wrote acceptance-criteria tests for US-016: 50-lab performance, duplicate dates, large date gaps, flat line (all same ANC), refresh after new lab
- Result: 135 passing, no bugs found

### Day 29 — Edge Cases + Polish + Docs
- Edge case tests: ANC=0.0, ANC=0.01, ANC=50 (warning not error), future date (+1 day), year 1900, only ANC filled
- Code review: no debug prints found in Sprint 3 code; matplotlib constants verified against palette
- Added docstrings to `_build_canvas` and `_draw_chart` in `anc_trend_chart.py` explaining embedding approach and color-coded marker strategy
- Updated `docs/USER_GUIDE.md`: added sections for Adding Lab Values, Latest Labs Panel, ANC Color Coding, ANC Trend Chart
- Result: 145 tests passing

### Day 30 — Sprint Review
- Dashboard integration confirmed: `ANCTrendChart` live in dashboard, wired to `_refresh_labs()` callback
- All 4 stories verified complete (see SPRINT_3_SUMMARY.md)
- M3: Labs Working — ACHIEVED ✅
- Tagged: v0.3-sprint3

### Decisions
- No bugs found during acceptance testing — all 4 stories shipped clean
- Edge case tests added directly to existing test files rather than new files — keeps test suite organized by module

### Next
- Sprint 4: Dashboard Integration & Polish (6 pts)

---

## 2026-04-05 — Sprint 3 Day 21 (Planning + Lab Entry Dialog Design)

### Sprint 3 Kickoff
- Reviewed Sprint 2 accomplishments — all 14 points delivered, M2: Timeline Working ✅
- Sprint 3 goal: Lab values entered with validation, latest labs display with ANC color coding, ANC trend chart visualizes blood count patterns over time
- Reviewed all 4 Sprint 3 stories and acceptance criteria in detail

### Story Acceptance Criteria Reviewed
- **US-013 Add Lab Values (3 pts):** Dialog with Date (required), ANC (required), WBC/Platelets/Hemoglobin (optional), numeric validation, save to database
- **US-014 View Latest Lab Values (1 pt):** Latest labs displayed prominently with date; empty state "No labs recorded"; updates after new entry
- **US-015 ANC Threshold Color Indicators (1 pt):** ANC color-coded — Green ≥1.5 (Normal), Yellow 1.0–1.49 (Mild), Orange 0.5–0.99 (Moderate), Red <0.5 (Severe); status label shown
- **US-016 View Lab Trend Chart (5 pts):** Line chart ANC over time; X-axis dates, Y-axis ANC; dashed reference line at 1.5; points below threshold highlighted; updates after new labs added

### Technical Approach Decided
- `get_anc_status(anc)` utility in `src/utils/anc_utils.py` — single source of truth for threshold colors/labels; reused in panel and chart
- Matplotlib embedded via `FigureCanvasTkAgg` from `matplotlib.backends.backend_tkagg`; color-coded markers overlaid on neutral line
- Validation ranges: ANC 0–20, WBC 0–50, Platelets 0–1000, Hemoglobin 0–20; values outside range trigger warning (not hard error)
- Dependency order: US-013 → US-014 + US-015 → US-016 → dashboard integration

### Day-by-Day Plan Confirmed
- Day 21: Planning + add_lab_dialog layout
- Day 22: Validation and save functionality
- Day 23: Latest labs display panel
- Day 24: ANC color coding
- Day 25: ANC color coding applied + chart research
- Day 26: Basic chart + threshold line
- Day 27: Chart styling and point highlighting
- Day 28: Chart integration and refresh
- Day 29: Testing and bug fixes
- Day 30: Sprint review and retrospective

### Development: Add Lab Values Dialog Design
- Created `src/views/dialogs/add_lab_dialog.py` with `AddLabDialog(tk.Toplevel)`
- Fields: Lab Date (default today), ANC* (required), WBC, Platelets, Hemoglobin, Notes (all optional)
- Grid layout: labels right-aligned col 0, entries col 1; hint text in smaller gray font below each field
- Required fields marked with `*`; optional fields labeled "(optional)"
- Added "+ Add Labs" button to dashboard header; `_on_add_labs()` opens dialog with patient context
- Dialog centers on parent, grabs focus, `<Return>` → save, `<Escape>` → cancel

### Decisions
- No cycle-association dropdown for MVP — adds complexity with little clinical value at this stage
- Notes field as single-line Entry (not Text widget) — keeps layout consistent with other dialogs
- "Add Labs" button placed in dashboard nav bar (top-right), consistent with "Add Patient" pattern

### Blockers
- None

### Next
- Day 22: Wire up input collection, validation logic (date, numeric, range warnings), save to database via `LabValue` model

---

## 2026-04-07 — Sprint 3 Days 25–27 (ANC Trend Chart — US-016)

### Morning Check-in
- Lab entry ✅ (US-013)
- Latest labs display ✅ (US-014)
- ANC color coding ✅ (US-015, 109 tests passing)
- Today: Start chart implementation — most complex part of Sprint 3

### Day 25 — Basic Chart Component
- Create `src/views/components/anc_trend_chart.py` with `ANCTrendChart(tk.Frame)`
- Embed via `FigureCanvasTkAgg` from `matplotlib.backends.backend_tkagg`
- `load_patient(patient_id)` and `refresh()` as public API
- Data: `get_labs_by_patient()` → extract dates + ANC sorted oldest→newest
- Empty state: message on axes when no data
- Single point: plot point + "Add more labs to see trend"
- Styling: axis labels ("Date", "ANC (K/μL)"), grid, line width 2, circle markers

### Day 26 — Threshold Line + Color-Coded Points
- Dashed threshold line at y=1.5 via `ax.axhline(y=1.5, color='red', linestyle='--')`
- Neutral gray trend line, colored markers per point via `get_anc_status()`
- X-axis: `AutoDateLocator` + `DateFormatter` for clean date labels, rotated if needed
- Polish: `fig.tight_layout()`, figure background matches dashboard, grid behind data (zorder)

### Day 27 — Dashboard Integration + Refresh
- Replace `chart_placeholder` in `dashboard.py` with real `ANCTrendChart`
- `refresh_labs()` in dashboard calls both `labs_panel.refresh()` and `chart.refresh()`
- `on_save` callback wired through to refresh both components after new lab entry
- Edge cases: 0 labs, 1 lab, 20+ labs, all normal, all below threshold, wide date range
- Tests: `tests/test_anc_trend_chart.py` covering data loading, empty/single state, refresh

### Decisions
- `get_anc_status()` reused from `anc_utils.py` — colors consistent between panel and chart
- Neutral gray line + colored overlay markers — more informative than single-color
- Chart column already reserved at 70% width from Gap 2 fix — swap placeholder for real component

### Next
- Sprint 3 review, retrospective, SPRINT_3_SUMMARY.md

---

## 2026-04-06 — Sprint 3 Day 24 (ANC Color Coding — US-015)

### Morning Check-in
- Lab entry ✅ (US-013 complete, 95 tests passing)
- Latest labs display ✅ (US-014 complete, gaps closed)
- Today: ANC threshold color coding — key clinical safety feature

### Plan
- Create `src/utils/anc_utils.py` with `get_anc_status(anc)` returning `{status, color, label}`
- Thresholds: ≥1.5 Normal (green), 1.0–1.49 Mild (yellow), 0.5–0.99 Moderate (orange), <0.5 Severe (red)
- Apply to `LatestLabsPanel`: colored ● indicator + value in threshold color + status label text
- Visual approach: combination of colored dot + colored value text (accessible — text label always present)
- Optional: color legend at bottom of panel
- Tests: `tests/test_anc_utils.py` covering all thresholds and edge cases

### Decisions
- Combination approach chosen (dot + colored text + label) over text-only or background highlight
- Text label always shown alongside color — does not rely on color alone (accessibility)
- Legend added to panel bottom — small, unobtrusive, helpful for first-time users
- `anc_utils.py` lives in `src/utils/` so chart (US-016) can reuse it without circular imports

### Next
- US-016: ANC trend chart with matplotlib (`FigureCanvasTkAgg`), threshold line at 1.5, color-coded markers

---

## 2026-03-15 — Sprint 2 Day 11

### Completed
- Created `src/views/components/` directory with `__init__.py`
- Built `TimelineComponent` class in `src/views/components/timeline.py`
- 8 cycle boxes displaying in two phase groups: AC (1-4) and T (5-8)
- Status-based colour scheme defined: pending (gray), current (blue), completed (green), modified (orange — Day 13)
- Phase accent colours defined for AC (blue) and T (purple)
- `_get_cycle_state()` determines visual state per cycle
- `_on_cycle_click()` placeholder bound to all cycle boxes — dialog wired on Day 13
- `cursor='hand2'` on all cycle boxes signals clickability
- `load_patient()` and `refresh()` as public API
- Integrated `TimelineComponent` into `DashboardView` — replaces Sprint 1 placeholder
- Verified 8 cycles display correctly with correct state colours

### Decisions
- Frame-based timeline chosen over Canvas — simpler event binding, easier widget composition
- `_rebuild_timeline()` destroys and recreates all boxes on refresh — simpler than diffing state
- `cycle_map` dict (cycle_number → Cycle) used for O(1) lookup during box creation
- `pack_propagate(False)` on each box enforces fixed 80×80 size regardless of content

### Technical Debt
- `COLORS['ac_phase']` and `COLORS['t_phase']` defined but not yet applied to phase labels — Day 12
- `_on_cycle_click()` is a placeholder — completion dialog wired on Day 13

### Next
- Day 12: Apply phase accent colours to labels, style completed/current/pending states fully, timeline refresh logic

---

## 2026-03-12 — Sprint 1 Day 8

### Completed
- Created `generate_test_data.py` in project root (US-021)
- Generates 5 synthetic patients with realistic initials, protocol, age, start date, diagnosis date
- 5 fixed progression profiles: early (0-2 cycles), mid (3-5), late (6-7), complete (8), dose-modified
- Lab values generated per completed cycle — ANC trends downward over treatment (myelosuppression simulation)
- WBC, platelets, hemoglobin also generated with gentle decline
- `clear_all_data()` deletes labs → cycles → patients in correct FK order
- CLI interface: `--patients N` and `--clear` flags via argparse
- Added Developer menu to macOS menu bar (US-022) — Generate Test Data and Clear All Data items
- Both menu actions show confirmation dialogs and auto-refresh patient list on completion

### Decisions
- Patient IDs fixed as `TEST-001`…`TEST-00N` — predictable, run `--clear` between generations
- Generator lives in project root (not `src/`) — adds `src/` to `sys.path` for model imports
- In-app access via macOS menu bar rather than UI button — keeps main interface clean

### Blockers
- None

### Next
- Day 9: Sprint 1 review — integration testing, bug fixes, self-demo against acceptance criteria
- Day 10: Retrospective, tag `v0.1-m1`, push to GitHub

---

## 2026-03-11 — Sprint 1 Day 7

### Completed
- Rebuilt `DashboardView` with real patient data — `set_patient()` loads full `Patient` object via `get_patient_by_db_id()`
- Added `get_patient_by_db_id(conn, db_id)` to `models.py` for lookup by integer primary key
- Patient header card displays: name (bold 20pt), ID · Protocol · Start Date in muted detail row
- `refresh()` method updates all header labels; handles no-patient state gracefully
- Added Treatment Timeline placeholder (left, 3/4 width) — "Coming in Sprint 2"
- Added Latest Labs placeholder (right, 1/4 width) — "Coming in Sprint 3"
- Dashboard layout: nav bar → patient header card → two-column content area
- Verified auto-save (US-020): added patient, force-quit, reopened — patient persisted
- `conn.commit()` in `add_patient()` documented as immediate disk write — no save button needed
- Added `- Remove Patient` button to patient list header (red, confirmation dialog, auto-refresh)

### Decisions
- `get_patient_by_db_id()` added alongside existing `get_patient_by_id()` (string) — both needed for different call sites
- `BG_ALT` used for header card and placeholder frames — consistent with Treeview row styling
- Timeline and labs placeholders use `grid()` with column weights (3:1) for proportional layout

### Blockers
- None

### Next
- Day 8: Synthetic data generator (`generate_test_data.py`) — 5 patients, varied cycles/labs, CLI flag `--patients N`
- Day 9: Sprint 1 review — bug fixes, self-demo against acceptance criteria, retrospective, tag `v0.1-m1`

---

## 2026-03-09 — Sprint 1 Day 5

### Completed
- Implemented `patient_list.py` with full Treeview (columns: Patient ID, Name, Current Cycle, Protocol)
- Cycle column shows completed count — e.g. `2/8` means 2 of 8 cycles done
- Patient DB id stored in both `iid` and row `tags` for reliable retrieval on click
- Added `+ Add Patient` label-button in header (placeholder — form in Day 6)
- Double-click row extracts patient id from tags, navigates to `DashboardView`
- Added `refresh()` public method — clears and reloads Treeview in one call
- Added `Patient.get_all(conn)` classmethod to `models.py`
- Applied full dark theme via `apply_dark_theme()` in `utils/__init__.py` — palette constants shared across all views
- Alternating row stripe colours (`#252525` / `#2a2a2a`), row height 32px, Arial 11 font
- Updated `DashboardView` with `set_patient(patient_id)` — updates header title and patient label
- Added `scripts/add_test_patients.py` for quick manual data insertion
- Tested complete flow with 0, 1, and 5 patients — all navigation checks passed
- 32/32 tests green throughout

### Decisions
- Completed cycle count used for Current Cycle column (not latest cycle number) — more clinically meaningful
- `BG_ROW_ODD` added to palette for alternating stripes without hardcoding colours in the view
- `set_patient()` separated from `__init__` so dashboard can be updated without full reconstruction
- Label-buttons used instead of `tk.Button` to avoid macOS system gray overriding dark header

### Blockers
- None

### Next
- Day 6: Add Patient form (ID, name, start date, protocol, validation, duplicate check, save/cancel, refresh list)
- Day 7: Patient selection, pass patient_id to dashboard, display patient name in header, test full List→Dashboard→Back flow
- Day 8: Verify auto-save, test persistence across restarts, handle DB errors, cycle/lab CRUD + tests
- Day 9: generate_test_data.py — 5 synthetic patients, varied cycles/labs, CLI flag --patients N
- Day 10: Sprint 1 review — bug fixes, self-demo against acceptance criteria, retrospective, tag v0.1-m1

---

## 2026-03-08 — Sprint 1 Phase 4

### Completed
- Added frame navigation system to `main.py`: stacked frames in a container, `show_frame()` switches views with `tkraise()`
- DashboardView is always recreated on each visit to load fresh patient data; PatientListView is persistent
- Created stub `src/views/patient_list.py` — navigates to DashboardView
- Created stub `src/views/dashboard.py` — navigates back to PatientListView
- Added `src/utils/__init__.py` with `show_error()` and `show_info()` dialog helpers
- Verified navigation programmatically — all 32 tests still green, no circular imports

### Decisions
- Views imported inside methods (not at module level) to avoid circular imports
- `show_frame(**kwargs)` passes keyword args to view constructors for future patient_id routing
- Utils helpers wrap messagebox — single import point for all dialogs

### Blockers
- None

### Next
- Phase 5: Implement patient list (Treeview, columns: ID/Name/Cycle/Status, empty state, Add Patient button, click-to-navigate, test empty + manual data)
- Phase 6: Add Patient form (ID, name, start date, protocol, validation, duplicate check, save/cancel, refresh list)
- Phase 7: Patient selection, pass patient_id to dashboard, display patient name in header, test full List→Dashboard→Back flow
- Phase 8: Verify auto-save, test persistence across restarts, handle DB errors, cycle/lab CRUD + tests
- Phase 9: generate_test_data.py — 5 synthetic patients, varied cycles/labs, CLI flag --patients N
- Phase 10: Sprint 1 review — bug fixes, self-demo against acceptance criteria, retrospective, tag v0.1-m1

---

## 2026-03-07 — Phase 0.2 & Sprint 1 (Phases 1-3)

### Completed
- Tested IDE configuration (VS Code) — Python interpreter, test discovery, all 12 tests green
- Verified Tkinter v8.6 with live window test — opened and closed cleanly
- Reviewed all 22 Sprint 1 stories
- Created `models.py` with dataclasses for `Patient`, `Cycle`, and `Lab`
- Built full CRUD functions for Patient, Cycle, and Lab in `models.py`
- Wrote 20 model tests — all passing (32 total across database + models)
- Fixed Python 3.12 date adapter deprecation warnings in `database.py`
- Created `main.py` with `App` window class, DB initialization, and clean close handler
- Verified main window opens and closes cleanly (exit code 0)
- Added inline comments across `database.py`, `models.py`, and `main.py`
- Created `.vscode/settings.json` for Python interpreter and pytest configuration

### Decisions
- CRUD functions live in `models.py` alongside dataclasses — keeps the data layer together
- `create_tables()` accepts a connection object directly — required for in-memory test isolation
- `App` inherits from `tk.Tk` — App IS the window, no separate root object needed
- Date adapters registered at module level in `database.py` — applies globally on import
- Full CRUD for all fields now rather than MVP-only fields — avoids revisiting mid-sprint

### Blockers
- None

### Next
- Phase 4: Frame navigation, `patient_list.py` view, `dashboard.py` view, error handling
- Phase 5: Patient list with Treeview, Add Patient button, click-to-navigate, test with empty DB

---

## 2026-03-07 — Phase 0.1 & 0.2 (Setup)

### Completed
- Verified Python 3.12.4
- Created project directory
- Created and activated virtual environment (`venv/`)
- Installed dependencies: `matplotlib`, `pytest`
- Verified Tkinter v8.6 available
- Initialized Git repository
- Created folder structure (`src/`, `tests/`, `data/`, `docs/`)
- Populated `requirements.txt` with pinned dependencies
- Created and tested `database.py` with SQLite (patients, cycles, labs tables)
- Wrote 12 database tests — all passing
- Cleaned and finalized `PLANNING.md`
- Created GitHub repository and pushed
- Set up Trello board with all 22 user stories across 4 sprints
- Emailed oncologists to schedule milestone demos

### Decisions
- One `PLANNING.md` file instead of one per phase (solo project, easier to maintain)
- `create_tables()` accepts an optional connection object to support in-memory testing

### Blockers
- None

### Next
- ~~Test IDE configuration~~ Done
- ~~Quick Tkinter test~~ Done
- ~~Review Sprint 1 stories~~ Done
- ~~Begin Sprint 1~~ Done
