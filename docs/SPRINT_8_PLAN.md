# Sprint 8 Plan — Workflow & Alerts

**V2 · Weeks 19–20 · Days 31–41 of V2**

---

## Sprint Goal

Monday morning the nurse opens the app and the dashboard tells her — without her having to look — **who is due, who is overdue, who has unsafe labs, and who is approaching a safety threshold**. Before any cycle is completed, the **pre-cycle safety checklist** runs every rule the prior sprints built and either greenlights, advises, soft-blocks, or hard-blocks the cycle. A **low-ANC banner** sits at the top of any patient with neutropenia. The patient list gains **search, filter, and sort** so finding a specific patient takes one keystroke instead of a scroll.

**This is the integration sprint.** Sprint 5 gave us audit and config; Sprint 6 gave us cardiotoxicity data; Sprint 7 gave us toxicity data. Sprint 8 turns that data into decisions. By Day 41 every safety-critical rule that ships in V2 lives as a pure function in `clinical/` and runs through one aggregator before the cycle save button does anything.

**No safety-critical decision should require the nurse to remember a threshold or look at a separate screen.**

---

## Stories

| Story | Title | Points | Status |
|-------|-------|--------|--------|
| US-031 | Patient list search + filter + sort | 2 | To Do |
| US-032 | Next-cycle-due / overdue status | 3 | To Do |
| US-033 | Pre-cycle safety checklist | 4 | To Do |
| US-034 | Low-ANC alert banner | 2 | To Do |

**Total: 11 story points · 11 development days**

---

## Sequencing

```
US-031 ─┐                                                ┌─► US-033 ─► (integration)
US-034 ─┤── independent warm-ups (Days 32–33)           │
US-032 ─┘                                                │
                                                         │
       ┌─────────────────────────────────────────────────┘
       │
   Days 35–39 — the cross-cutting capstone
```

- **US-031 + US-034 are warm-ups.** Both are self-contained, low-risk, and surface UI patterns we'll reuse in US-033 (search box, dismissible banner). Land them first.
- **US-032 next.** It introduces cycle-scheduling math (`expected_cycle_date(last_cycle_date, dose_density)`) which US-033 reuses for its "labs-within-72h" rule.
- **US-033 last and longest.** Five days of Sprint 8 belong to it — every prior sprint feeds into it, and it must integrate with the cycle-completion dialog without breaking the existing override flow Sprint 6 built.

---

## Dependencies (must be done)

| From | Artifact | Why Sprint 8 needs it |
|------|----------|-----------------------|
| Sprint 5 | Migration framework | US-032 ships one column (`patient.last_cycle_date_cached` is **out of scope** — compute on the fly from `cycle` rows; no new columns) |
| Sprint 5 | Institution config | Every rule reads thresholds, blocking modes, lookback windows from YAML |
| Sprint 5 | Audit log | Every override on the checklist writes an audit row |
| Sprint 5 | `dose_density` on patient (US-019) | US-032 cadence math needs it |
| Sprint 6 | Cumulative dose service + LVEF service | US-033 cumulative-headroom rule + LVEF rule call these |
| Sprint 6 | Cycle-completion override flow | US-033 plugs in *upstream* of the existing red / hard-stop / LVEF dialogs — must not duplicate or replace them |
| Sprint 7 | Neuropathy, infusion reaction, symptom services | US-033 rules read from each |
| V1 | Patient list view, ANC trend chart, lab service | US-031 extends list query; US-034 reads latest ANC; US-033 lab-freshness rule reads `lab.draw_date` |

If `dose_density` is not on every patient row, **fix in Sprint 8 Day 31 before touching US-032** — fall-back to `standard_q3w` is acceptable but must be explicit, not inferred.

---

## Pre-Sprint: Specialist YAML Review (Day 31 morning)

V2-plan questions for Sprint 8. Resolve on Day 31 or accept defaults and note in `PROJECT_LOG.md`.

