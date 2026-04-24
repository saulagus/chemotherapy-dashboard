# Sprint 6 Plan — Cardiotoxicity Safety

**V2 · Weeks 15–16 · Days 11–20 of V2**

---

## Sprint Goal

Every AC cycle records the patient's height, weight, BSA, and the anthracycline dose actually delivered in mg/m². The cumulative anthracycline dose (doxorubicin-equivalent) is calculated on every cycle write. LVEF assessments are captured with timestamp and modality. A cardiotoxicity risk badge on the dashboard shows **green / yellow / red / hard-stop** state, and the cycle-completion flow soft-blocks at red and hard-blocks at the configured cumulative limit — with overrides audited and attributed.

**The nurse should never be able to silently administer a dose that pushes the patient past 400 mg/m² doxorubicin-equivalent without a deliberate, recorded override.**

---

## Stories

| Story | Title | Points | Status |
|-------|-------|--------|--------|
| US-023 | BSA / height / weight per cycle (+ mini dose calculator) | 3 | To Do |
| US-024 | Cumulative anthracycline dose calculation | 3 | To Do |
| US-025 | LVEF / cardiac assessment tracking | 2 | To Do |
| US-026 | Cardiotoxicity risk badge + cumulative-dose warning | 3 | To Do |

**Total: 11 story points · 10 development days**

---

## Sequencing

```
US-023 ──► US-024 ──► US-026
                ▲
              US-025  (parallel to US-024)
```

- **US-023 first** — everything downstream needs BSA per cycle. No cumulative math without `dose_mg_per_m2` on `cycle`.
- **US-024 gates US-026** — the badge reads the cumulative total; the service must own the math before the UI surfaces it.
- **US-025 can run parallel to US-024** — different table, different panel, no data dependency.
- **US-026 last** — consumes US-023 + US-024 + US-025 outputs into a single visual and into the cycle-completion rule.

---

## Dependencies (must be done)

| From Sprint | Artifact | Why Sprint 6 needs it |
|-------------|----------|-----------------------|
| Sprint 5 | Migration framework (US-017) | US-023, US-024, US-025 each ship a migration |
| Sprint 5 | Institution config layer (US-017a) | Thresholds, BSA formula, equivalence factors all read from YAML |
| Sprint 5 | Audit log (US-018) | Override-and-reason writes flow through `audit.record(...)` |
| Sprint 5 | Edit-cycle dialog (US-020) | BSA fields extend this dialog; do not fork a new one |
| V1 | CycleService | Extended, not rewritten, to compute dose on save |

If the config layer is not wired to the cycle-completion path, **stop and fix it before touching Sprint 6 stories** — every story in this sprint reads thresholds from config.

---

## Pre-Sprint: Specialist YAML Review (Day 11 morning)

Before any code lands, resolve the four patient-safety-critical questions flagged in the V2 plan:

| Question | Default | Decision | Source |
|----------|---------|----------|--------|
| Doxorubicin cumulative thresholds (yellow / red / hard-stop) | 300 / 400 / 450 mg/m² | ☐ Accept · ☐ Override | |
| Anthracycline equivalence factors | dox 1.0 · epi 0.5 · dauno 0.5 · ida 5.0 · mito 4.0 | ☐ Accept · ☐ Override | |
| LVEF hold thresholds (absolute · delta) | <50% absolute · drop ≥10 AND <55% | ☐ Accept · ☐ Override | |
| LVEF modality preference | Echo default; MUGA allowed | ☐ Accept · ☐ Override | |
| BSA formula | Mosteller | ☐ Accept · ☐ Override (DuBois) | |

Deliverable: one YAML diff against `config/institution.defaults.yaml`, committed the same morning. If specialists are not reachable, ship defaults and file a note in `PROJECT_LOG.md` — do not block the sprint.

---

## Architecture Additions

Sprint 6 introduces the `clinical/` package. Start it with **one file, three pure functions, one test file** — no premature framework.

