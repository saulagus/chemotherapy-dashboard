# Sprint 7 Plan — Toxicity Tracking

**V2 · Weeks 17–18 · Days 21–30 of V2**

---

## Sprint Goal

The clinical picture expands beyond labs and cardiotoxicity. By end of sprint, every patient record captures **peripheral neuropathy (CTCAE v5 sensory + motor)**, **infusion hypersensitivity reactions with rechallenge guidance**, **G-CSF administrations (visible on the ANC trend chart)**, and **per-cycle symptom quick-entry**. Each toxicity surface lands as an independent panel row, each rule lives as a pure function in `clinical/`, and every data point is positioned so that Sprint 8's pre-cycle checklist can read it without further plumbing.

**By Day 30 the nurse can grade neuropathy, log a reaction, mark a G-CSF dose, and capture symptoms in under 60 seconds per cycle — and Sprint 8 inherits a complete toxicity dataset.**

---

## Stories

| Story | Title | Points | Status |
|-------|-------|--------|--------|
| US-027 | Peripheral neuropathy CTCAE grading | 3 | To Do |
| US-028 | Infusion hypersensitivity reaction log | 3 | To Do |
| US-029 | Growth factor (G-CSF) administration log | 2 | To Do |
| US-030 | Symptom quick-entry | 3 | To Do |

**Total: 11 story points · 10 development days**

---

## Sequencing

```
US-027 ─┐
US-028 ─┤── all largely independent; integrate in toxicity panel on Day 29
US-029 ─┤
US-030 ─┘
```

The V2 plan flagged Sprint 7 as "all largely independent; any order." Build order chosen for risk reduction — neuropathy first because its grade→action mapping is the most clinically loaded; symptom quick-entry last because its scope is the easiest to trim if the sprint runs hot.

---

## Dependencies (must be done)

| From | Artifact | Why Sprint 7 needs it |
|------|----------|-----------------------|
| Sprint 5 | Migration framework (US-017) | Every story ships a migration |
| Sprint 5 | Institution config layer (US-017a) | Grade→action map, symptom set, rechallenge policy, CTCAE version all read from YAML |
| Sprint 5 | Audit log (US-018) | Every toxicity create/edit/delete writes an audit row |
| Sprint 5 | Soft-delete pattern (US-020/021) | All four new tables follow `deleted_at` soft-delete |
| Sprint 6 | `clinical/` package + pure-function rule | Pattern established; extend, do not redesign |
| V1 | ANC trend chart (`anc_trend_chart.py`) | US-029 adds G-CSF marker glyphs to the existing chart, not a new chart |
| V1 | Cycle entry dialog | Symptom quick-entry hangs off cycle save, not a separate workflow |

If any of the above is missing, **fix it before touching Sprint 7 stories** — Sprint 7 has no novel infrastructure; it stands on Sprint 5 + 6.

---

## Pre-Sprint: Specialist YAML Review (Day 21 morning)

The four V2-plan questions flagged for Sprint 7. Resolve them on Day 21 or ship defaults and note overrides in `PROJECT_LOG.md`.

| Question | Default | Decision | Source |
|----------|---------|----------|--------|
| Neuropathy grade → action mapping | G2 hold + resume −20%; G3 hold + −25%, discontinue on recurrence; G4 discontinue | ☐ Accept · ☐ Override | |
| Infusion reaction rechallenge policy | G1 slow 50%; G2 stop+restart 50%; G3 do not rechallenge; G4 hard-block | ☐ Accept · ☐ Override | |
| CTCAE version | 5.0 | ☐ Accept · ☐ 4.03 | |
| Symptom set (all-phase + T-phase additions) | nausea, fatigue, mucositis, constipation + arthralgia, peripheral_edema | ☐ Accept · ☐ Override | |
| G-CSF agent vocabulary | pegfilgrastim, filgrastim, lipegfilgrastim | ☐ Accept · ☐ Override | |
| G-CSF policy (dose-dense vs standard) | dose-dense AC = primary every cycle; standard AC = secondary unless FN risk | ☐ Accept · ☐ Override | |

Deliverable: one YAML diff against `config/institution.defaults.yaml` committed Day 21.

---

## Architecture Additions

Sprint 7 extends the established `clinical/` + `services/` + `views/` layering. **No new package.** Three rule modules under `clinical/`, four services, four dialogs, one merged toxicity panel.