| Question | Default | Decision | Source |
|----------|---------|----------|--------|
| Pre-cycle ANC — AC | ≥ 1500 /µL | ☐ Accept · ☐ Override | |
| Pre-cycle ANC — T | ≥ 1500 /µL | ☐ Accept · ☐ Override | |
| Pre-cycle ANC — dose-dense (cycle ≥ 2) | ≥ 1000 /µL | ☐ Accept · ☐ Override | |
| Pre-cycle platelets | ≥ 100,000 /µL | ☐ Accept · ☐ Override | |
| Lab freshness window | ≤ 72 h from draw to administration | ☐ Accept · ☐ Override | |
| Cycle-due lookahead | 7 d (yellow when due within 7 d) | ☐ Accept · ☐ Override | |
| Cadence — standard q3w | 21 d | ☐ Accept · ☐ Override | |
| Cadence — dose-dense q2w | 14 d | ☐ Accept · ☐ Override | |
| Low-ANC banner — red threshold | < 500 /µL | ☐ Accept · ☐ Override | |
| Low-ANC banner — orange threshold | 500–999 /µL | ☐ Accept · ☐ Override | |
| Per-rule blocking mode (advisory / soft / hard) | see table in *Config Additions* | ☐ Accept · ☐ Override | |
| Active-infection attestation required? | yes (nurse checkbox, not enforced lab) | ☐ Accept · ☐ Override | |
| Hard-gate vs advisory preference for checklist as a whole | rules-level only (no checklist-wide hard gate) | ☐ Accept · ☐ Override | |

Deliverable: one YAML diff against `config/institution.defaults.yaml` committed Day 31.

---

## Architecture Additions

Sprint 8 adds **two new clinical modules and one rules aggregator**, extends the patient list query, and inserts one new dialog into the cycle-completion flow. **No new package, no rules registry, no base class.** Each rule is a flat pure function with a uniform return shape.

```
src/
├── clinical/
│   ├── scheduling.py            ← NEW — expected_cycle_date, status from cadence
│   └── precycle.py              ← NEW — one pure function per checklist rule + aggregator
├── services/
│   ├── patients.py              ← extend: search/filter/sort query
│   ├── cycles.py                ← extend: last_cycle_date(patient_id) helper
│   └── checklist.py             ← NEW — gather inputs from every service, call clinical/precycle
└── views/
    ├── components/
    │   ├── patient_list.py          ← extend: search box, sort headers, status column
    │   ├── low_anc_banner.py        ← NEW — dashboard-top banner, dismissible per session
    │   └── cycle_status_indicator.py ← NEW — green/yellow/red dot + tooltip for patient list
    └── dialogs/
        └── precycle_checklist_dialog.py ← NEW — runs before cycle-completion override flow
tests/
├── test_clinical_scheduling.py
├── test_clinical_precycle.py        ← one test class per rule + aggregator tests
├── test_checklist_service.py
├── test_patient_list_search.py
├── test_low_anc_banner.py
└── test_precycle_checklist_dialog.py
```

**Pattern carried forward from Sprints 6 and 7:**
- `clinical/` modules import nothing from `services/`, `views/`, or `sqlite3`. Primitives in, primitives out.
- All thresholds, modes, vocabularies via config.
- Rule return shape (uniform): `RuleResult(rule_id: str, status: 'pass'|'advisory'|'soft_block'|'hard_block', message: str, value: Any | None, threshold: Any | None)`.
- Aggregator returns `ChecklistResult(rules: list[RuleResult], worst_status: str, can_save_without_override: bool)`.
- Dialog renders the list verbatim — no rule logic in the view.

---

## Schema Migrations

**None.** Sprint 8 is read-only against the schema. Every signal it surfaces was persisted by Sprint 5/6/7. If you find yourself adding a column, stop — the answer is already in the cycle, lab, neuropathy, reaction, symptom, or LVEF table.

The one exception we will *consider* and likely defer: a `cycle.checklist_overrides_json` field for storing exactly which rules were overridden on a given save. **Decision deferred to Day 39** based on whether the audit log alone is sufficient. Default position: skip the column; audit rows with `action='checklist_override'` and a JSON `details` field are enough.

---

## Config Additions (`config/institution.defaults.yaml`)