```
src/
├── clinical/
│   ├── __init__.py
│   └── cardiotoxicity.py       ← pure functions, no DB, no Tk
├── services/
│   ├── cycles.py               ← extended: compute + persist dose_mg_per_m2
│   └── lvef.py                 ← NEW (US-025)
├── migrations/
│   ├── 0004_cycle_bsa_dose.py
│   ├── 0005_lvef_assessments.py
│   └── 0006_patient_prior_anthracycline.py
└── views/
    ├── dialogs/
    │   ├── edit_cycle_dialog.py    ← extend with BSA/dose fields
    │   └── lvef_dialog.py          ← NEW
    └── components/
        └── cardiotoxicity_panel.py ← NEW — badge + cumulative meter
tests/
├── test_clinical_cardiotoxicity.py
├── test_cycle_dose_calc.py
├── test_lvef_service.py
└── test_cardiotoxicity_panel.py
```

**Rule:** nothing in `clinical/` reads the database, touches Tk, or imports from `services/`. It takes primitives in, returns primitives out. That is what makes the rules engine testable.

---

## Schema Migrations

### 0004 — `cycle` BSA and delivered-dose fields
```sql
ALTER TABLE cycle ADD COLUMN height_cm REAL;
ALTER TABLE cycle ADD COLUMN weight_kg REAL;
ALTER TABLE cycle ADD COLUMN bsa_m2 REAL;               -- computed from height/weight at save
ALTER TABLE cycle ADD COLUMN anthracycline_agent TEXT;  -- 'doxorubicin' | 'epirubicin' | ...
ALTER TABLE cycle ADD COLUMN dose_mg_total REAL;        -- what the nurse dispensed
ALTER TABLE cycle ADD COLUMN dose_mg_per_m2 REAL;       -- computed: total / bsa
```

### 0005 — `lvef_assessment` table
```sql
CREATE TABLE lvef_assessment (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  patient_id TEXT NOT NULL REFERENCES patient(id),
  assessment_date DATE NOT NULL,
  lvef_percent REAL NOT NULL,
  modality TEXT NOT NULL,        -- 'echo' | 'muga'
  context TEXT,                  -- 'baseline' | 'end_of_ac' | 'ad_hoc'
  notes TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  deleted_at TIMESTAMP
);
CREATE INDEX idx_lvef_patient_date ON lvef_assessment(patient_id, assessment_date);
```

### 0006 — patient prior-anthracycline exposure
```sql
ALTER TABLE patient ADD COLUMN prior_anthracycline_dose_mg_per_m2 REAL DEFAULT 0;
ALTER TABLE patient ADD COLUMN prior_anthracycline_agent TEXT;
```

**Each migration must ship with:**
- `up(conn)` and `down(conn)` functions
- Backup taken before migration applies (already handled by US-017 runner)
- A fixture test that applies all migrations against a V1 DB snapshot without error

---

## Config Additions (`config/institution.defaults.yaml`)

```yaml
cardiotoxicity:
  bsa_formula: mosteller           # mosteller | dubois
  weight_change_warning_pct: 10

  cumulative_thresholds_mg_per_m2:
    yellow: 300
    red: 400
    hard_stop: 450

  equivalence_factors:             # relative to doxorubicin (1.0)
    doxorubicin: 1.0
    epirubicin: 0.5
    daunorubicin: 0.5
    idarubicin: 5.0
    mitoxantrone: 4.0

  lvef:
    absolute_hold_pct: 50
    delta_hold_pct: 10
    delta_hold_absolute_ceiling_pct: 55
    review_flag_delta_pct: 16

  blocking_modes:
    cumulative_yellow: advisory
    cumulative_red: soft_block
    cumulative_hard_stop: hard_block
    lvef_absolute: soft_block
    lvef_delta: soft_block
```

These values are consumed by `clinical.cardiotoxicity` — no magic numbers in code.

---

## Day-by-Day Plan

