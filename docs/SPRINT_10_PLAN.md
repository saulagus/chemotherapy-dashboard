# Sprint 10 Plan - V2 Close-Out, Reliability, and N12 Completion

**V2 - Weeks 23-24 - Days 51-59 of V2 - Final sprint before V2 release**

---

## Sprint Goal

Sprint 10 closes V2. By the end of the sprint, the app must contain every item still inside the V2 scope, protect user data with an in-app backup/restore path, expose configuration safely, support keyboard-driven workflows, prove performance and coverage targets, and ship with release documentation that a V1 user can follow.

This plan intentionally expands the old Sprint 10 scope. The original V2 summary listed `[N12] Hospitalization / ER visit capture` as **IN V2**, but the prior Sprint 10 draft treated the sprint as polish only. That mismatch is now resolved: hospitalization / ER visit capture is added as `US-043`, and it is the only new clinical surface allowed in this sprint.

**V2 release rule:** by Day 59, every story below is either complete and verified or V2 does not release. After Day 59, new work becomes v2.0.1, v2.1, or V3.

---

## Stories

| Story | Title | Points | Status | Release impact |
|-------|-------|--------|--------|----------------|
| US-043 | Hospitalization / ER visit capture | 3 | To Do | Required because N12 is in the V2 scope summary |
| US-039 | Backup / restore database | 3 | To Do | Release blocker if backup is incomplete |
| US-040 | Keyboard shortcuts & accessibility pass | 2 | To Do | Non-blocking if partially complete and documented |
| US-040a | Settings inspection dialog (read-only config view) | 1 | To Do | Non-blocking if YAML-open fallback ships |
| US-041 | Performance & test-coverage hardening | 2 | To Do | Perf blockers are release blockers; coverage delta can move to v2.1 |
| US-042 | V2 documentation & release prep | 1 | To Do | Release blocker |

**Total: 12 story points - 9 development days**

The sprint is heavier than the original 9-point polish plan because N12 was missing from the close-out scope. Keep US-043 narrow: capture, view, audit, and test hospitalization/ER events. Do not add predictive logic, reports, pathway analytics, billing fields, or new clinical decision support around hospitalization events in V2.

---

## V2 Scope Reconciliation

This table is the source of truth for "anything missing for V2." Sprint 10 exists to clear the final rows.

| V2 item | Status before Sprint 10 | Sprint 10 handling |
|---------|--------------------------|--------------------|
| H1 Edit/delete patient, cycle, lab with audit trail | Done in Sprint 5 | Regression only |
| H3 Low-ANC alert banner | Done in Sprint 8 | Regression only |
| H4 Toxicity tracking | Done in Sprint 7 | Regression only |
| H5 PDF export | Done in Sprint 9 | Perf/regression only |
| M2 Search/filter/sort patient list | Done in Sprint 8 | Keyboard focus shortcut only |
| M3 Print-friendly view | Done in Sprint 9 | Shortcut and perf regression only |
| M5 Dose-modification history view | Done in Sprint 9 | Regression only |
| L4 Audit trail | Done in Sprint 5 | Extend action set for backup/restore and US-043 |
| L5 Cycle due status | Done in Sprint 8 | Regression only |
| N1 Cumulative anthracycline dose | Done in Sprint 6 | Settings visibility and regression only |
| N2 LVEF/cardiac function tracking | Done in Sprint 6 | Settings visibility and regression only |
| N3 Peripheral neuropathy CTCAE grading | Done in Sprint 7 | Settings visibility and regression only |
| N4 Pre-cycle safety checklist | Done in Sprint 8 | Perf/regression only |
| N5 Next-cycle-due status | Done in Sprint 8 | Regression only |
| N6 Infusion hypersensitivity reaction log | Done in Sprint 7 | Regression only |
| N7 G-CSF administration log | Done in Sprint 7 | Regression only |
| N8 BSA / height / weight per cycle | Done in Sprint 6 | Regression only |
| N9 Audit trail | Done in Sprint 5 | Extend events only |
| N10 Backup / restore | Missing | US-039 |
| N11 Symptom quick-entry | Done in Sprint 7 | Regression only |
| N12 Hospitalization / ER visit capture | Missing | US-043 |
| N14 Clinical-rules engine module | Done across Sprints 6-8 | Regression only |
| Institutional configuration layer | Done in Sprint 5, expanded since | US-040a visibility and Sprint 10 config additions |

