# Sprint 7 Summary — Toxicity Tracking

**Dates:** 2026-04-27 – 2026-04-28  
**Points delivered:** 11 pts (US-027: 3, US-028: 3, US-029: 2, US-030: 3)  
**Tests:** 636 passing — 0 regressions  
**Tag:** `v2-sprint7`

---

## What Was Built

### US-027 — Peripheral Neuropathy Tracking (3 pts)

Clinical rules layer (`src/clinical/neuropathy.py`):
- `effective_grade(sensory, motor, config)` — returns `max(sensory, motor)` when `use_higher_grade_for_action=True` (configurable)
- `recommended_action(grade, config)` — returns a `NeuropathyAction` with `dose_pct`, `action_code`, and advisory text per CTCAE v5

Database: `neuropathy_assessment` table (migration `0007`) with `sensory_grade` and `motor_grade` columns (both `CHECK 0–4`), `ctcae_version`, soft-delete via `deleted_at`.

Service (`src/services/neuropathy.py`): `create_neuropathy`, `update_neuropathy`, `delete_neuropathy` (soft), `list_neuropathy`, `latest_neuropathy` — every mutation writes an audit row.

UI:
- `NeuropathyDialog` / `EditNeuropathyDialog` — date, sensory G0–G4, motor G0–G4 radiobuttons, live advisory banner, notes
- `ToxicityPanel` neuropathy section — latest assessment with grade color-coded (G0/G1 green → G4 red), advisory text, "View history / + Add new" links
- `_NeuropathyHistoryWindow` — full list with Edit / Delete per row

Config additions:
```yaml
toxicity:
  neuropathy:
    grade_actions:
      0: { dose_pct: 100, action: continue }
      1: { dose_pct: 100, action: continue }
      2: { dose_pct: 100, action: monitor_closely }
      3: { dose_pct: 50,  action: hold_or_reduce }
      4: { dose_pct: 0,   action: discontinue }
    use_higher_grade_for_action: true
```

---

### US-028 — Infusion Reaction Logging (3 pts)

Clinical rules layer (`src/clinical/infusion_reactions.py`):
- `rechallenge_advice(grade, config)` — returns a `RechallengeAdvice` with `rechallenge` flag, `rate_pct`, `premed_enhance`, `switch_agent_to`, `hard_block`, and advisory text
- G1/G2: rechallenge at 50% rate with enhanced premedication
- G3: no rechallenge, consider agent switch
- G4: hard block (attending override required in cycle dialog)

Database: `infusion_reaction` table (migration `0008`) with `severity_grade` `CHECK 1–4`, `symptoms_json TEXT NOT NULL DEFAULT '[]'`, soft-delete.

Service (`src/services/infusion_reactions.py`): `create_reaction`, `update_reaction`, `delete_reaction`, `list_reactions`, `list_reactions_for_cycle`, `latest_reaction`.

UI:
- `InfusionReactionDialog` / `EditInfusionReactionDialog` — cycle dropdown, agent, onset_min, grade 1–4 with live rechallenge advisory (orange = rechallenge OK, red = hard block), symptom checkboxes from config vocab
- `ToxicityPanel` infusion reactions section with rechallenge advisory colored by `hard_block`
- `_ReactionHistoryWindow`

---

### US-029 — G-CSF Administration Tracking (2 pts)

Database: `gcsf_admin` table (migration `0009`) — `cycle_id` nullable (ad-hoc G-CSF allowed), `prophylaxis_type`, `dose_mg`.

Service (`src/services/gcsf.py`): standard CRUD + `gcsf_dates_for_patient(conn, patient_id, window_days)` which returns a flat list of all dates in `[admin_date, admin_date + window_days]` for each G-CSF record.

ANC trend chart (`src/views/components/anc_trend_chart.py`):
- Each ANC point within a G-CSF stimulation window is rendered with a triangle marker (`^`) in cyan (`#80DEEA`) instead of the default circle
- Legend appears when any G-CSF records exist

UI:
- `GcsfDialog` / `EditGcsfDialog` — admin date, agent dropdown (from config vocab), optional dose_mg, prophylaxis type radiobuttons, optional cycle link
- `ToxicityPanel` G-CSF section
- `_GcsfHistoryWindow`

Config additions:
```yaml
toxicity:
  gcsf:
    agent_vocab: [filgrastim, pegfilgrastim, lenograstim]
    stimulated_window_days: 7
```

---

### US-030 — Symptom Quick-Entry (3 pts)