### DAY 11 — Sprint planning, specialist review, skeleton
**Morning (~2h)** — Specialist review of YAML defaults; write config diff; commit `config/institution.yaml` with any overrides (or note defaults accepted).
**Afternoon (~3h)** — Create `src/clinical/__init__.py`, `src/clinical/cardiotoxicity.py` skeleton with signatures (`compute_bsa`, `to_doxorubicin_equivalent`, `cumulative_status`, `lvef_status`). Create empty `test_clinical_cardiotoxicity.py`. Run migrations 0004/0005/0006 scaffolds (empty `up`/`down`) locally, confirm runner picks them up.
**Commit:** `Added Sprint 6 cardiotoxicity module scaffolding`

### DAY 12 — US-023 part 1: BSA migration + pure function
- Implement `0004_cycle_bsa_dose.py` up/down.
- Implement `compute_bsa(height_cm, weight_kg, formula)` for Mosteller and DuBois.
- Unit tests: known reference values (1.70 m, 65 kg → 1.76 m² Mosteller). Edge cases: negative, zero, missing → raise `ValueError`.
- Extend `CycleService.save_cycle(...)`: if height + weight present, compute BSA and `dose_mg_per_m2` on write in the same transaction as the cycle row.
**Commit:** `Added BSA calculation and cycle dose fields`

### DAY 13 — US-023 part 2: edit-cycle dialog fields + mini calculator
- Add Height, Weight, Anthracycline agent (dropdown from config keys), Dose (mg total) inputs to the existing edit-cycle dialog.
- Live-compute BSA and mg/m² as the user types; show below the inputs as read-only text (not a separate dialog — inline is less clicks).
- Prefill height/weight from prior cycle on this patient; warn visually if weight changes >10% from prior measurement (read `weight_change_warning_pct` from config).
- Tests: dialog validation; service writes persist height/weight/bsa/dose fields.
**Commit:** `Added height, weight, and dose fields to cycle entry`
**US-023 DONE — 3 pts**

### DAY 14 — US-024 part 1: equivalence + cumulative math
- Implement `to_doxorubicin_equivalent(agent, dose_mg_per_m2, factors)` — pure, reads factors dict, unknown agent raises.
- Implement `cumulative_doxorubicin_equivalent(cycles, factors, prior_exposure_mg_per_m2)` — sums across cycles, adds prior exposure, excludes soft-deleted rows.
- Extensive unit tests: mixed-agent patients, empty cycle list, prior exposure only, soft-deleted rows excluded.
- Add `prior_anthracycline_dose_mg_per_m2` + `prior_anthracycline_agent` to Edit Patient dialog (US-019 artifact). Both optional, default 0 / null.
**Commit:** `Added cumulative anthracycline dose calculation`

### DAY 15 — US-024 part 2: service surface + US-025 start
- `CycleService.cumulative_dose(patient_id) -> CumulativeSummary` (dataclass: `total_mg_per_m2`, `agent_breakdown`, `status`). Called on every dashboard refresh for the current patient.
- Integration test against fixture patient: add 4 AC cycles at 60 mg/m² dox → expect 240 mg/m² → yellow.
- Start US-025: migration 0005, `services/lvef.py` (add / edit / delete / list, with audit trail), LVEF dataclass.
**Commit:** `Added cumulative-dose service and LVEF service skeleton`

### DAY 16 — US-025 finish: LVEF dialog + panel row
- `lvef_dialog.py`: date, %, modality (echo/muga), context (baseline/end_of_ac/ad_hoc), notes.
- LVEF history row in dashboard: "LVEF: 62% (echo, 2026-03-12) — baseline 65%, Δ −3" with the Δ colored per config rules.
- `lvef_status(current_pct, baseline_pct, config) -> {"ok"|"review"|"hold", reason}` pure function.
- Unit + integration tests; edit and delete flow writes audit entries.
**Commit:** `Added LVEF tracking and cardiac assessment history`
**US-025 DONE — 2 pts**

### DAY 17 — US-024 finish + US-026 start
- Finalize US-024: wire cumulative summary into dashboard data layer (not UI yet); confirm <5ms for a patient with 8 cycles.
- Performance test added to `test_performance.py`.
**US-024 DONE — 3 pts**
- Begin US-026: new `cardiotoxicity_panel.py` component. Badge + cumulative meter (bar showing current / hard_stop with yellow/red ticks at thresholds).
- `cumulative_status(total, config) -> {"green"|"yellow"|"red"|"hard_stop"}` pure function.
**Commit:** `Added cumulative dose service wiring`