Explicitly deferred remains unchanged from `docs/V2_PLAN_SUMMARY.txt`: EHR/FHIR, multi-user/PostgreSQL, other regimens, web/mobile, CSV import, protocol comparison, ECOG, port/line patency, cohort analytics, patient-facing PRO app, MD e-sign, QI metrics, and medication/allergy/premed management.

---

## Sequencing

```
Day 51  -> N12 decisions + scaffolding + config schema additions
Day 52  -> US-043 migration/service/rules-free data layer
Day 53  -> US-043 dialog + dashboard/panel integration + tests
Day 54  -> US-039 backup service + backup dialog
Day 55  -> US-039 restore flow + migration replay + tests
Day 56  -> US-040 shortcuts + US-040a settings viewer
Day 57  -> US-041 performance + coverage tooling + regression hardening
Day 58  -> US-042 release notes, upgrade guide, README, demo script
Day 59  -> final verification, summaries, tags, push
```

Ordering rules:

- `US-043` goes first because it is the only missing V2 clinical story and it needs a migration.
- `US-039` goes second because backup/restore is the highest data-loss risk.
- `US-040` and `US-040a` share Day 56 because both are self-contained UX polish over existing handlers/config.
- `US-041` must follow all feature work; measuring a moving target wastes the hardening pass.
- `US-042` must be last; release docs freeze the exact shipped surface.

---

## Dependencies

| From | Artifact | Why Sprint 10 needs it |
|------|----------|------------------------|
| Sprint 5 | Migration runner | US-043 adds migration `0011`; US-039 restore may replay older DBs forward |
| Sprint 5 | Audit log | US-043 create/update/delete and US-039 backup/restore write audit events |
| Sprint 5 | Institution config | US-040a renders the loaded config; Sprint 10 adds final config sections |
| Sprint 6 | Cardiotoxicity services/config | US-040a must display thresholds; US-041 protects perf |
| Sprint 7 | Toxicity services/config | US-043 reason list includes toxicity-related events; regression protected |
| Sprint 8 | Checklist/workflow services | Dashboard integration and perf budgets include checklist data gathering |
| Sprint 9 | Reports/export services | Performance budgets include PDF/CSV export and print dashboard |
| Sprint 9 close-out | `v2-sprint9` tag green | Sprint 10 cannot release against a moving Sprint 9 surface |

If `v2-sprint9` is not tagged and green on Day 51, fix that before touching Sprint 10 stories.

---

## Day 51 Decisions

Resolve these in the planning session. If no stakeholder is available, accept defaults and document the decision in `docs/PROJECT_LOG.md`.

| Topic | Default | Decision |
|-------|---------|----------|
| N12 event types | `hospitalization`, `er_visit` | Accept unless specialist requests different wording |
| N12 cycle link | Optional `cycle_id`; event can be patient-level | Accept |
| N12 reason vocabulary | `febrile_neutropenia`, `infection`, `infusion_reaction`, `cardiotoxicity`, `uncontrolled_symptoms`, `thrombosis_or_line_issue`, `other` | Accept unless specialist adds one |
| N12 outcome vocabulary | `discharged_home`, `admitted`, `transferred`, `ongoing`, `death`, `unknown` | Accept |
| N12 reports integration | Not in V2 PDF/CSV; dashboard visibility only | Accept |
| Backup reminder cadence | Use existing `backup.reminder_interval_days`, default 7 | Accept |
| Backup directory | `~/Documents/ChemoDashboard/backups` | Accept |
| Backup retention | Keep last 10; warn before deleting | Accept |
| Restore confirmation | Type institution name | Accept |
| Shortcuts | `Ctrl+N`, `Ctrl+L`, `Ctrl+F`, `Ctrl+B`, `Ctrl+P`, `Ctrl+E`, `Esc`, `?` | Accept |
| macOS shortcut mirroring | Mirror Ctrl shortcuts to Cmd | Accept |
| Settings grouping | By section/domain | Accept |
| Performance budget | P95 dashboard load under 200 ms on 100-patient fixture | Accept |
| Coverage target | `src/clinical/` and `src/services/` at or above 85% | Accept |
| Coverage tooling | Add pinned dev/test coverage tooling | Accept |
| Release notes audience | Nurse plus sysadmin in one file | Accept |

---

## Architecture Additions

Sprint 10 adds one clinical capture surface, one data-protection service, one settings viewer, one shortcut registry, coverage tooling, and release docs.