```yaml
scheduling:
  cadence_days:
    standard_q3w: 21
    dose_dense_q2w: 14
  due_within_days: 7              # yellow-status window
  overdue_after_days: 0           # red the day after expected date

labs:
  freshness_hours: 72             # max age of labs at cycle administration

precycle:
  anc:
    ac:        { min_per_uL: 1500 }
    t:         { min_per_uL: 1500 }
    dose_dense_from_cycle_2: { min_per_uL: 1000 }
  platelets:
    min_per_uL: 100000
  active_infection:
    require_nurse_attestation: true
  neuropathy_t_phase_max_grade: 1   # T-phase only; AC ignores this rule
  symptoms_advisory_grade: 3        # ≥3 surfaces as advisory
  # Cumulative dose and LVEF rules read their thresholds from cardiotoxicity:* (Sprint 6)

  blocking_modes:
    anc_below_threshold:        soft_block
    platelets_below_threshold:  soft_block
    labs_stale:                 advisory
    active_infection:           soft_block
    cumulative_red:             soft_block          # mirrors Sprint 6
    cumulative_hard_stop:       hard_block          # mirrors Sprint 6
    lvef_abnormal:              soft_block
    neuropathy_t_above_max:     soft_block
    symptoms_grade_3_or_higher: advisory

alerts:
  low_anc_banner:
    red_below_per_uL: 500
    orange_below_per_uL: 1000
    dismiss_scope: session            # 'session' | 'until_next_lab'
```

**Sources of truth, restated:**
- Cumulative-dose thresholds → `cardiotoxicity.cumulative_thresholds_mg_per_m2` (Sprint 6, unchanged)
- LVEF thresholds → `cardiotoxicity.lvef.*` (Sprint 6, unchanged)
- Neuropathy grade-action mapping → `toxicity.neuropathy.grade_actions` (Sprint 7, unchanged)

Sprint 8 **does not duplicate these values** — its rules read from the same keys Sprints 6/7 wrote.

---

## Rule Catalogue (US-033)

Each row = one pure function in `clinical/precycle.py`, one test class. The aggregator calls them in this order:

| # | Rule ID | Phase | Inputs | Default mode |
|---|---------|-------|--------|--------------|
| 1 | `anc_below_threshold` | both | latest ANC, phase, dose-density, cycle # | soft_block |
| 2 | `platelets_below_threshold` | both | latest platelets | soft_block |
| 3 | `labs_stale` | both | latest lab `draw_date`, planned admin date | advisory |
| 4 | `active_infection` | both | nurse attestation checkbox | soft_block |
| 5 | `cumulative_red` | AC | `CycleService.cumulative_dose()` | soft_block |
| 6 | `cumulative_hard_stop` | AC | `CycleService.cumulative_dose()` | hard_block |
| 7 | `lvef_abnormal` | AC | latest + baseline LVEF | soft_block |
| 8 | `neuropathy_t_above_max` | T | latest neuropathy effective grade | soft_block |
| 9 | `symptoms_grade_3_or_higher` | both | latest cycle's symptom grades | advisory |

**Phase detection:** positional, matching Sprint 7's convention — cycles 1–4 = AC, 5–8 = T. The phase is computed once at checklist start and passed into every rule.

**Sprint 6 overlap is intentional, not duplication:** rules 5/6/7 already exist in `cycle_completion_dialog._on_save()` as standalone gates. Sprint 8 *moves the call site*: the checklist dialog runs first, the existing override dialogs trigger only when their rule fails. The Sprint 6 dialogs are not rewritten — they're invoked from the new flow.

---

## Day-by-Day Plan

### DAY 31 — Sprint planning, specialist review, scaffolding
**Morning (~2h)** — Specialist YAML review; commit overrides (or accept defaults and note in `PROJECT_LOG.md`). Verify `dose_density` populated for every patient in fixture + demo DBs.
**Afternoon (~3h)** — Add `scheduling:`, `labs:`, `precycle:`, and `alerts:` blocks to `config/institution.defaults.yaml`. Scaffold `src/clinical/scheduling.py`, `src/clinical/precycle.py`, `src/services/checklist.py`, and the four new view modules with empty signatures. Empty test files.
**Commit:** `Added Sprint 8 workflow and alerts scaffolding`