### DAY 18 — US-026 part 2: visual + integration
- Badge states visible in the patient list (next to name) AND in the dashboard header.
  - Green <300 · Yellow 300–399 · Red 400–449 · Hard-stop ≥450 — all from config.
- Tooltip on hover: "284 mg/m² doxorubicin-equivalent · 16 mg/m² remaining before yellow".
- Hook into cycle-completion flow:
  - **Red** → confirmation dialog: "This cycle would bring cumulative to 412 mg/m². Proceed?" with reason text field; writes `audit.record(action='override_red', reason=...)` on confirm.
  - **Hard-stop** → dialog blocks completion, offers "Attending override"; requires reason, writes `audit.record(action='override_hard_stop', reason=...)`.
- Per-rule blocking mode read from config — a site can switch red to `advisory` or hard-stop to `soft_block`.
**Commit:** `Added cardiotoxicity risk badge and threshold warnings`

### DAY 19 — US-026 part 3: LVEF in panel, polish, integration tests
- Extend cardiotoxicity panel with LVEF row (latest %, Δ from baseline, status).
- Soft-block cycle completion when `lvef_status != "ok"` (config blocking mode respected).
- End-to-end test: fresh patient → 5 AC cycles → badge green → yellow → red → override path → audit row visible in US-022 viewer.
- Regression sweep: existing cycle and lab tests all pass; no Sprint 5 test broken.
**Commit:** `Added LVEF integration into cardiotoxicity panel`
**US-026 DONE — 3 pts**

### DAY 20 — Demo, retro, summary
- Load demo patient near 280 mg/m²; walk: add weight → add cycle → see badge tick to yellow → add one more cycle → red + override dialog → reason audited.
- Walk LVEF drop: 65% → 52% → soft-block with reason.
- Write `docs/SPRINT_6_SUMMARY.md` in the shape of Sprint 3's summary (points delivered, bugs fixed, lessons, carry-over if any).
- Update `docs/PROJECT_LOG.md` with Sprint 6 close-out entry.
- Tag `v2-sprint6`.
**Commit:** `Added Sprint 6 summary and close-out`

---

## Story Acceptance Criteria

### US-023 — BSA / height / weight per cycle (3 pts)
- [ ] Height, weight, agent, dose-mg inputs present on edit-cycle dialog
- [ ] BSA + mg/m² computed live as user types (inline, not a separate dialog)
- [ ] Mosteller and DuBois both supported; formula selected via config
- [ ] Prefill from prior cycle when available
- [ ] Weight-change warning fires at >10% change from prior measurement
- [ ] Values persist: `height_cm`, `weight_kg`, `bsa_m2`, `anthracycline_agent`, `dose_mg_total`, `dose_mg_per_m2`
- [ ] All writes flow through CycleService; audit unchanged
- [ ] Unit tests for Mosteller and DuBois against reference values

### US-024 — Cumulative anthracycline dose (3 pts)
- [ ] `to_doxorubicin_equivalent` pure function covers all five configured agents
- [ ] `cumulative_doxorubicin_equivalent` sums across cycles + prior exposure
- [ ] Soft-deleted cycles excluded from total
- [ ] Prior-anthracycline fields present on Edit Patient dialog; default 0
- [ ] `CycleService.cumulative_dose(patient_id)` returns breakdown per agent + total + status
- [ ] Performance: cumulative calc <5 ms for 8-cycle patient
- [ ] Integration test: 4 cycles × 60 mg/m² dox → 240 mg/m² → green

### US-025 — LVEF / cardiac assessment (2 pts)
- [ ] LVEF entries: date, %, modality (echo/muga), context, notes
- [ ] Add, edit, soft-delete supported
- [ ] Audit entries on every write (action `lvef_created`, `lvef_updated`, `lvef_deleted`)
- [ ] History visible in dashboard cardiotoxicity panel (latest + Δ from baseline)
- [ ] `lvef_status` pure function returns ok / review / hold per config thresholds