```
src/
├── migrations/
│   └── 0011_hospitalization_events.py       <- NEW - N12 event table
├── services/
│   ├── backup.py                            <- NEW - SQLite online backup/restore
│   └── hospitalization_events.py            <- NEW - N12 CRUD + audit
├── views/
│   ├── components/
│   │   ├── hospitalization_events_panel.py  <- NEW - recent N12 event display
│   │   └── settings_viewer.py               <- NEW - read-only config tree
│   ├── dialogs/
│   │   ├── hospitalization_event_dialog.py  <- NEW - add/edit N12 event
│   │   ├── backup_dialog.py                 <- NEW - back up now + reminder
│   │   ├── restore_dialog.py                <- NEW - restore confirmation
│   │   ├── settings_dialog.py               <- NEW - hosts settings_viewer
│   │   └── shortcuts_help_dialog.py         <- NEW - rendered from registry
│   └── shortcuts.py                         <- NEW - central key-binding registry
docs/
├── RELEASE_NOTES_V2.md                      <- NEW
├── UPGRADE_GUIDE_V1_TO_V2.md                <- NEW
├── SHORTCUTS.md                             <- NEW
├── DEMO_SCRIPT_V2.md                        <- NEW
├── SPRINT_10_SUMMARY.md                     <- NEW
└── V2_RELEASE_SUMMARY.md                    <- NEW
tests/
├── test_hospitalization_events_service.py   <- NEW
├── test_hospitalization_event_dialog.py     <- NEW or focused component tests
├── test_backup_service.py                   <- NEW
├── test_settings_viewer.py                  <- NEW
├── test_shortcuts.py                        <- NEW
├── test_perf_dashboard_load.py              <- NEW
└── test_perf_pdf_render.py                  <- NEW
```

Patterns to follow:

- All database writes go through `src/services/`.
- Every service write emits an audit row in the same transaction unless the operation is intentionally read-only.
- Dialog modules follow existing Tkinter style: shared font constants, shared color constants, body before pinned bottom actions, and grid layout for forms.
- New config fields extend the Pydantic schema and `config/institution.defaults.yaml` together.
- Settings viewer renders the loaded validated config object, not raw YAML.
- Shortcuts are registered centrally; no scattered hardcoded bindings.

---

## Schema Plan

Sprint 10 ships exactly one schema migration: `src/migrations/0011_hospitalization_events.py`.

### `hospitalization_events` table

Planned columns:

| Column | Type | Required | Notes |
|--------|------|----------|-------|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | Yes | Internal row id |
| `patient_id` | TEXT | Yes | Match Sprint 7 toxicity tables; references `patients(patient_id)` |
| `cycle_id` | INTEGER | No | Optional link to a cycle |
| `event_date` | TEXT | Yes | ISO date string |
| `event_type` | TEXT | Yes | `hospitalization` or `er_visit` |
| `reason` | TEXT | Yes | Config vocabulary plus `other` |
| `severity` | INTEGER | No | Optional CTCAE-like grade 1-5; no rule engine in V2 |
| `outcome` | TEXT | Yes | Config vocabulary |
| `notes` | TEXT | No | Free text |
| `created_at` | TEXT | Yes | Timestamp |
| `updated_at` | TEXT | No | Timestamp |
| `deleted_at` | TEXT | No | Soft-delete |

Index plan:

- `idx_hospitalization_events_patient_date` on `(patient_id, event_date DESC)`
- `idx_hospitalization_events_cycle` on `cycle_id`
- `idx_hospitalization_events_deleted` on `deleted_at`

Rollback plan:

- `down(conn)` drops indexes and the table.
- Restore tests still rely on forward migrations; no production workflow runs down migrations.

No other schema changes are allowed in Sprint 10.

---

## Config Plan

Preserve existing keys. In particular, the backup reminder key already exists and remains:

```yaml
backup:
  reminder_interval_days: 7
```

Add the missing Sprint 10 fields without renaming existing config:

```yaml
hospitalizations:
  event_types:
    - hospitalization
    - er_visit
  reason_vocab:
    - febrile_neutropenia
    - infection
    - infusion_reaction
    - cardiotoxicity
    - uncontrolled_symptoms
    - thrombosis_or_line_issue
    - other
  outcome_vocab:
    - discharged_home
    - admitted
    - transferred
    - ongoing
    - death
    - unknown

backup:
  reminder_interval_days: 7
  default_directory: "~/Documents/ChemoDashboard/backups"
  retention_count: 10
  filename_pattern: "chemo_dashboard_{YYYY-MM-DD}_{HHmm}.db"
  warn_before_delete: true

restore:
  require_confirmation_text: institution_name
  pre_restore_backup_filename: ".pre-restore-{YYYY-MM-DD-HHmm}.db"

shortcuts:
  enabled: true
  bindings:
    new_patient: "Ctrl+N"
    add_labs: "Ctrl+L"
    search: "Ctrl+F"
    backup_now: "Ctrl+B"
    print: "Ctrl+P"
    export_pdf: "Ctrl+E"
    close_dialog: "Escape"
    shortcuts_help: "question"

settings_viewer:
  enabled: true
  show_origin: true
  group_by: section

performance:
  budgets_ms:
    dashboard_load_p95: 200
    pdf_oncologist_p95: 800
    pdf_print_dashboard_p95: 600
    csv_labs_p95: 200
    cycle_save_p95: 150
```

Schema expectations:

- Pydantic models forbid unknown keys, as existing config sections do.
- Existing config tests expand to cover new defaults, invalid values, and override precedence.
- If this project does not split runtime and dev dependencies, coverage tooling is pinned in `requirements.txt` with a comment identifying it as test tooling.

---

## Public Interfaces

### US-043 service API

Planned module: `src/services/hospitalization_events.py`

```python
@dataclass
class HospitalizationEvent:
    id: int | None
    patient_id: str
    cycle_id: int | None
    event_date: date
    event_type: str
    reason: str
    severity: int | None
    outcome: str
    notes: str
    created_at: str | None = None
    updated_at: str | None = None
    deleted_at: str | None = None
```

Functions:

- `create_event(conn, event, actor=None) -> HospitalizationEvent`
- `update_event(conn, event, actor=None) -> HospitalizationEvent`
- `soft_delete_event(conn, event_id, actor=None) -> None`
- `get_event(conn, event_id, include_deleted=False) -> HospitalizationEvent | None`
- `list_events_for_patient(conn, patient_id, include_deleted=False) -> list[HospitalizationEvent]`
- `list_events_for_cycle(conn, cycle_id, include_deleted=False) -> list[HospitalizationEvent]`
- `latest_event_for_patient(conn, patient_id) -> HospitalizationEvent | None`

Validation:

- `patient_id` required.
- `event_date` required.
- `event_type` must be in config vocabulary.
- `reason` must be in config vocabulary.
- `outcome` must be in config vocabulary.
- `severity`, when supplied, must be 1-5.
- `cycle_id` may be `None`.

Audit actions:

- `hospitalization_create`
- `hospitalization_update`
- `hospitalization_soft_delete`

### US-039 service API

Planned module: `src/services/backup.py`

Data classes:

- `BackupResult(path, size_bytes, schema_version, audit_id)`
- `BackupFile(path, size_bytes, created_at, schema_version)`
- `RestoreResult(restored_path, pre_restore_path, schema_version_before, schema_version_after, migrations_applied, audit_id)`

Functions:

- `create_backup(conn, target_dir, config, actor=None) -> BackupResult`
- `list_backups(target_dir, config) -> list[BackupFile]`
- `prune_old_backups(target_dir, config) -> list[Path]`
- `read_schema_version(db_path) -> int`
- `restore_backup(backup_path, current_db_path, config, actor=None) -> RestoreResult`

Restore contract:

- Never silently overwrites the current DB.
- Creates a pre-restore backup before replacing the DB.
- Validates the incoming DB is SQLite.
- Reads schema version before replacement when possible.
- Runs forward migrations after restore if the restored DB is older.
- Writes audit row after successful restore.

### US-040 shortcut registry

Planned module: `src/views/shortcuts.py`

- One registry bound to the root Tk window.
- Config drives bindings.
- Collision detected at registration.
- macOS Cmd mirror registered automatically for Ctrl shortcuts.
- Help dialog reads registry entries, not a duplicate list.

### US-040a settings viewer

Planned component: `src/views/components/settings_viewer.py`

- Input: loaded `InstitutionConfig`.
- Output: read-only tree rows of key path, value, and origin.
- Search filters by key path.
- Completeness test walks defaults and asserts every key path is rendered.

---

## Day-by-Day Plan