### DAY 32 — US-031: search + filter + sort
- Extend `services/patients.py` with `list_patients(search: str = "", sort_by: str = "name", sort_dir: str = "asc", phase_filter: str | None = None) -> list[Patient]`. Soft-deleted excluded as today.
- Extend `views/components/patient_list.py`:
  - Search box at top — substring match on patient_id and name (case-insensitive). Live as the user types, debounced ~150 ms.
  - Sort by clicking column headers (name, last cycle date, cumulative dose, dose-risk badge).
  - Filter dropdown: All / AC phase / T phase / Completed.
- Tests: query-layer correctness, sort directions, filter combinations, empty-result state.
**Commit:** `Added patient list search, filter, and sort`
**US-031 DONE — 2 pts**

### DAY 33 — US-034: low-ANC banner
- `views/components/low_anc_banner.py`: red bar < 500, orange bar 500–999, hidden ≥ 1000. Reads thresholds from config.
- Mounted at the top of the dashboard, above the patient header. Dismiss button stores dismissal in a session-scoped dict keyed by `patient_id` (default `dismiss_scope: session`).
- If `dismiss_scope: until_next_lab` configured, dismissal expires when a newer lab row is created for the patient.
- Tests: threshold boundaries, dismiss/restore, multi-patient session state.
**Commit:** `Added low-ANC alert banner with dismissible session state`
**US-034 DONE — 2 pts**

### DAY 34 — US-032 part 1: scheduling math + status function
- Implement `clinical/scheduling.py`:
  - `expected_cycle_date(last_cycle_date, dose_density, config) -> date` — adds cadence days from config.
  - `cycle_status(last_cycle_date, dose_density, today, config) -> Literal['on_schedule', 'due_soon', 'overdue', 'no_cycles']` — returns status and the day count.
- Pure functions; tested against fixtures for both q3w and q2w, edge cases at the boundary (`due_within_days`, day-of expected, day after).
- `services/cycles.py`: add `last_completed_cycle_date(patient_id) -> date | None` helper, soft-deletes excluded.
**Commit:** `Added cycle scheduling rules and last-cycle helper`

### DAY 35 — US-032 part 2: status column + indicator
- `views/components/cycle_status_indicator.py`: dot widget — green / yellow / red / gray (no cycles) — with hover tooltip "Last cycle 2026-04-08 · expected 2026-04-29 · due in 2 days".
- Add as new column in patient list (between name and Dose Risk). Sortable by status.
- Hook into refresh: list re-evaluates status on every dashboard load and after every cycle save.
- Integration test: 4-patient fixture covering all four status states; sort behavior.
**Commit:** `Added next-cycle-due status column to patient list`
**US-032 DONE — 3 pts**

### DAY 36 — US-033 part 1: rule scaffolds + aggregator + first three rules
- Define `RuleResult` and `ChecklistResult` dataclasses in `clinical/precycle.py`.
- Implement aggregator: `run_checklist(inputs: ChecklistInputs, config) -> ChecklistResult` — calls every rule, collects results, computes `worst_status` and `can_save_without_override`.
- Implement first three rules as pure functions with full unit-test coverage:
  - `anc_below_threshold` — picks the right threshold from `precycle.anc.*` based on phase + dose-density + cycle number.
  - `platelets_below_threshold` — flat threshold from config.
  - `labs_stale` — compares latest lab `draw_date` to planned admin date; window from `labs.freshness_hours`.
- Aggregator unit-tested with 3-rule fixture: all-pass, one-soft-block, one-advisory cases.
**Commit:** `Added pre-cycle checklist aggregator and lab/ANC rules`