```
src/
├── clinical/
│   ├── neuropathy.py            ← NEW — grade math + grade→action mapping
│   ├── infusion_reactions.py    ← NEW — rechallenge advisory
│   └── symptoms.py              ← NEW — severity classification + advisory thresholds
├── services/
│   ├── neuropathy.py            ← NEW
│   ├── infusion_reactions.py    ← NEW
│   ├── gcsf.py                  ← NEW
│   └── symptoms.py              ← NEW
├── migrations/
│   ├── 0007_neuropathy_assessment.py
│   ├── 0008_infusion_reaction.py
│   ├── 0009_gcsf_admin.py
│   └── 0010_symptom_entry.py
└── views/
    ├── dialogs/
    │   ├── neuropathy_dialog.py
    │   ├── infusion_reaction_dialog.py
    │   ├── gcsf_dialog.py
    │   └── symptom_quick_entry_dialog.py
    └── components/
        ├── toxicity_panel.py            ← NEW — combined neuropathy + reactions + symptoms
        └── anc_trend_chart.py           ← extend with G-CSF marker glyph
tests/
├── test_clinical_neuropathy.py
├── test_clinical_infusion_reactions.py
├── test_clinical_symptoms.py
├── test_neuropathy_service.py
├── test_infusion_reaction_service.py
├── test_gcsf_service.py
├── test_symptoms_service.py
└── test_toxicity_panel.py
```

**Rules carried forward from Sprint 6:**
- `clinical/` modules import nothing from `services/`, `views/`, or `sqlite3`. Primitives in, primitives out.
- All thresholds and vocabularies via config.
- Audit row written in the same transaction as the mutation in every service.
- Dialogs extend the existing edit-dialog pattern; no new dialog framework.

---

## Schema Migrations

### 0007 — `neuropathy_assessment` table
```sql
CREATE TABLE neuropathy_assessment (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  patient_id TEXT NOT NULL REFERENCES patient(id),
  cycle_id INTEGER REFERENCES cycle(id),         -- nullable: assessment can be ad-hoc
  assessment_date DATE NOT NULL,
  sensory_grade INTEGER NOT NULL CHECK (sensory_grade BETWEEN 0 AND 4),
  motor_grade INTEGER NOT NULL CHECK (motor_grade BETWEEN 0 AND 4),
  ctcae_version TEXT NOT NULL DEFAULT '5.0',
  notes TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  deleted_at TIMESTAMP
);
CREATE INDEX idx_neuropathy_patient_date ON neuropathy_assessment(patient_id, assessment_date);
```

### 0008 — `infusion_reaction` table
```sql
CREATE TABLE infusion_reaction (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  patient_id TEXT NOT NULL REFERENCES patient(id),
  cycle_id INTEGER NOT NULL REFERENCES cycle(id),
  agent TEXT NOT NULL,                           -- 'paclitaxel' | 'doxorubicin' | ...
  onset_min INTEGER NOT NULL,                    -- minutes from infusion start
  severity_grade INTEGER NOT NULL CHECK (severity_grade BETWEEN 1 AND 4),
  symptoms_json TEXT NOT NULL DEFAULT '[]',      -- JSON array of strings (vocab in config)
  response TEXT,                                 -- free text: meds given, action taken
  rechallenge_outcome TEXT,                      -- 'tolerated' | 'recurred' | 'switched_agent' | null
  notes TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  deleted_at TIMESTAMP
);
CREATE INDEX idx_reaction_patient_cycle ON infusion_reaction(patient_id, cycle_id);
```

### 0009 — `gcsf_admin` table
```sql
CREATE TABLE gcsf_admin (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  patient_id TEXT NOT NULL REFERENCES patient(id),
  cycle_id INTEGER REFERENCES cycle(id),         -- nullable: ad-hoc support possible
  agent TEXT NOT NULL,                           -- 'pegfilgrastim' | 'filgrastim' | ...
  admin_date DATE NOT NULL,
  dose_mg REAL,
  prophylaxis_type TEXT,                         -- 'primary' | 'secondary' | 'therapeutic'
  notes TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  deleted_at TIMESTAMP
);
CREATE INDEX idx_gcsf_patient_date ON gcsf_admin(patient_id, admin_date);
```

### 0010 — `symptom_entry` table
```sql
CREATE TABLE symptom_entry (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  patient_id TEXT NOT NULL REFERENCES patient(id),
  cycle_id INTEGER REFERENCES cycle(id),
  entry_date DATE NOT NULL,
  symptom TEXT NOT NULL,                         -- vocab from config
  grade INTEGER NOT NULL CHECK (grade BETWEEN 0 AND 4),
  notes TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  deleted_at TIMESTAMP
);
CREATE INDEX idx_symptom_patient_cycle ON symptom_entry(patient_id, cycle_id);
```