### Day 51 - Sprint 10 planning, V2 gap reconciliation, scaffolding

Tasks:

- Confirm `v2-sprint9` tag exists and full suite is green from Sprint 9 close-out.
- Record Day 51 planning decisions in `docs/PROJECT_LOG.md`.
- Add/confirm config defaults and schema models for hospitalizations, backup additions, restore, shortcuts, settings viewer, and performance budgets.
- Scaffold `0011_hospitalization_events.py`, `services/hospitalization_events.py`, `services/backup.py`, `views/shortcuts.py`, dialogs/components, and test files.

Verification:

- Import check for config schema and scaffolded modules.
- Logic check for config load with new defaults.
- Full suite: `pytest tests/ -v`.

Commit:

- `Added Sprint 10 V2 close-out scaffolding`

### Day 52 - US-043 backend: migration and service

Tasks:

- Implement migration `0011_hospitalization_events.py`.
- Implement `HospitalizationEvent` dataclass and service CRUD functions.
- Add audit actions and audit writes.
- Enforce validation in the service layer.

Verification:

- Import check: `python3 -c "from services.hospitalization_events import HospitalizationEvent; print('OK')"`
- Logic check: inline create/list/update/delete round trip against in-memory DB after migrations.
- Focused tests: `pytest tests/test_hospitalization_events_service.py -v`.
- Full suite: `pytest tests/ -v`.

Commit:

- `Added hospitalization event service`

### Day 53 - US-043 UI: dialog and dashboard visibility

Tasks:

- Implement add/edit dialog with existing dialog layout patterns.
- Add recent hospitalization/ER event panel to patient workflow.
- Wire add/edit/delete actions.
- Add empty state.
- Ensure no report/PDF expansion in V2.

Verification:

- Import check for dialog and panel.
- Logic check for dialog validation helpers.
- Focused tests for dialog/panel behavior.
- Full suite: `pytest tests/ -v`.

Commit:

- `Added hospitalization event capture UI`

US-043 done when backend, UI, audit, and tests all pass.

### Day 54 - US-039 backup service and backup dialog

Tasks:

- Implement SQLite online backup using `sqlite3.Connection.backup()`.
- Implement backup listing and retention calculation.
- Add backup dialog with default directory and success state.
- Add reminder logic using `backup.reminder_interval_days`.
- Write audit row `backup_created`.

Verification:

- Import check: `python3 -c "from services.backup import create_backup; print('OK')"`
- Logic check: create backup, open backup independently, compare expected row count.
- Focused tests: `pytest tests/test_backup_service.py -v`.
- Full suite: `pytest tests/ -v`.

Commit:

- `Added database backup service and dialog`

### Day 55 - US-039 restore flow and migration replay

Tasks:

- Implement restore preflight and confirmation helpers.
- Preserve current DB as a pre-restore backup before replacement.
- Validate selected backup DB.
- Replay forward migrations after restore when needed.
- Add restore dialog with typed confirmation.
- Write audit row `restore_performed`.

Verification:

- Import check for restore API.
- Logic check: backup -> mutate -> restore -> original state recovered.
- Focused restore tests, including older-schema fixture.
- Full suite: `pytest tests/ -v`.

Commit:

- `Added database restore with confirmation and migration replay`

US-039 done when backup, restore, audit, retention, and migration replay tests pass.

### Day 56 - US-040 shortcuts and US-040a settings viewer

Tasks:

- Implement central shortcut registry.
- Register default shortcuts from config.
- Add shortcut help dialog.
- Apply accessibility pass: tab order, Enter primary action, Esc cancel, visible focus.
- Implement read-only settings dialog and config tree viewer.
- Add `docs/SHORTCUTS.md`.

Verification:

- Import checks for `views.shortcuts`, settings viewer, and dialogs.
- Logic check: shortcut collision raises; settings tree includes known key paths.
- Focused tests: `pytest tests/test_shortcuts.py tests/test_settings_viewer.py -v`.
- Full suite: `pytest tests/ -v`.

Commit:

- `Added keyboard shortcuts and settings inspection`

US-040 and US-040a done when registry, docs, settings viewer, and accessibility checklist pass.

### Day 57 - US-041 performance and coverage hardening

Tasks:

- Add pinned coverage tooling (`pytest-cov` or `coverage`) as test tooling.
- Add/generate 100-patient performance fixture.
- Add dashboard, cycle save, PDF, and CSV performance tests.
- Run coverage against `src/clinical/` and `src/services/`.
- Add targeted tests for uncovered clinical/service branches.
- Fix only real hotspots: indexes, cached config reads, query consolidation.