### DAY 37 — US-033 part 2: cardiotoxicity + LVEF rules (AC) + active infection
- `cumulative_red` and `cumulative_hard_stop` — call `CycleService.cumulative_dose()` (Sprint 6); thin wrappers that produce `RuleResult` from the same status. **Reuses Sprint 6 logic; does not reimplement.**
- `lvef_abnormal` — call `lvef_status()` (Sprint 6); wrap result.
- `active_infection` — uses `inputs.nurse_attests_no_infection: bool`; if `require_nurse_attestation: true` and the flag is missing/false, returns `soft_block`.
- AC-only gating: rules 5/6/7 short-circuit to `pass` when `inputs.phase == 't'`.
- Tests: each rule independently; AC-vs-T gating verified.
**Commit:** `Added cardiotoxicity, LVEF, and infection rules to checklist`

### DAY 38 — US-033 part 3: T-phase neuropathy + symptoms rule
- `neuropathy_t_above_max` — calls `services.neuropathy.latest_neuropathy()`, computes `effective_grade()` (Sprint 7), compares to `precycle.neuropathy_t_phase_max_grade`. T-phase only; AC short-circuits to `pass`.
- `symptoms_grade_3_or_higher` — calls `services.symptoms.latest_cycle_symptoms()`; advisory if any symptom at-or-above `precycle.symptoms_advisory_grade`.
- Tests: phase gating, threshold boundaries, no-data path (no neuropathy assessment yet → `pass` with explanatory message, not `soft_block`).
- `services/checklist.py`: assemble `ChecklistInputs` from every service in one query batch — labs, cumulative-dose summary, latest LVEF, latest neuropathy, latest cycle symptoms, latest cycle date, dose-density, planned admin date.
**Commit:** `Added neuropathy and symptoms rules and checklist input gathering`

### DAY 39 — US-033 part 4: dialog + cycle-completion integration
- `views/dialogs/precycle_checklist_dialog.py`:
  - Header: patient name, planned cycle # and phase, planned admin date.
  - Rule list: one row per `RuleResult` with status icon, message, value vs threshold.
  - Active-infection nurse attestation checkbox at the top of the list (default unchecked).
  - "Proceed" button:
    - Enabled when `worst_status` ∈ {`pass`, `advisory`}: proceeds straight to cycle-completion dialog with no override prompt.
    - Disabled when any `hard_block`: "Proceed" greyed out, attending-override path explains *which* rule blocks.
    - Confirmation dialog when any `soft_block`: requires reason text (≥ 20 chars), writes one `audit.record(action='checklist_override', details={'rules':[...], 'reason':...})` row.
- Hook into `CycleCompletionDialog`: on cycle save click, run checklist first; only if checklist clears (or override applied) does the existing Sprint-6 override flow run.
- **Decision on `cycle.checklist_overrides_json`:** keep audit log as the single record; no schema change.
- Integration test: full path on a fresh fixture patient — pass / advisory / soft-block-with-override / hard-block-blocked.
**Commit:** `Added pre-cycle checklist dialog and cycle integration`

### DAY 40 — Integration sweep + end-to-end
- End-to-end test: a fixture patient mid-AC-phase, fresh labs, normal LVEF, no neuropathy → checklist all green → cycle completes silently.
- E2E test: same patient with ANC 900 (AC, dose-dense from C2 → still below 1000 if first cycle, soft_block at 900 ≤ 1000) → soft-block → override with reason → audit row → cycle completes.
- E2E test: AC patient at 412 mg/m² doxorubicin → cumulative_red soft_block + cumulative-dose dialog from Sprint 6 chain together correctly (one override, two audit rows acceptable: `checklist_override` and `override_red`).
- E2E test: T-phase patient with effective neuropathy G2 → `neuropathy_t_above_max` soft_block → override path.
- Regression sweep: every Sprint 5/6/7 test passes; cycle-completion override flow unchanged when checklist clears.
- Performance: dashboard load with checklist input gathering < 100 ms additional at P95 on demo DB.
**Commit:** `Added Sprint 8 end-to-end integration coverage`
**US-033 DONE — 4 pts**

### DAY 41 — Demo, retro, summary
- Demo walkthrough on demo DB: open dashboard → low-ANC banner visible on one patient → search "PT-005" → click → see overdue-status indicator → click cycle save → checklist runs → green except labs-stale advisory → proceed → cycle saves.
- Second walkthrough: T-phase patient with G2 neuropathy → checklist soft-blocks → enter override reason → audit viewer (US-022) shows `checklist_override` with rule details.
- Write `docs/SPRINT_8_SUMMARY.md` matching the Sprint 7 summary shape.
- Update `docs/PROJECT_LOG.md` close-out entry.
- Tag `v2-sprint8`.
**Commit:** `Added Sprint 8 summary and close-out`