**Each migration must ship with `up(conn)` and `down(conn)`, applied through the existing runner, with a fixture test that rolls forward and back without error against a Sprint-6-tagged DB snapshot.**

---

## Config Additions (`config/institution.defaults.yaml`)

```yaml
toxicity:
  ctcae_version: "5.0"

  neuropathy:
    grade_actions:
      0: { dose_pct: 100, action: continue }
      1: { dose_pct: 100, action: continue }
      2: { dose_pct: 80,  action: hold_one_cycle_then_resume }
      3: { dose_pct: 75,  action: hold_until_recovered_then_resume_discontinue_on_recurrence }
      4: { dose_pct: 0,   action: discontinue_permanently }
    # When sensory and motor differ, use the higher of the two grades for action lookup.
    use_higher_grade_for_action: true

  infusion_reactions:
    symptom_vocab:
      - flushing
      - urticaria
      - hypotension
      - hypertension
      - dyspnea
      - bronchospasm
      - back_pain
      - chest_pain
      - anaphylaxis
    rechallenge_policy:
      1: { rechallenge: true,  rate_pct: 50, premed_enhance: false }
      2: { rechallenge: true,  rate_pct: 50, premed_enhance: true }
      3: { rechallenge: false, switch_agent_to: nab_paclitaxel_or_docetaxel }
      4: { rechallenge: false, switch_agent_to: nab_paclitaxel_or_docetaxel, hard_block: true }

  gcsf:
    agent_vocab: [pegfilgrastim, filgrastim, lipegfilgrastim]
    policy:
      dose_dense_q2w: primary
      standard_q3w: secondary

  symptoms:
    set_all_phases: [nausea, fatigue, mucositis, constipation]
    set_t_phase_additional: [arthralgia, peripheral_edema]
    advisory_grade: 3                 # Grade ≥3 = advisory in pre-cycle checklist

  blocking_modes:
    neuropathy_grade_2: advisory
    neuropathy_grade_3_before_t: soft_block
    neuropathy_grade_4: hard_block
    infusion_reaction_grade_4: hard_block
    symptoms_grade_3_or_higher: advisory
```

These values are consumed by `clinical.neuropathy`, `clinical.infusion_reactions`, and `clinical.symptoms` — no magic numbers in code.

---

## Day-by-Day Plan

### DAY 21 — Sprint planning, specialist review, scaffolding
**Morning (~2h)** — Specialist YAML review; commit overrides (or note defaults accepted in `PROJECT_LOG.md`).
**Afternoon (~3h)** — Add `toxicity:` block to `config/institution.defaults.yaml`. Scaffold `src/clinical/neuropathy.py`, `src/clinical/infusion_reactions.py`, `src/clinical/symptoms.py` with function signatures only. Empty test files. Run scaffolds for migrations 0007–0010 (empty `up`/`down`); confirm runner picks them up.
**Commit:** `Added Sprint 7 toxicity module scaffolding`

### DAY 22 — US-027 part 1: neuropathy migration + grading rules
- Implement `0007_neuropathy_assessment.py` up/down.
- Implement `clinical/neuropathy.py`:
  - `effective_grade(sensory: int, motor: int, config) -> int` — pure; respects `use_higher_grade_for_action`.
  - `recommended_action(grade: int, phase: str, config) -> NeuropathyAction` — returns dataclass `{dose_pct, action_code, advisory_text}`.
- Unit tests: each grade 0–4 in both phases (AC, T) against config fixture; invalid grade raises `ValueError`.
- `services/neuropathy.py`: `create`, `update`, `delete` (soft), `list_for_patient`, `latest`. Audit on every write (`neuropathy_created`, `neuropathy_updated`, `neuropathy_deleted`).
**Commit:** `Added neuropathy CTCAE grading service and rules`

### DAY 23 — US-027 part 2: neuropathy dialog + panel row
- `views/dialogs/neuropathy_dialog.py`: date, sensory grade, motor grade (both 0–4 dropdowns with CTCAE description tooltips), notes, optional cycle link.
- Toxicity panel row (placeholder component on Day 23; full panel on Day 29): "Neuropathy: sensory G2 / motor G1 (2026-04-15) — recommend −20% next dose."
- Edit + delete flows wired to service; audit verified.
- Tests: dialog validation, recommended-action display matches `recommended_action()` output for every grade.
**Commit:** `Added neuropathy entry dialog and recommended action display`
**US-027 DONE — 3 pts**