Verification:

- Import check for any new helpers.
- Logic check for performance fixture shape.
- Focused perf tests.
- Coverage command:
  - `pytest --cov=src/clinical --cov=src/services --cov-report=term-missing`
- Full suite: `pytest tests/ -v`.

Commit:

- `Added performance and coverage hardening`

US-041 done when perf budgets pass and coverage is measured. If coverage remains below 85%, document the deficit and file v2.1 work; do not fake coverage.

### Day 58 - US-042 release documentation

Tasks:

- Write `docs/RELEASE_NOTES_V2.md`.
- Write `docs/UPGRADE_GUIDE_V1_TO_V2.md`.
- Update `README.md`.
- Write `docs/DEMO_SCRIPT_V2.md`.
- Confirm `docs/SHORTCUTS.md` matches live registry.
- Consolidate deferred items into v2.1/V3 backlog docs if new gaps surfaced.

Verification:

- Markdown link/path sanity check.
- Manual upgrade-guide dry run against a copied v1 DB if available.
- Full suite: `pytest tests/ -v`.

Commit:

- `Added V2 release notes, upgrade guide, demo script, and README`

### Day 59 - final verification, summaries, tags

Tasks:

- Run final demo from `docs/DEMO_SCRIPT_V2.md`.
- Write `docs/SPRINT_10_SUMMARY.md`.
- Write `docs/V2_RELEASE_SUMMARY.md`.
- Update `docs/PROJECT_LOG.md` with close-out.
- Tag `v2-sprint10`.
- Tag `v2.0.0`.
- Push branch and tags.

Verification:

- Full suite: `pytest tests/ -v`.
- Coverage command.
- Perf command.
- Demo walkthrough complete.
- `git status --short` clean before tagging.

Commit:

- `Added Sprint 10 summary and V2 release close-out`

---

## Story Acceptance Criteria

### US-043 - Hospitalization / ER visit capture

- [ ] Migration `0011_hospitalization_events.py` creates the table and indexes.
- [ ] Service supports create, update, list by patient, list by cycle, latest by patient, get by id, and soft delete.
- [ ] `patient_id`, `event_date`, `event_type`, `reason`, and `outcome` are required.
- [ ] `cycle_id` is optional.
- [ ] `event_type`, `reason`, and `outcome` use config vocabularies.
- [ ] `severity` accepts only 1-5 when provided.
- [ ] Service writes audit rows for create, update, and soft delete.
- [ ] Dialog supports add and edit.
- [ ] Patient workflow displays recent events and a clear empty state.
- [ ] Soft-deleted events are hidden by default.
- [ ] No PDF/CSV/reporting integration is added in V2.
- [ ] Happy path, empty state, invalid vocabulary, severity boundaries, optional cycle, soft-delete, and audit paths are tested.

### US-039 - Backup / restore database

- [ ] Backup uses SQLite online-backup API, not plain file copy.
- [ ] Backup file is a valid SQLite DB that opens independently.
- [ ] Backup writes `backup_created` audit row with path and size.
- [ ] Reminder uses existing `backup.reminder_interval_days`.
- [ ] Retention logic keeps the newest configured count.
- [ ] Restore requires typed confirmation.
- [ ] Restore creates a pre-restore backup before replacing current DB.
- [ ] Restore validates incoming DB before replacement.
- [ ] Restore detects schema version and runs forward migrations if needed.
- [ ] Restore writes `restore_performed` audit row.
- [ ] Round-trip test proves backup -> mutate -> restore recovers original state.
- [ ] Older-schema restore fixture migrates cleanly.

### US-040 - Keyboard shortcuts and accessibility pass

- [ ] Central registry owns all bindings.
- [ ] Default bindings come from config.
- [ ] Collisions raise during registration.
- [ ] Ctrl shortcuts mirror to Cmd on macOS.
- [ ] New patient, add labs, search, backup, print, export PDF, close dialog, and help shortcuts work.
- [ ] `?` opens help generated from registry state.
- [ ] Every dialog has sane tab order.
- [ ] Enter triggers primary action where safe.
- [ ] Esc cancels or closes dialogs.
- [ ] `docs/SHORTCUTS.md` matches live registry.

### US-040a - Settings inspection dialog