---

## Story Acceptance Criteria

### US-031 — Patient list search + filter + sort (2 pts)
- [ ] Search box filters patient list by substring on id + name, case-insensitive, debounced
- [ ] Column headers (name, last cycle date, cumulative dose, dose-risk badge, status) all sortable
- [ ] Phase filter: All / AC / T / Completed
- [ ] Empty-result state shows "No patients match" with a "Clear filters" link
- [ ] No regression in existing patient-list rendering or row tags
- [ ] Query-layer test coverage on `services/patients.list_patients` ≥ 90%

### US-032 — Next-cycle-due / overdue status (3 pts)
- [ ] `expected_cycle_date()` and `cycle_status()` are pure functions in `clinical/scheduling.py`
- [ ] Cadence honored from config: q3w = 21 d, q2w = 14 d
- [ ] Status states: green (on schedule), yellow (due within `due_within_days`), red (overdue), gray (no cycles)
- [ ] Status column visible in patient list with sortable header
- [ ] Tooltip on indicator shows "last cycle / expected / days until/since"
- [ ] Status updates after every cycle save without app restart
- [ ] Unit + integration test coverage on `clinical/scheduling.py` ≥ 90%

### US-033 — Pre-cycle safety checklist (4 pts)
- [ ] Nine rules implemented as independent pure functions in `clinical/precycle.py`
- [ ] Each rule returns the uniform `RuleResult` dataclass shape
- [ ] Aggregator returns `ChecklistResult` with `worst_status` and `can_save_without_override`
- [ ] Phase-gated rules short-circuit to `pass` outside their phase
- [ ] Cumulative-dose and LVEF rules **delegate** to Sprint 6 logic (no reimplementation)
- [ ] Neuropathy rule **delegates** to Sprint 7 `effective_grade()` (no reimplementation)
- [ ] Active-infection nurse attestation checkbox present in dialog
- [ ] Per-rule blocking mode read from `precycle.blocking_modes` — every rule is downgradable
- [ ] Checklist runs **before** the existing cycle-completion override flow
- [ ] Soft-block override requires ≥ 20-char reason; writes one `checklist_override` audit row
- [ ] Hard-block disables Proceed and explains which rule(s) block
- [ ] No new schema columns; all data sourced from existing tables
- [ ] Unit test per rule + aggregator integration tests + dialog integration tests
- [ ] Coverage on `clinical/precycle.py` ≥ 90%

### US-034 — Low-ANC alert banner (2 pts)
- [ ] Banner renders red < 500, orange 500–999, hidden ≥ 1000 (thresholds from config)
- [ ] Banner mounted at dashboard top, above patient header
- [ ] Dismiss button hides banner for that patient for the session
- [ ] `dismiss_scope: until_next_lab` honored when configured
- [ ] Banner reappears when a newer lab row pushes ANC under threshold again (after dismissal expiry)
- [ ] Test coverage on threshold boundaries and dismiss/restore behavior

---

## Success Criteria (sprint-level)

- [ ] All four stories merged to master, tagged `v2-sprint8`
- [ ] Coverage on `src/clinical/scheduling.py` and `src/clinical/precycle.py` ≥ 90%
- [ ] Coverage on `src/services/checklist.py` ≥ 85%
- [ ] No regressions in Sprint 5, 6, or 7 test suites
- [ ] Dashboard load with checklist gathering, status column, banner, search-enabled list < 250 ms at P95 on demo DB (200 ms target + 50 ms budget for the new work)
- [ ] Demo walkthrough (Day 41) covers all four stories without manual DB poking
- [ ] Zero magic numbers in code — every threshold, cadence, mode, and lookback resolves through config
- [ ] Audit viewer (US-022) shows `checklist_override` rows with rule list and reason
- [ ] No new schema migrations shipped this sprint