### DAY 24 — US-028 part 1: infusion reaction migration + rechallenge logic
- Implement `0008_infusion_reaction.py` up/down.
- Implement `clinical/infusion_reactions.py`:
  - `rechallenge_advice(grade: int, config) -> RechallengeAdvice` — returns dataclass `{rechallenge: bool, rate_pct: int|None, switch_agent_to: str|None, hard_block: bool, advisory_text: str}`.
- Unit tests: G1–G4 against config; G4 sets `hard_block=True`; unknown grade raises.
- `services/infusion_reactions.py`: `create`, `update`, `delete` (soft), `list_for_patient`, `list_for_cycle`. Audit on every write.
**Commit:** `Added infusion reaction service and rechallenge rules`

### DAY 25 — US-028 part 2: reaction dialog + history + rechallenge advisory
- `views/dialogs/infusion_reaction_dialog.py`: cycle (dropdown of patient's cycles), agent, onset_min, severity grade (1–4), symptoms (multi-select from config vocab), response (text), rechallenge outcome (only enabled after a subsequent cycle exists).
- After save: surface rechallenge advisory banner in the dialog itself: e.g., G3 → "Do not rechallenge with paclitaxel; switch to nab-paclitaxel or docetaxel."
- Toxicity panel row (placeholder): "Last reaction: paclitaxel · G2 at 14 min · rechallenged @ 50% · tolerated."
- Tests: dialog validation, rechallenge advisory text matches `rechallenge_advice()` output.
**Commit:** `Added infusion reaction logging and rechallenge advisory`
**US-028 DONE — 3 pts**

### DAY 26 — US-029: G-CSF service + dialog + ANC chart marker
- Implement `0009_gcsf_admin.py` up/down.
- `services/gcsf.py`: `create`, `update`, `delete` (soft), `list_for_patient`, `list_for_cycle`. Audit on every write.
- `views/dialogs/gcsf_dialog.py`: date, agent (config vocab), dose_mg, prophylaxis type, optional cycle link.
- **Extend `views/components/anc_trend_chart.py`**: when an ANC reading falls within `[gcsf_admin.admin_date, admin_date + 7d]`, render the marker as a triangle (G-CSF-stimulated) instead of the default circle. Legend updated to show both glyphs.
- Toxicity panel row (placeholder): "G-CSF: pegfilgrastim — 6 mg on 2026-04-12 (primary, cycle 3)."
- Tests: service CRUD; chart-integration test renders with mixed marker types.
**Commit:** `Added G-CSF administration logging with ANC chart marker`
**US-029 DONE — 2 pts**

### DAY 27 — US-030 part 1: symptom migration + quick-entry model + dialog
- Implement `0010_symptom_entry.py` up/down.
- Implement `clinical/symptoms.py`:
  - `applicable_symptoms(phase: str, config) -> list[str]` — returns base set in AC; base+T-additional in T.
  - `is_advisory(grade: int, config) -> bool` — true when grade ≥ `advisory_grade`.
- `services/symptoms.py`: `create_many` (one batch per cycle), `update`, `delete` (soft), `list_for_patient`, `list_for_cycle`.
- `views/dialogs/symptom_quick_entry_dialog.py`: one row per applicable symptom, grade 0–4 dropdown, notes (optional). Designed to launch from cycle save so all symptoms for a cycle are captured at once.
**Commit:** `Added symptom quick-entry service and dialog`

### DAY 28 — US-030 part 2: symptom history + cycle-save integration + T-phase additions
- Hook symptom dialog into the cycle-completion flow: after a cycle saves successfully, prompt "Capture symptoms for this cycle? (skip / fill)". Skipping is allowed; record nothing.
- Symptom set adapts to cycle phase: AC cycles show 4 symptoms; T cycles show 6 (per config).
- Toxicity panel row (placeholder): "Symptoms last cycle: nausea G2, fatigue G3 (advisory), mucositis G0, constipation G1."
- Advisory glyph appears next to any symptom at or above `advisory_grade`.
- Tests: cycle-phase to symptom-set mapping; advisory glyph rendering.
**Commit:** `Added symptom quick-entry to cycle completion and T-phase additions`
**US-030 DONE — 3 pts**

### DAY 29 — Toxicity panel integration + end-to-end
- Promote the four placeholder rows into a consolidated `views/components/toxicity_panel.py` mounted in the dashboard below the cardiotoxicity panel.
  - Section 1: Neuropathy (latest assessment + recommended action)
  - Section 2: Infusion reactions (latest reaction + rechallenge advisory)
  - Section 3: G-CSF (latest admin)
  - Section 4: Symptoms (latest cycle's symptoms with advisory glyphs)
- Each section has "View history" + "Add new" actions.
- End-to-end test: patient enters AC2 → log G1 sensory neuropathy → log G2 paclitaxel reaction (cycle linkage) → log pegfilgrastim → log nausea G2 + fatigue G1 → all visible in panel; audit viewer shows every entry.
- Regression sweep: every Sprint 5 + Sprint 6 test passes; cardiotoxicity panel unchanged.
**Commit:** `Added consolidated toxicity panel and end-to-end coverage`

### DAY 30 — Demo, retro, summary
- Demo walkthrough on a fixture patient who is mid-T phase: capture symptoms → grade neuropathy at G2 → see recommended −20% advisory → log a G2 reaction → see rechallenge advisory → log G-CSF → ANC chart marker visible.
- Write `docs/SPRINT_7_SUMMARY.md` matching the Sprint 6 summary shape.
- Update `docs/PROJECT_LOG.md` close-out entry.
- Tag `v2-sprint7`.
**Commit:** `Added Sprint 7 summary and close-out`

---

## Story Acceptance Criteria

### US-027 — Peripheral neuropathy CTCAE grading (3 pts)
- [ ] `neuropathy_assessment` table created via migration 0007 with `up` and `down`
- [ ] Sensory and motor grades stored separately, each constrained 0–4
- [ ] CTCAE version stamped on every row (default from config)
- [ ] Add / edit / soft-delete via `services/neuropathy.py`; audit row on every mutation
- [ ] Dialog enforces grade range; tooltip shows CTCAE descriptor for each grade
- [ ] `effective_grade()` and `recommended_action()` are pure functions; no DB or Tk imports
- [ ] Recommended action computed from config, not hardcoded
- [ ] Toxicity panel section shows latest assessment + recommended action
- [ ] Unit + integration test coverage ≥ 90% on `clinical/neuropathy.py`

### US-028 — Infusion hypersensitivity reaction log (3 pts)
- [ ] `infusion_reaction` table created via migration 0008 with `up` and `down`
- [ ] Reaction tied to a specific cycle; agent, onset_min, severity, symptoms, response, rechallenge_outcome captured
- [ ] Symptoms vocabulary read from config (no free-text symptom field)
- [ ] Add / edit / soft-delete via `services/infusion_reactions.py`; audit row on every mutation
- [ ] Rechallenge advisory shown immediately after save, sourced from `rechallenge_advice()`
- [ ] G4 reactions trigger `hard_block: true` advisory text (Sprint 8 will enforce; Sprint 7 only displays)
- [ ] Toxicity panel section shows latest reaction + rechallenge text
- [ ] Unit + integration test coverage ≥ 90% on `clinical/infusion_reactions.py`

### US-029 — G-CSF administration log (2 pts)
- [ ] `gcsf_admin` table created via migration 0009 with `up` and `down`
- [ ] Agent vocabulary, prophylaxis types read from config
- [ ] Add / edit / soft-delete via `services/gcsf.py`; audit row on every mutation
- [ ] ANC trend chart renders G-CSF-stimulated readings with a distinct glyph (triangle); legend updated
- [ ] Window for "G-CSF-stimulated" classification configurable; default `[admin_date, admin_date + 7d]`
- [ ] Toxicity panel section shows latest admin (agent, dose, date, prophylaxis type)
- [ ] Chart marker integration covered by visual-regression-style test (image hash or marker-count assertion)

### US-030 — Symptom quick-entry (3 pts)
- [ ] `symptom_entry` table created via migration 0010 with `up` and `down`
- [ ] Symptom set per phase read from config; AC = 4, T = 6 by default
- [ ] Quick-entry dialog launches after cycle save (skippable)
- [ ] Add / edit / soft-delete via `services/symptoms.py`; audit row on every mutation
- [ ] Grade ≥ `advisory_grade` highlighted with advisory glyph
- [ ] Toxicity panel section shows latest cycle's symptoms inline with grades
- [ ] Phase-to-symptom-set mapping covered by unit test
- [ ] No hardcoded symptom names anywhere in code

---

## Success Criteria (sprint-level)

- [ ] All four stories merged to master, tagged `v2-sprint7`
- [ ] Coverage on new `src/clinical/` modules (neuropathy, infusion_reactions, symptoms) ≥ 90%
- [ ] Coverage on new `src/services/` modules ≥ 85%
- [ ] No regressions in the Sprint 5 or Sprint 6 test suites
- [ ] Dashboard load with toxicity panel + cardiotoxicity panel + cumulative calc < 200 ms at P95 on demo DB
- [ ] Demo walkthrough (Day 30) completes neuropathy → reaction → G-CSF → symptoms without manual DB poking
- [ ] Zero magic-number thresholds, vocabularies, or symptom names in code — every value resolves through config
- [ ] Audit viewer (US-022) shows every Sprint 7 mutation with the correct action label

---

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Specialist YAML review slips past Day 21 | Medium | Ship defaults; specialist overrides are a one-line YAML change later |
| Symptom quick-entry dialog feels heavy and gets skipped every cycle | Medium | One row per symptom, grade dropdown only, defaults to 0 — total interaction < 15 s. Skip is one-click |
| Rechallenge advisory mistaken for an enforcement gate | Medium | Sprint 7 surfaces advisory text only. Sprint 8's pre-cycle checklist is where blocking happens; document in advisory text itself |
| ANC chart glyph regression breaks legibility | Low | Visual-regression test on Day 26; manual review on Day 29 |
| Four migrations land on the same patient DB and one fails mid-batch | Low | Each migration wrapped in transaction; runner takes a backup before each (Sprint 5 plumbing); fixture test rolls forward and back through 0001–0010 |
| `clinical/` module count grows from 1 to 4 in one sprint, inviting a base class | High | No registry, no base class, no shared interface. Each module is a flat collection of pure functions |
| Sprint 7 spec creeps to add ECOG, hospitalization, port patency | High | Section "Out of Scope" below. Refer requests there to Sprint 10 stretch or V3 |

---

## Out of Scope (reject on sight)

- ECOG performance status capture → Sprint 10 stretch (per V2 plan)
- Hospitalization / ER visit capture (N12) → V2 backlog, not Sprint 7
- Port / line patency tracking → V3
- Cohort outlier detection on toxicity rates → V3 (needs accumulated data)
- Patient-facing PRO entry of symptoms → V3 (different product)
- Free-text symptom or reaction-symptom entry → vocabulary-only in V2
- Trastuzumab-specific cardiotoxicity from reaction history → V3 (no AC-TH in V2)
- Dose-modification *enforcement* on neuropathy → Sprint 8 pre-cycle checklist
- Automatic G-CSF reminder ("schedule pegfilgrastim 24 h post-cycle") → V3 workflow

If any of the above surfaces mid-sprint, log to `docs/BACKLOG_V3.md` (or Sprint 10 stretch list) and move on.

---

## Definition of Done (per story)

1. Code committed with single-line `Added ...` message
2. Migration `up` and `down` tested against a Sprint-6-tagged DB snapshot
3. Unit tests on pure functions + integration test on service surface
4. Config values, vocabularies, and thresholds read from YAML, not hardcoded
5. Audit entries written for every create / update / delete
6. Dialog rendered cleanly at 1920×1080 and 1024×768
7. Toxicity panel section visible on dashboard with current data
8. No regression in Sprint 5 or Sprint 6 test suite
9. Entry in `PROJECT_LOG.md` for the day

---

## Post-Sprint Carry-Over Protocol

If any story is incomplete at end of Day 30:

- **US-027 incomplete** → carry into Sprint 8 Day 1, but pre-cycle checklist (US-033) must defer the neuropathy rule until US-027 lands. Worst case: Sprint 8 ships with the neuropathy rule in `advisory` mode and tightens to `soft_block` in a Sprint 8 follow-up commit.
- **US-028 incomplete** → carry into Sprint 8 Day 1; G4 hard-block in pre-cycle checklist deferred similarly.
- **US-029 incomplete** → defer ANC chart glyph; data still capturable via dialog. Visual integration is polish, not safety.
- **US-030 incomplete** → carry into Sprint 8; pre-cycle checklist's "Grade ≥3 symptom" rule waits.

**Do not start Sprint 8 stories with Sprint 7 carry-over still open** unless the carry-over is purely visual (US-029 chart glyph). The pre-cycle checklist in Sprint 8 reads everything Sprint 7 ships; partial Sprint 7 = partial checklist = a safety hole the rules engine cannot detect.