- [ ] Settings dialog is read-only.
- [ ] Viewer renders loaded Pydantic config, not raw YAML.
- [ ] Viewer shows key path and value.
- [ ] Viewer labels default vs override when `show_origin` is true.
- [ ] Search filters by key path.
- [ ] Every key in `config/institution.defaults.yaml` appears in the viewer.
- [ ] No edit affordance ships in V2.

### US-041 - Performance and test-coverage hardening

- [ ] Coverage tooling is pinned and runnable.
- [ ] Coverage is measured for `src/clinical/` and `src/services/`.
- [ ] Target is at least 85% for clinical and services.
- [ ] Performance fixture covers 100 patients, 8 cycles, and 20 labs.
- [ ] P95 dashboard load is under 200 ms.
- [ ] P95 cycle save is under 150 ms.
- [ ] Sprint 9 PDF and CSV budgets are re-asserted.
- [ ] Any perf fix is narrowly scoped.

### US-042 - V2 documentation and release prep

- [ ] `docs/RELEASE_NOTES_V2.md` exists and matches shipped surface.
- [ ] `docs/UPGRADE_GUIDE_V1_TO_V2.md` starts with backup-first instructions.
- [ ] `README.md` links release notes, upgrade guide, demo script, and shortcuts.
- [ ] `docs/DEMO_SCRIPT_V2.md` walks one feature per V2 sprint.
- [ ] `docs/SPRINT_10_SUMMARY.md` exists.
- [ ] `docs/V2_RELEASE_SUMMARY.md` exists.
- [ ] `docs/PROJECT_LOG.md` has close-out.
- [ ] Tags `v2-sprint10` and `v2.0.0` are pushed.

---

## Test Matrix

| Area | Happy path | Empty/None | Boundary | Error path | Regression |
|------|------------|------------|----------|------------|------------|
| Hospitalization service | Create/list/update/delete | No events for patient | Severity 1 and 5 | Invalid type/reason/outcome | Existing toxicity services unaffected |
| Hospitalization UI | Add/edit event | Empty panel | Long notes/reason labels | Missing required fields | Dashboard still loads patients |
| Backup | Create and reopen DB | Empty DB | Retention count 0/1/10 | Invalid target directory | Existing migrations unaffected |
| Restore | Restore round trip | Backup without optional data | Older schema -> current | Invalid SQLite file; failed confirmation | Current DB protected |
| Shortcuts | All defaults fire handlers | Disabled shortcuts | Collision | Missing handler | Existing button flows still work |
| Settings viewer | All defaults render | No overrides | Nested config keys | Unknown config rejected by schema | Existing config tests pass |
| Performance | 100-patient fixture | Small DB | P95 thresholds | Budget miss reported | Sprint 9 export budgets still pass |
| Coverage | Coverage command runs | N/A | 85% target | Missing tooling fails clearly | Full suite remains green |
| Docs | Release docs link correctly | N/A | N/A | Missing planned artifact caught | V1 docs remain historical |

Verification commands per step:

- Import check: `python3 -c "from module import X; print('OK')"`
- Logic check: inline assertion script specific to the step.
- Focused tests for the touched area.
- Full suite: `pytest tests/ -v`.
- Coverage on Day 57 and Day 59.

---

## Release Gates

V2 can release only when all of these are true:

- [ ] US-043 implemented, tested, and visible in patient workflow.
- [ ] US-039 backup works.
- [ ] US-039 restore protects the current DB before replacing it.
- [ ] Full suite passes.
- [ ] Coverage command runs and reports clinical/services coverage.
- [ ] Performance budgets pass or documented measured values are explicitly accepted.
- [ ] Release notes and upgrade guide exist.
- [ ] Sprint 10 summary and V2 release summary exist.
- [ ] No untracked release artifact is left outside git.
- [ ] `git status --short` is clean before tagging.
- [ ] `v2-sprint10` and `v2.0.0` tags are pushed.

Hard release blockers:

- Data loss risk in backup/restore.
- Failed migrations on a realistic DB.
- US-043 data cannot be saved or reloaded.
- App cannot launch.
- Full suite fails because of a real regression.
- Missing release notes or upgrade guide.

Non-blocking but must be documented:

- Coverage below 85% after real test hardening.
- One unwired shortcut if the command remains reachable by button/menu.
- Settings viewer missing origin labels if the raw current value still renders.
- Minor manual demo issue that does not affect data integrity or V2 scope.

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| N12 expands into clinical decision support | High | Sprint failure | Keep US-043 to capture/view/audit only |
| N12 migration chooses wrong patient key shape | Medium | Data inconsistency | Follow Sprint 7 toxicity tables using text `patient_id` |
| Restore corrupts current DB | High | Release blocker | Pre-restore backup before replacement; round-trip tests |
| Older backup cannot migrate forward | Medium | Release blocker | Fixture restore from older schema; use Sprint 5 runner |
| Shortcut binding conflicts appear late | Medium | UX regression | Registry collision test at startup |
| Settings viewer drifts from config | Medium | Hidden clinical threshold | Completeness test walks config defaults |
| Coverage tooling changes runtime install | Low | Packaging churn | Pin as test tooling; document in requirements if no dev split |
| Performance fixture is too slow for local loop | Medium | Slow development | Generate on demand unless committed fixture is small |
| Day 59 finds multiple bugs | Medium | Release slip | One release-blocker fix allowed; rest goes to v2.0.1/v2.1 |
| Documentation says a feature exists that failed | Low | Stakeholder trust loss | Docs land after feature verification |

---

## Out of Scope

Reject these during Sprint 10:

- Hospitalization risk prediction.
- Hospitalization reporting/PDF export.
- Admission billing fields.
- ECOG capture.
- Port/line patency.
- Medication/allergy/premed management.
- Editable settings.
- Per-user shortcut customization.
- Encrypted backups.
- Cloud backups.
- Automatic scheduled backups without user click.
- Multi-user authentication.
- New regimen support.
- New chart types.
- Web/mobile work.
- Large architectural refactors.

If any item is requested, add it to `docs/BACKLOG_V2_1.md` or `docs/BACKLOG_V3.md` and continue Sprint 10.

---

## Carry-Over Protocol

- **US-043 incomplete:** V2 cannot release because N12 is now recognized as missing V2 scope. Extend or explicitly revise V2 scope in release notes with stakeholder approval.
- **US-039 backup incomplete:** V2 cannot release. Backup is the minimum safety net.
- **US-039 restore incomplete but backup complete:** Ship only if release notes call restore `v2.0.1` and backup works; otherwise extend.
- **US-040 incomplete:** Ship reachable UI buttons and document missing shortcuts as v2.0.1.
- **US-040a incomplete:** Ship a settings dialog that opens/shows the YAML path; full viewer becomes v2.0.1.
- **US-041 perf fails:** If measured performance is still clinically usable, document actual budget and file v2.1 work; do not refactor late.
- **US-041 coverage below 85%:** Ship only after the coverage command works and the gap is documented.
- **US-042 incomplete:** V2 cannot release.

---

## Commit and Push Protocol

Each logical unit gets one commit:

1. `Added Sprint 10 V2 close-out scaffolding`
2. `Added hospitalization event service`
3. `Added hospitalization event capture UI`
4. `Added database backup service and dialog`
5. `Added database restore with confirmation and migration replay`
6. `Added keyboard shortcuts and settings inspection`
7. `Added performance and coverage hardening`
8. `Added V2 release notes, upgrade guide, demo script, and README`
9. `Added Sprint 10 summary and V2 release close-out`

After each commit:

```bash
git push origin master
```

After final close-out:

```bash
git tag v2-sprint10
git tag v2.0.0
git push origin master
git push origin v2-sprint10
git push origin v2.0.0
```

No commit message includes ticket refs or `Co-Authored-By claude`.

---

## Final V2 Release Checklist

- [ ] `docs/SPRINT_10_PLAN.md` matches actual Sprint 10 scope.
- [ ] `docs/PROJECT_LOG.md` has planning and close-out entries.
- [ ] `config/institution.defaults.yaml` and schema agree.
- [ ] N12 migration lands and is covered.
- [ ] Backup/restore works against real SQLite files.
- [ ] Settings viewer shows every config key.
- [ ] Shortcut help matches live registry.
- [ ] Coverage command is installed and runnable.
- [ ] Full test suite passes.
- [ ] Performance budgets pass or accepted measured values are documented.
- [ ] Release notes, upgrade guide, README, shortcuts doc, demo script, Sprint 10 summary, and V2 release summary are committed.
- [ ] `v2-sprint10` tag pushed.
- [ ] `v2.0.0` tag pushed.

When every checked item is true: **V2 ships.**