### US-026 — Risk badge + cumulative warning (3 pts)
- [ ] Badge visible on patient list row and dashboard header
- [ ] States: green / yellow / red / hard-stop — thresholds from config
- [ ] Tooltip shows current mg/m² and headroom to next threshold
- [ ] Red state soft-blocks cycle completion with reason dialog → audit
- [ ] Hard-stop state hard-blocks with attending-override path → audit
- [ ] LVEF abnormal state soft-blocks cycle completion with reason → audit
- [ ] Per-rule blocking mode honored from config (`advisory` | `soft_block` | `hard_block`)
- [ ] All override reasons appear in US-022 audit viewer

---

## Success Criteria (sprint-level)

- [ ] All four stories merged to master, tagged `v2-sprint6`
- [ ] Coverage on `src/clinical/` ≥90%
- [ ] Coverage on `src/services/lvef.py` ≥85%
- [ ] No regressions in Sprint 5 test suite
- [ ] Dashboard load with cardiotoxicity panel + cumulative calc <200 ms at P95 on demo DB
- [ ] Demo walkthrough (Day 20) completes green → yellow → red override → hard-stop block → LVEF block without manual DB poking
- [ ] Zero magic-number thresholds in code — every threshold resolved via config loader

---

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Specialist YAML review slips past Day 11 | Medium | Ship defaults; note in PROJECT_LOG; specialist overrides are a one-line YAML change |
| Mosteller vs DuBois disagreement >5% misleads nurse | Low | Tests against published reference values; formula source shown in tooltip |
| Override dialog friction pushes nurses to "always override" | Medium | Require ≥20-char reason; surface override rate in Sprint 10 polish pass |
| Hard-stop blocks a clinically valid cycle | Low | Every institution can downgrade `cumulative_hard_stop` to `soft_block` via config |
| US-026 scope creeps with more badges / more rules | High | Explicitly OUT: cyclophosphamide cumulative (V3), AC-TH (V3), pediatric-adjusted thresholds (V3) |
| `clinical/` module grows into a framework | Medium | Rule: one file until there are 3 rule types; no base class, no registry |

---

## Out of Scope (reject on sight)

- Cyclophosphamide cumulative tracking → V3
- AC-TH / trastuzumab cardiotoxicity combined rule → V3
- Troponin / BNP biomarker tracking → V3
- Pediatric BSA-adjusted thresholds → V3
- Custom threshold per patient (vs per institution) → V3
- Graphing LVEF trend over time → V2 Sprint 9 (belongs in reporting)
- Automatic LVEF pull from PACS / echo reports → V3 (EHR integration)

If a request surfaces mid-sprint from any of the above, log it to `docs/BACKLOG_V3.md` and move on.

---

## Definition of Done (per story)

1. Code committed with single-line `Added ...` message
2. Migration up+down tested against a V1 DB snapshot
3. Unit tests on pure functions + integration test on service surface
4. Config values read from YAML, not hardcoded
5. Audit entries written for every override and every mutation
6. Dialog / panel rendered cleanly at 1920×1080 and 1024×768
7. No regression in the Sprint 5 test suite
8. Entry in `PROJECT_LOG.md` for the day

---

## Post-Sprint Carry-Over Protocol

If any story is incomplete at end of Day 20:
- **US-023 incomplete** → Sprint halts. Everything downstream depends on BSA. Extend Sprint 6 by 2 days rather than carrying.
- **US-024 incomplete** → carry into Sprint 7 Day 1; US-026 follows; push one toxicity story to Sprint 8.
- **US-025 incomplete** → carry into Sprint 7 Day 1 (low coupling).
- **US-026 incomplete** → carry into Sprint 7; Sprint 7 toxicity stories absorb the slip since they're independent.

Do not start Sprint 7 stories with Sprint 6 carry-over still open. The pre-cycle checklist in Sprint 8 reads everything Sprint 6 ships; partial Sprint 6 means a partial checklist.