---

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| US-033 grows past its 4-pt budget because every prior sprint feeds it | High | Five days allocated (Days 35–39); each rule day-bounded; aggregator landed Day 36 so dialog work on Day 39 is wiring-only |
| Checklist duplicates Sprint 6 cumulative/LVEF rules instead of delegating | High | Rules 5/6/7 are explicitly thin wrappers around Sprint 6 services; reviewed against `cycle_completion_dialog._on_save()` on Day 37 |
| Two override prompts fire on the same save (checklist + Sprint 6 dialog) | Medium | Two audit rows is acceptable; document in summary. Alternative — collapsing into one dialog — is V2.1 polish, not Sprint 8 |
| Specialist review on Day 31 slips | Medium | Ship defaults; a YAML override later does not require code change |
| `dose_density` missing on legacy patients breaks US-032 | Low | Day-31 verification step + explicit `standard_q3w` fallback at the query layer; not silent |
| Banner-dismissal session state leaks across patients | Low | State keyed by `patient_id`; covered by tests |
| Search-box live filter is laggy on large patient lists | Low | Debounce ~150 ms; query-layer indexed on `name` already (V1) |
| Active-infection attestation defaults to "yes, no infection" and gets clicked through | Medium | Default unchecked; soft-block fires until checked; nurse must take an explicit action |
| Performance regression from per-row checklist evaluation in patient list | Medium | Patient list shows status indicator only (one query: `last_completed_cycle_date`). **Full checklist runs only at cycle-save, not at list-render time** |
| Schema-creep: a column that "would make this easier" | High | None this sprint. Confirmed in *Schema Migrations* section |

---

## Out of Scope (reject on sight)

- Push notifications / OS toasts on overdue patients → V3 (UI-blocking decision; per V2 plan)
- Email/SMS reminders → V3
- Predictive ANC modeling ("ANC will likely be 800 at next cycle") → V3 cohort analytics
- Cohort-level checklist failure rates → V3 (needs accumulated data)
- Auto-rescheduling overdue cycles → V3 workflow
- Calendar integration / iCal export → V3
- Patient-facing pre-cycle reminders → V3 (different product)
- Multi-day worklist / "this week's patients" PDF → Sprint 9 (reporting), not here
- Hardcoded checklist rules per protocol → V3 (multi-protocol is V3)
- Whole-checklist hard gate (vs per-rule modes) → V2.1 if specialist review demands it; defaults stay rule-level

If any of the above surfaces mid-sprint, log to `docs/BACKLOG_V3.md` and move on.

---

## Definition of Done (per story)

1. Code committed with single-line `Added ...` message
2. Unit tests on every pure function + integration test on every dialog/component
3. Config values, vocabularies, and thresholds read from YAML, not hardcoded
4. Audit entries written for every override (US-033 only)
5. Component rendered cleanly at 1920×1080 and 1024×768
6. Status indicator / banner / search / checklist visible on dashboard with current data
7. No regression in Sprint 5, 6, or 7 test suite
8. Entry in `PROJECT_LOG.md` for the day

---

## Post-Sprint Carry-Over Protocol

If any story is incomplete at end of Day 41:

- **US-031 incomplete** → carry into Sprint 9 Day 1 (no downstream dependency).
- **US-032 incomplete** → carry into Sprint 9 Day 1; status column hidden until ready.
- **US-033 incomplete (rules done, dialog incomplete)** → ship the aggregator and a minimal dialog; defer per-rule UX polish to Sprint 10.
- **US-033 incomplete (rules incomplete)** → **Sprint 8 cannot close.** Extend by 2 days rather than ship a partial checklist. A partial pre-cycle checklist is a safety hole that the rules engine cannot detect — every rule must land or every rule must be explicitly disabled in config (`mode: advisory`).
- **US-034 incomplete** → carry into Sprint 9 Day 1 (no downstream dependency).

**Do not start Sprint 9 with US-033 carry-over still open.** Sprint 9 (reporting) generates a PDF that summarizes the patient's safety state — that summary depends on the checklist's `RuleResult` shape being final.
