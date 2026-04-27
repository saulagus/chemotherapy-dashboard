# Sprint 6 Summary — Cardiotoxicity Safety

**V2 · Weeks 15–16 · Days 11–20**
**Points delivered: 11 / 11**
**Tests: 473 passing · 0 regressions**

---

## Stories Delivered

| Story | Title | Points | Status |
|-------|-------|--------|--------|
| US-023 | BSA / height / weight per cycle (+ mini dose calculator) | 3 | ✅ Done |
| US-024 | Cumulative anthracycline dose calculation | 3 | ✅ Done |
| US-025 | LVEF / cardiac assessment tracking | 2 | ✅ Done |
| US-026 | Cardiotoxicity risk badge + cumulative-dose warning | 3 | ✅ Done |

---

## What Was Built

### US-023 — BSA / height / weight per cycle
- Height, weight, anthracycline agent, and dose-mg fields added to the cycle-completion dialog
- Live BSA + mg/m² calculator updates as the user types (Mosteller formula, DuBois available via config)
- Values persisted to `cycle` table: `height_cm`, `weight_kg`, `bsa_m2`, `anthracycline_agent`, `dose_mg_total`, `dose_mg_per_m2`
- Pre-fill from the most recent prior cycle for height/weight; visual warning when weight changes >10% from prior measurement
- Migration `0004_cycle_bsa_dose.py` ships `up()` and `down()`

### US-024 — Cumulative anthracycline dose calculation
- `clinical/cardiotoxicity.py`: `to_doxorubicin_equivalent()`, `cumulative_doxorubicin_equivalent()`, `cumulative_status()` — all pure functions, zero DB/Tk dependencies
- `services/cycles.py`: `cumulative_dose(conn, patient_id) → CumulativeSummary` (total_mg_per_m2, agent_breakdown, status)
- Prior-anthracycline exposure field on patient demographics (migration `0006_patient_prior_anthracycline.py`)
- Soft-deleted cycles excluded from total; mixed-agent patients supported via equivalence factors from config
- Performance: <5 ms for 8-cycle patient (verified in `test_performance.py`)

### US-025 — LVEF / cardiac assessment tracking
- Migration `0005_lvef_assessments.py`; `LvefAssessment` dataclass
- `services/lvef.py`: `create_lvef`, `update_lvef`, `delete_lvef` (soft), `list_lvef`, `get_baseline_lvef` — all audit-trailed
- `lvef_dialog.py` and `EditLvefDialog` for add/edit flows
- `clinical/cardiotoxicity.py`: `lvef_status(current, baseline, config) → {status, reason}` — absolute hold (<50%), delta hold (≥10pp AND <55%), review flag (≥16pp)
- Cardiotoxicity panel shows: latest LVEF %, modality, date, status badge, Δ from baseline, full assessment history with edit/delete
- Audit actions: `lvef_created`, `lvef_updated`, `lvef_deleted`

### US-026 — Risk badge + cumulative-dose warning
- **Cardiotoxicity panel**: cumulative dose value + badge (`[ADVISORY]` / `[HOLD]` / `[HARD STOP]`) + responsive Canvas meter with zone tints and threshold tick marks
- **Patient list**: "Dose Risk" column (7th column, 90 px) — per-patient `cumulative_dose()` on load; motion-based tooltip showing exact mg/m² and headroom; hover tag preservation
- **Dashboard header**: colored badge (● Green / ⚠ Yellow / ⛔ Red / ⛔ STOP) next to patient name; refreshes after every cycle save via `on_cycle_save` callback hook on `TimelineComponent`
- **Cycle-completion blocking** (prospective check before save):
  - Cumulative red + soft_block → red confirmation dialog, requires non-empty reason, logs `override_red`
  - Cumulative hard_stop + hard_block → purple attending-override dialog, requires ≥20-char reason, logs `override_hard_stop`
  - LVEF hold + soft_block → LVEF confirmation dialog (AC cycles only), requires non-empty reason, logs `override_lvef`
  - All blocking modes read from config — any rule can be downgraded to `advisory`
- Edit path: old cycle's dox-equiv subtracted before computing prospective total (no double-count)

---

## Tests Added This Sprint

| File | New Tests | Description |
|------|-----------|-------------|
| `test_clinical_cardiotoxicity.py` | +8 | `cumulative_status` boundary tests |
| `test_cycle_service.py` | +7 | `cumulative_dose` service tests |
| `test_cardiotoxicity_panel.py` | 13 | Panel rendering at all status levels |
| `test_cycle_blocking.py` | 24 | Audit actions, prospective math, all blocking paths + LVEF paths |
| `test_e2e_integration.py` | +11 | Phase 9 cardiotoxicity walkthrough |

**Total: 473 tests (214 V1 baseline + 259 V2 additions to date)**

---

## Architectural Decisions

- **`clinical/` module rule**: zero DB/Tk imports — pure functions in, primitives out. Maintained throughout sprint; all rules are independently unit-testable.
- **Blocking mode per-rule**: every safety gate reads its mode from `config.blocking_modes`. Sites can downgrade any rule to `advisory` without code changes.
- **Prospective dose on edit**: subtract old cycle's stored `dose_mg_per_m2` before adding new value. Avoids re-computing BSA and eliminates double-count on edits.
- **Treeview multi-tag foreground**: dose_tag listed first in the tag tuple so its `foreground` property takes priority over the stripe `background`. The only way to get per-column color in Tkinter's Treeview without a custom widget.
- **Override audit after save**: override rows written after the clinical save succeeds so a DB failure on the audit write doesn't block a valid clinical entry (logged, not re-raised).
- **LVEF block AC-only**: consistent with pre-cycle checklist design (Sprint 8). T-phase cycles skip the LVEF gate at the `_on_save()` level.

---

## Bugs Fixed

- `saved_id` for new cycles was always `None` in override audit rows. Fixed by capturing the return value of `create_cycle()` as `saved_cycle`.

---

## Carry-Over

None. All 11 story points delivered. Sprint 7 (Toxicity Tracking) can start immediately.

---

## Sprint 7 Preview

- **US-027** Peripheral neuropathy CTCAE grading (sensory + motor, grades 0–4)
- **US-028** Infusion hypersensitivity reaction log
- **US-029** G-CSF administration log (with ANC chart marker)
- **US-030** Symptom quick-entry (nausea, fatigue, mucositis, constipation; T-phase adds arthralgia + peripheral edema)