Clinical rules layer (`src/clinical/symptoms.py`):
- `applicable_symptoms(phase, config)` — AC phase returns `set_all_phases`; T phase appends `set_t_phase_additional`
- `is_advisory(grade, config)` — `grade >= advisory_grade` (default 3)

Database: `symptom_entry` table (migration `0010`) — `grade CHECK 0–4`, `cycle_id` nullable.

Service (`src/services/symptoms.py`):
- `create_symptom`, `create_many` (batch — single transaction, one audit row per entry), `update_symptom`, `delete_symptom`, `list_symptoms`, `list_symptoms_for_cycle`, `latest_cycle_symptoms`

UI:
- `SymptomQuickEntryDialog` — modal dialog launched after a cycle saves; one row per applicable symptom (phase-adaptive: AC = 4, T = 6), grade G0–G4 via radiobuttons, advisory glyph (⚠) via variable trace, Skip button and Escape to dismiss
- `CycleCompletionDialog._prompt_symptom_entry` — yes/no prompt after successful cycle save; "No" skips silently, "Yes" opens the symptom dialog
- `ToxicityPanel` symptoms section — latest cycle's symptom grades in color-coded chips, "+ Add" from most recent completed cycle, "View history"
- `_SymptomHistoryWindow`

Config additions:
```yaml
toxicity:
  symptoms:
    set_all_phases: [nausea, fatigue, mucositis, constipation]
    set_t_phase_additional: [arthralgia, peripheral_edema]
    advisory_grade: 3
```

---

## New Files

| File | Purpose |
|------|---------|
| `src/clinical/neuropathy.py` | CTCAE v5 grade → action rules |
| `src/clinical/infusion_reactions.py` | Rechallenge advisory logic |
| `src/clinical/symptoms.py` | Phase-adaptive symptom set + advisory threshold |
| `src/services/neuropathy.py` | Neuropathy CRUD + audit |
| `src/services/infusion_reactions.py` | Reaction CRUD + audit |
| `src/services/gcsf.py` | G-CSF CRUD + stimulation window helper |
| `src/services/symptoms.py` | Symptom CRUD + batch insert + audit |
| `src/migrations/0007_neuropathy_assessment.py` | Schema migration |
| `src/migrations/0008_infusion_reaction.py` | Schema migration |
| `src/migrations/0009_gcsf_admin.py` | Schema migration |
| `src/migrations/0010_symptom_entry.py` | Schema migration |
| `src/views/dialogs/neuropathy_dialog.py` | Add / Edit dialog |
| `src/views/dialogs/infusion_reaction_dialog.py` | Add / Edit dialog |
| `src/views/dialogs/gcsf_dialog.py` | Add / Edit dialog |
| `src/views/dialogs/symptom_quick_entry_dialog.py` | Post-cycle quick-entry |
| `src/views/components/toxicity_panel.py` | Consolidated toxicity panel |
| `tests/test_clinical_neuropathy.py` | 13 tests |
| `tests/test_neuropathy_service.py` | 26 tests |
| `tests/test_clinical_infusion_reactions.py` | 11 tests |
| `tests/test_infusion_reaction_service.py` | 23 tests |
| `tests/test_gcsf_service.py` | 27 tests |
| `tests/test_clinical_symptoms.py` | 13 tests |
| `tests/test_symptoms_service.py` | 27 tests |
| `tests/test_toxicity_panel.py` | 23 tests |

---

## Audit Actions Added

```
neuropathy_created / neuropathy_updated / neuropathy_deleted
reaction_created   / reaction_updated   / reaction_deleted
gcsf_created       / gcsf_updated       / gcsf_deleted
symptom_created    / symptom_updated    / symptom_deleted
```

All 12 actions registered in `services/audit.ACTIONS`.

---

## Design Decisions

**Config-driven everywhere.** Symptom names, grade thresholds, rechallenge rules, G-CSF agent vocab, and neuropathy action mappings all live in `institution.defaults.yaml`. No clinical values are hardcoded in Python.

**Soft-delete pattern consistent.** All four new tables follow the same `deleted_at TIMESTAMP` convention used throughout the project.

**Symptom prompt is skippable.** The cycle-completion flow offers the symptom dialog as an opt-in step (`messagebox.askyesno`). Skipping records nothing — no empty rows, no audit noise.

**G-CSF stimulation window computed at query time.** `gcsf_dates_for_patient` expands each administration into a date range using `window_days` from config. The ANC chart calls this once per render and does O(1) per-point lookup.

**Phase detection is positional.** Cycles 1–4 = AC, 5–8 = T. Used in both `CycleCompletionDialog` and `SymptomQuickEntryDialog`.
