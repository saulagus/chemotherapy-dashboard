# Sprint 10 Plan — Polish & Reliability

**V2 · Weeks 23–24 · Days 51–59 of V2 · Final sprint before V2 release**

---

## Sprint Goal

V2 is feature-complete on Day 50. Sprint 10 makes it **production-ready**. By Day 59 the nurse can back up and restore her database without leaving the app, drive every common task from the keyboard, inspect every clinical threshold currently in force without opening a YAML file, and trust that the dashboard loads in under 200 ms with 100 patients on disk. The V2 release notes, upgrade guide, and demo script are written, the test suite is hardened to ≥85% coverage on `clinical/` and `services/`, and the codebase is ready to hand to a stakeholder.

**This is the closing sprint.** No new clinical surface lands. Every story protects what Sprints 5–9 built — from data loss, from regression, from "I can't find the setting," from the slow drift of a 60-day codebase.

**By Day 59 V2 ships. After Day 59 the next commit is a v2.1 / V3 ticket, not a V2 fix.**

---

## Stories

| Story | Title | Points | Status |
|-------|-------|--------|--------|
| US-039 | Backup / restore database | 3 | To Do |
| US-040 | Keyboard shortcuts & accessibility pass | 2 | To Do |
| US-040a | Settings inspection dialog (read-only config view) | 1 | To Do |
| US-041 | Performance & test-coverage hardening | 2 | To Do |
| US-042 | V2 documentation & release prep | 1 | To Do |

**Total: 9 story points · 9 development days**

---

## Sequencing

```
US-039 ─┐
US-040  ├── parallel-eligible warm-ups (Days 52–55)
US-040a ┘
                          │
US-041 ─► full-suite hardening pass — must follow all feature work (Days 56–57)
                          │
US-042 ─► release prep — must be last (Days 58–59)
```

- **US-039 first.** Highest-risk story; the SQLite online-backup API has edge cases worth exposing early. Restore path also touches the migration runner — gets attention while the day is fresh.
- **US-040 + US-040a in parallel windows.** Both are self-contained UX work; either can slot into a half-day around the larger stories.
- **US-041 mid-sprint.** Coverage and perf hardening must run *after* features land — measuring a moving target wastes the budget.
- **US-042 last.** Documentation freezes the V2 surface; doing it before the polish work invites rewrites.

---

## Dependencies (must be done)

| From | Artifact | Why Sprint 10 needs it |
|------|----------|-----------------------|
| Sprint 5 | Migration runner | US-039 restore path runs migrations forward against a restored DB if its schema version is older |
| Sprint 5 | Audit log | US-039 writes a `backup_created` / `restore_performed` row; US-040a is a read-only viewer over config (nothing to audit) |
| Sprint 5 | Institution config | US-040a is fundamentally a renderer over the loaded config tree |
| Sprint 6/7/8 | All thresholds in `config/institution.defaults.yaml` | US-040a must surface every value V2 reads — completeness is the test |
| Sprint 9 | `reports/` package | US-041 perf budget must include PDF render time; perf goals already encoded in Sprint 9 |
| V1 + everything since | Full feature set | US-040 keyboard pass cannot start until every dialog/button it must reach exists |
| Sprint 9 close | `v2-sprint9` tag green | If Sprint 9 carry-over is open, US-042 release prep cannot start |

If `v2-sprint9` is not tagged on Day 51, **fix that before touching Sprint 10 stories**. V2 documentation cannot describe a feature surface that is still moving.

---

## Pre-Sprint: Specialist & Stakeholder Review (Day 51 morning)

Sprint 10 is the only sprint where stakeholder review is more important than specialist review — clinical thresholds are frozen by now. Resolve on Day 51 or accept defaults.

| Question | Default | Decision | Source |
|----------|---------|----------|--------|
| Backup reminder cadence | every 7 days since last backup | ☐ Accept · ☐ Override | |
| Backup file location default | `~/Documents/ChemoDashboard/backups/` | ☐ Accept · ☐ Override | |
| Backup retention policy | keep last 10; warn before deleting older | ☐ Accept · ☐ Override | |
| Restore confirmation level | type institution name to confirm | ☐ Accept · ☐ Override | |
| Keyboard shortcut set | `Ctrl+N` new patient · `Ctrl+L` add labs · `Ctrl+F` search · `Ctrl+B` backup · `Ctrl+P` print · `Ctrl+E` export PDF · `Esc` close dialog · `?` shortcut help | ☐ Accept · ☐ Override | |
| macOS modifier | `Cmd` mirrored to `Ctrl` shortcuts | ☐ Accept · ☐ Override | |
| Settings dialog grouping | by sprint section (cardiotoxicity, toxicity, precycle, alerts, scheduling, reports) | ☐ Accept · ☐ Override | |
| Performance budget (P95 dashboard load, demo DB) | 200 ms | ☐ Accept · ☐ Override | |
| Test coverage target on `clinical/` and `services/` | 85% | ☐ Accept · ☐ Override | |
| Release notes audience | nurse + sysadmin (single doc, two sections) | ☐ Accept · ☐ Override | |

Deliverable: one YAML diff against `config/institution.defaults.yaml` committed Day 51, plus shortcut decisions captured in `docs/SHORTCUTS.md` (created Day 54).

---

## Architecture Additions

Sprint 10 adds **one service** (backup/restore), **one component** (settings viewer), and **one app-level binding layer** (keyboard shortcuts). Everything else is hardening and documentation.

```
src/
├── services/
│   └── backup.py                    ← NEW — SQLite online-backup, restore, retention
├── views/
│   ├── components/
│   │   └── settings_viewer.py       ← NEW — read-only config tree renderer
│   ├── dialogs/
│   │   ├── backup_dialog.py         ← NEW — "Back up now" + reminder banner
│   │   ├── restore_dialog.py        ← NEW — file picker + confirm-by-typing
│   │   ├── settings_dialog.py       ← NEW — hosts settings_viewer
│   │   └── shortcuts_help_dialog.py ← NEW — "?" key listing every shortcut
│   └── shortcuts.py                 ← NEW — central key-binding registry
docs/
├── RELEASE_NOTES_V2.md              ← NEW — what's new in V2 vs v1.0
├── UPGRADE_GUIDE_V1_TO_V2.md        ← NEW — DB migration path; backup-first instruction
├── SHORTCUTS.md                     ← NEW — keyboard reference
├── DEMO_SCRIPT_V2.md                ← NEW — supersedes V1 DEMO_SCRIPT.md for stakeholder demos
└── README.md                        ← updated — V2 feature list, install, run
tests/
├── test_backup_service.py           ← NEW — online backup, restore, retention, version mismatch
├── test_settings_viewer.py          ← NEW — every config key from defaults appears in viewer
├── test_shortcuts.py                ← NEW — registry maps to live handlers; collision detection
├── test_perf_dashboard_load.py      ← NEW — P95 budget assertion on demo DB
└── test_perf_pdf_render.py          ← NEW — Sprint 9 budgets re-asserted
```

**Patterns carried forward:**
- `services/backup.py` is the only module that opens a second SQLite connection (the backup target). Single transaction, audit row in the *source* DB.
- `views/shortcuts.py` is the single source of truth for key bindings — every dialog registers handlers here, not via scattered `bind()` calls.
- The settings viewer is a tree renderer over the *loaded* (Pydantic-validated) config, not the raw YAML file — overrides applied at runtime show through.
- Documentation files are plain Markdown; no doc-site dependency.

---

## Schema Migrations

**None.** Sprint 10 is read-only against the schema.

The backup story uses SQLite's online-backup API (`sqlite3.Connection.backup()`) — no schema change, no copy hack. The restore story may run *forward* migrations against a restored older-schema DB (using the Sprint 5 runner unchanged), but ships no new migration of its own.

If you find yourself adding a column for "release polish," stop. V2's data model is frozen on Day 50.

---

## Config Additions (`config/institution.defaults.yaml`)

```yaml
backup:
  default_directory: "~/Documents/ChemoDashboard/backups"
  reminder_days: 7
  retention_count: 10
  filename_pattern: "chemo_dashboard_{YYYY-MM-DD}_{HHmm}.db"
  warn_before_delete: true

restore:
  require_confirmation_text: institution_name   # 'institution_name' | 'literal_RESTORE'
  pre_restore_backup_filename: ".pre-restore-{YYYY-MM-DD-HHmm}.db"

shortcuts:
  enabled: true
  bindings:
    new_patient:    "Ctrl+N"
    add_labs:       "Ctrl+L"
    search:         "Ctrl+F"
    backup_now:     "Ctrl+B"
    print:          "Ctrl+P"
    export_pdf:     "Ctrl+E"
    close_dialog:   "Escape"
    shortcuts_help: "question"
  # macOS auto-mirrors Ctrl to Cmd at registration time

settings_viewer:
  enabled: true
  show_origin: true              # show whether each value is default or override
  group_by: sprint               # 'sprint' | 'flat'

performance:
  budgets_ms:
    dashboard_load_p95: 200
    pdf_oncologist_p95: 800
    pdf_print_dashboard_p95: 600
    csv_labs_p95: 200
    cycle_save_p95: 150
```

**Sources of truth, restated:**
- Every existing config key from Sprints 5–9 stays put. Sprint 10 only adds the four new sections above.
- Performance budgets are codified in YAML so the perf tests in `test_perf_*.py` read the same numbers the docs cite — one source.

---

## Day-by-Day Plan

### DAY 51 — Sprint planning, stakeholder review, scaffolding
**Morning (~2h)** — Stakeholder/specialist review of the Day-51 question table. Confirm `v2-sprint9` tag is green on master. Confirm full test suite passes against demo DB.
**Afternoon (~3h)** — Add `backup:`, `restore:`, `shortcuts:`, `settings_viewer:`, and `performance:` blocks to `config/institution.defaults.yaml`. Scaffold `src/services/backup.py`, `src/views/shortcuts.py`, four new dialog modules, settings_viewer component. Empty test files. Verify scaffolds wire into the app without breaking startup.
**Commit:** `Added Sprint 10 polish and reliability scaffolding`

### DAY 52 — US-039 part 1: backup service + dialog
- Implement `services/backup.py`:
  - `create_backup(conn, target_dir, config) -> BackupResult` — uses `sqlite3.Connection.backup()` to write a portable `.db` to `target_dir/{filename_pattern}`. Writes one `audit_log` row with `action='backup_created'` and details `{path, size_bytes}`.
  - `list_backups(target_dir, config) -> list[BackupFile]` — sorted newest-first; reads filename pattern.
  - `prune_old_backups(target_dir, config) -> list[Path]` — enforces `retention_count`; warns (does not delete) if `warn_before_delete: true`.
  - `BackupResult(path, size_bytes, schema_version, audit_id)`.
- `views/dialogs/backup_dialog.py`: target directory picker (default from config), "Back up now" button, post-backup toast with file path, copy-path-to-clipboard button.
- Reminder banner on dashboard top: shows when last backup > `reminder_days` ago. Dismissible per session.
- Tests: backup writes a file, backup file is a valid SQLite DB, backup is independently openable (no app deps), retention pruning math, audit row written.
**Commit:** `Added database backup service and dialog`

### DAY 53 — US-039 part 2: restore + version-aware migration replay
- `services/backup.read_schema_version(path) -> int` — opens target DB read-only, reads `migration_history.max(version)`.
- `services/backup.restore(target_path, current_db_path, config) -> RestoreResult`:
  - Renames current DB to `pre_restore_backup_filename` (no silent overwrite).
  - Copies the chosen backup into place.
  - Reads its schema version; if older than current code's expected version, runs forward migrations via the Sprint 5 runner.
  - Writes one `audit_log` row with `action='restore_performed'` and details `{from_path, pre_restore_path, schema_version_before, schema_version_after}`.
- `views/dialogs/restore_dialog.py`:
  - File picker for the backup .db.
  - Pre-flight: shows backup's schema version, current code's expected version, "will run N migrations" hint.
  - Confirmation: type institution name (or literal `RESTORE` if so configured) — button stays disabled until typed text matches.
- Tests: round-trip — back up → modify DB → restore → assert original state. Older-schema restore — fixture .db at v0007 restored against v0010 code triggers 3 forward migrations and lands clean. Cancel-mid-restore leaves the original DB untouched.
**Commit:** `Added database restore with confirmation and migration replay`
**US-039 DONE — 3 pts**

### DAY 54 — US-040: keyboard shortcuts + accessibility pass
- Implement `views/shortcuts.py`:
  - `Shortcuts` registry — singleton bound to root Tk window at app start.
  - `register(action_name: str, handler: Callable)` — handlers register themselves; binding string comes from config. Collision raises at registration time.
  - macOS detection: at registration, `Ctrl+X` mirrors to `Cmd+X` (`<Command-x>`) so the same config key works cross-platform.
- Wire shortcuts: `Ctrl+N` (new patient dialog), `Ctrl+L` (add labs), `Ctrl+F` (focus patient search box), `Ctrl+B` (backup dialog), `Ctrl+P` (print), `Ctrl+E` (export PDF), `Esc` (close topmost dialog), `?` (open shortcut help dialog).
- `views/dialogs/shortcuts_help_dialog.py`: rendered from the same registry — adding a new shortcut requires zero changes to this dialog.
- **Accessibility pass:** every dialog has a sensible tab order; primary action is the default button (Enter triggers); `Esc` cancels every dialog; focus visible on every focused widget. Manual checklist in `docs/SHORTCUTS.md`.
- Write `docs/SHORTCUTS.md`: table of every shortcut + the action it invokes.
- Tests: registry collision detection; mac-mirroring; help dialog enumerates all registered shortcuts.
**Commit:** `Added keyboard shortcuts registry and accessibility pass`
**US-040 DONE — 2 pts**

### DAY 55 — US-040a: settings inspection dialog
- Implement `views/components/settings_viewer.py`:
  - Tree renderer over the loaded Pydantic config object — keys grouped per `settings_viewer.group_by` (default `sprint`: cardiotoxicity, toxicity, precycle, alerts, scheduling, labs, reports, backup, shortcuts, performance).
  - Each row: key path, current value, origin (`default` or `override`) when `show_origin: true`.
  - Read-only — no edit affordances. Copy-to-clipboard on any value.
  - Search box at top filters by key path substring.
- `views/dialogs/settings_dialog.py`: hosts the viewer; "Open YAML in editor" button that calls `subprocess.run(["open", path])` (macOS) / `os.startfile()` (Windows). On failure, falls back to "show file path" toast.
- Add "Settings" item to the dashboard menu/help button (no top menu bar exists in V1; expose via the existing help button or a small gear icon top-right).
- **Completeness test:** assert every key in `config/institution.defaults.yaml` appears somewhere in the rendered tree. This is the fix-once-and-stay-fixed test — adding a new config key in a future sprint will fail this test until the viewer is updated (which is automatic, since it walks the config tree, but the test catches `enabled: false` regressions).
- Tests: completeness, search filtering, override-vs-default labelling on a fixture config with one override applied.
**Commit:** `Added read-only settings inspection dialog`
**US-040a DONE — 1 pt**

### DAY 56 — US-041 part 1: performance hardening
- Generate a 100-patient × 8-cycle × 20-lab synthetic DB via `generate_test_data.py` (extended if needed). Commit as `tests/fixtures/perf_100p.db` (or generate-on-demand if size is a concern).
- Implement `tests/test_perf_dashboard_load.py`:
  - Asserts P95 dashboard load (open patient → header + timeline + labs + cardiotoxicity + toxicity + checklist input gather + status indicator + low-ANC banner) < `performance.budgets_ms.dashboard_load_p95`.
  - Asserts P95 cycle save < `cycle_save_p95`.
- Implement `tests/test_perf_pdf_render.py`:
  - Re-asserts Sprint 9 budgets (oncologist, print-dashboard, CSV) on the 100-patient fixture.
- Profile any regression with `cProfile`; fix the top-3 hotspots only — Sprint 10 is not refactor week. Common wins likely:
  - Index missing on a frequent join (audit `EXPLAIN QUERY PLAN`).
  - Per-row checklist-input gathering on the patient list (already explicitly out-of-scope per Sprint 8 — verify it stayed that way).
  - Repeated config-tree walks at render time → cache the loaded config in the app singleton.
**Commit:** `Added performance test suite and hotspot fixes`

### DAY 57 — US-041 part 2: coverage hardening + regression sweep
- Run `pytest --cov=src/clinical --cov=src/services --cov-report=term-missing`.
- Identify modules below the 85% target. Add tests for uncovered branches — error paths, soft-delete edge cases, config-override edge cases. **No code changes for coverage's sake** — if a branch is unreachable, mark it with `# pragma: no cover` and explain why in a comment (this is one of the few comments that earns its keep).
- Final regression sweep: full test suite passes; perf budgets passing; manually walk the demo script for every sprint's killer feature on the demo DB.
- Lint pass (existing tooling — do not introduce a new linter this sprint).
**Commit:** `Added coverage hardening to clinical and services layers`
**US-041 DONE — 2 pts**

### DAY 58 — US-042 part 1: release notes + upgrade guide + README + demo script
- Write `docs/RELEASE_NOTES_V2.md`:
  - Header: version, release date, summary paragraph.
  - **What's new** section grouped by clinical theme (Data integrity & audit · Cardiotoxicity safety · Toxicity tracking · Workflow & alerts · Reporting & export · Polish & reliability) with the sprint number each block came from.
  - **Configuration changes** — every new top-level YAML section (audit, cardiotoxicity, toxicity, scheduling, labs, precycle, alerts, reports, exports, backup, restore, shortcuts, settings_viewer, performance).
  - **Migrations** — list 0001 through final, one line each.
  - **New dependencies** — pydantic (Sprint 5), reportlab (Sprint 9). Pinned versions.
  - **Known gaps** — anything explicitly deferred to V3, copied from each sprint's *Out of Scope* sections (consolidated, not duplicated).
- Write `docs/UPGRADE_GUIDE_V1_TO_V2.md`:
  - Step 1: back up the v1.0 .db file (tar/cp).
  - Step 2: install V2 deps (`pip install -r requirements.txt`).
  - Step 3: launch app — migrations run automatically; existing data preserved.
  - Step 4: review `docs/SHORTCUTS.md` and the new Settings dialog.
  - Rollback: stop V2, restore the v1.0 backup, downgrade requirements.
- Update `README.md`: new feature bullets, install/run section unchanged or trivially updated, link to release notes + upgrade guide + demo script + shortcuts.
- Write `docs/DEMO_SCRIPT_V2.md`: 15-minute walkthrough hitting one feature per sprint. Supersedes the V1 `DEMO_SCRIPT.md` (which stays in repo for historical reference, marked V1).
**Commit:** `Added V2 release notes, upgrade guide, demo script, and README`

### DAY 59 — US-042 part 2: final demo + V2 release tag
- Final demo walkthrough on the demo DB following `docs/DEMO_SCRIPT_V2.md` end-to-end. One bug → one fix → one commit; if more than one bug surfaces, document in `docs/BACKLOG_V2_1.md` and ship.
- Write `docs/SPRINT_10_SUMMARY.md` matching the Sprint 9 summary shape.
- Write `docs/V2_RELEASE_SUMMARY.md` — single file rolling up Sprints 5–10 (point totals, story counts, test counts, perf numbers, ship date). This is the artifact the next stakeholder demo opens with.
- Update `docs/PROJECT_LOG.md` with a V2 close-out entry.
- Tag `v2.0.0` (release tag) in addition to `v2-sprint10` (sprint tag).
**Commit:** `Added Sprint 10 summary and V2 release close-out`
**US-042 DONE — 1 pt**

---

## Story Acceptance Criteria

### US-039 — Backup / restore database (3 pts)
- [ ] `services/backup.create_backup()` uses SQLite online-backup API (not a file copy)
- [ ] Backup file is a valid, openable SQLite DB without the app present
- [ ] Backup writes one `backup_created` audit row with path + size
- [ ] Reminder banner appears when last backup > `reminder_days` ago; dismissible per session
- [ ] Restore renames current DB to `pre_restore_backup_filename` before overwriting (no silent loss)
- [ ] Restore detects schema version of incoming DB; runs forward migrations if older
- [ ] Restore confirmation requires typing institution name (or configured literal)
- [ ] Restore writes one `restore_performed` audit row with version-before/after
- [ ] Round-trip test: backup → mutate → restore → original state recovered
- [ ] Older-schema restore test: v0007 fixture restored under v0010 code lands at v0010
- [ ] Coverage on `services/backup.py` ≥ 90%

### US-040 — Keyboard shortcuts & accessibility pass (2 pts)
- [ ] Central `Shortcuts` registry; collision raises at registration
- [ ] All bindings sourced from `shortcuts.bindings` config — zero hardcoded keysym strings outside the registry
- [ ] macOS auto-mirroring of Ctrl → Cmd at registration time
- [ ] All eight default shortcuts wired: new patient, add labs, search, backup, print, export PDF, close, help
- [ ] `?` opens a help dialog enumerating every registered shortcut
- [ ] Every dialog: Enter → primary action; Esc → cancel
- [ ] Tab order sane on every dialog (manual checklist in `docs/SHORTCUTS.md`)
- [ ] `docs/SHORTCUTS.md` shipped and current

### US-040a — Settings inspection dialog (1 pt)
- [ ] Read-only tree renderer over the loaded (Pydantic-validated) config
- [ ] Grouping per `settings_viewer.group_by`
- [ ] `show_origin: true` labels each value as `default` or `override`
- [ ] Search-by-key-path filter
- [ ] "Open YAML in editor" button with graceful fallback
- [ ] Completeness test: every key in `institution.defaults.yaml` appears in the rendered tree
- [ ] No edit affordances — read-only by contract this sprint (V3 may add edit)

### US-041 — Performance & test-coverage hardening (2 pts)
- [ ] 100-patient × 8-cycle × 20-lab fixture available (committed or generate-on-demand)
- [ ] P95 dashboard load < `performance.budgets_ms.dashboard_load_p95` (default 200 ms)
- [ ] P95 cycle save < `cycle_save_p95` (default 150 ms)
- [ ] Sprint 9 PDF/CSV budgets re-asserted on 100-patient fixture
- [ ] Coverage on `src/clinical/` ≥ 85%; on `src/services/` ≥ 85%
- [ ] No new dependencies added in the name of perf or coverage
- [ ] All hotspot fixes scoped to indexes, caching, or query consolidation — no architectural rewrites

### US-042 — V2 documentation & release prep (1 pt)
- [ ] `docs/RELEASE_NOTES_V2.md` — every sprint's clinical contribution, every config addition, every migration, every new dep
- [ ] `docs/UPGRADE_GUIDE_V1_TO_V2.md` — backup-first instruction, step-by-step path, rollback documented
- [ ] `README.md` — V2 feature bullets, links to release notes / upgrade / demo / shortcuts
- [ ] `docs/SHORTCUTS.md` — current and complete (built in US-040)
- [ ] `docs/DEMO_SCRIPT_V2.md` — 15-min walkthrough, one feature per sprint
- [ ] `docs/V2_RELEASE_SUMMARY.md` — single rollup artifact for next stakeholder demo
- [ ] `v2.0.0` release tag pushed

---

## Success Criteria (sprint-level)

- [ ] All five stories merged to master, tagged `v2-sprint10` and `v2.0.0`
- [ ] Coverage on `src/clinical/` and `src/services/` ≥ 85%; coverage on `src/services/backup.py` ≥ 90%
- [ ] No regressions in Sprint 5/6/7/8/9 test suites
- [ ] All performance budgets in `performance.budgets_ms` met at P95 on 100-patient fixture
- [ ] Demo walkthrough (Day 59) completes without manual DB poking, hitting one feature per sprint
- [ ] Zero magic numbers in code — every threshold, cadence, mode, lookback, budget, shortcut, filename pattern resolves through config
- [ ] No new schema migrations shipped this sprint
- [ ] No new top-level dependencies shipped this sprint
- [ ] Settings dialog renders every key in `institution.defaults.yaml`
- [ ] V2 release artifacts (notes, upgrade guide, README, demo script, shortcuts ref, release summary) all current

---

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Restore path corrupts the live DB on a partial copy | High | Pre-restore rename of current DB to `.pre-restore-*.db` before any write; restore is overwrite-then-validate; failed validate restores from the rename. Tested with cancel-mid-restore. |
| Older-schema restore exposes a migration that's never been run forward against real-shape data | Medium | Sprint 5 migration runner already round-trips up/down on every migration in CI. Add an explicit fixture at v0007 schema for the restore test — that's the test that catches it. |
| Keyboard-shortcut collisions emerge late, only when a user discovers them | Medium | Registry raises at registration time, not at keypress time — collisions are caught at app start, in tests. |
| macOS Cmd-mirroring breaks on a Tk version we haven't tested | Low | Manual smoke on macOS Day 54; documented as macOS-tested in release notes; Windows/Linux Ctrl path unchanged. |
| Settings viewer drifts from config as future sprints add keys | Medium | Completeness test walks the live config tree — adding a key auto-appears; the test catches accidental disablement. |
| Perf budgets fail on Day 56 and burn the rest of the sprint | Medium | Budgets are codified in YAML, not in test code — adjusting a budget is a one-line config change with a justification in the commit. Don't chase a budget into a refactor; document the regression and ship. |
| Coverage chase introduces tests of trivial branches with no clinical value | High | Coverage delta this sprint targets *clinical-relevant* branches (error paths in services, soft-delete edges, override paths). `# pragma: no cover` is acceptable for unreachable defensive branches. |
| Documentation drifts during the sprint as features change | Low | Docs land Day 58, after all features. The V2 surface is frozen by Day 57. |
| The "one bug → one fix" rule on Day 59 turns into many | Medium | Hard cap: any bug found on Day 59 that isn't a release-blocker goes to `docs/BACKLOG_V2_1.md` and ships there. Release-blocker = data loss, security, or "the demo doesn't work." |
| `v2.0.0` tag pushed before sprint summary written | Low | Order of Day-59 commit list: summary first, tag last. |
| Scope-creep: "while we're polishing, can we…" | High | Every story above ends in a feature freeze. Sprint 10 ends V2; the next ticket is V2.1. |

---

## Out of Scope (reject on sight)

- Editable settings dialog → V3 (V2 is read-only inspection by design)
- Per-user shortcut customization → V3
- Encrypted backups (SQLCipher) → V3 (V2 ships plain `.db` per V2 plan)
- Cloud / remote backup destinations → V3
- Automatic scheduled backups (without user click) → V3 (single-user app; manual + reminder is V2 contract)
- Multi-user authentication / role-based UI → V3
- Localization / internationalization → V3
- Theming / dark mode → V3
- New clinical thresholds, vocabularies, or rules → V3
- Refactor of any `clinical/` or `services/` module beyond targeted hotspot fixes → V2.1 if justified
- New chart types → V3
- Web/mobile build → V3
- Any additional regimen support (TCHP, FEC, weekly paclitaxel) → V3
- Test-framework changes (pytest plugins, alternative coverage tools) → V3 if motivated

If any of the above surfaces mid-sprint, log to `docs/BACKLOG_V2_1.md` or `docs/BACKLOG_V3.md` and move on.

---

## Definition of Done (per story)

1. Code committed with single-line `Added ...` message
2. Unit + integration tests on every new module
3. Config values, shortcuts, paths, budgets read from YAML, not hardcoded
4. Audit entries written for backup and restore
5. Component / dialog rendered cleanly at 1920×1080 and 1024×768
6. macOS smoke test passed on the touched surface; cross-platform notes captured if relevant
7. No regression in Sprint 5/6/7/8/9 test suites
8. Entry in `PROJECT_LOG.md` for the day

---

## Post-Sprint Carry-Over Protocol

If any story is incomplete at end of Day 59:

- **US-039 incomplete (backup works, restore incomplete)** → ship backup; restore lands as a v2.0.1 patch within one week. Backup-only is a usable safety net; restore-only is not.
- **US-039 incomplete (backup incomplete)** → **V2 cannot release.** A V2 without working backup is a regression on the implicit V1 contract (the user could always file-copy the .db). Extend by 1–2 days.
- **US-040 incomplete** → ship the shortcuts that are wired; document the rest in `docs/SHORTCUTS.md` as v2.0.1. Keyboard polish is non-blocking.
- **US-040a incomplete** → ship a stub Settings dialog that just opens the YAML in an editor; full read-only viewer lands as v2.0.1.
- **US-041 incomplete (perf budgets fail)** → adjust the budget in YAML to the measured number, document the regression in release notes, file a v2.1 ticket. Do not chase perf into an architectural rewrite.
- **US-041 incomplete (coverage below 85%)** → ship; coverage delta is a v2.1 ticket.
- **US-042 incomplete** → **V2 cannot release.** Without release notes and upgrade guide, V1 users have no path forward. Extend by 1 day if needed.

**This is the last carry-over protocol of V2.** After Day 59, the next ticket is v2.0.1 (patch), v2.1 (point release), or V3 — never "V2 part 2."

---

## V2 Release Checklist (Day 59, after US-042)

- [ ] All Sprint 10 stories acceptance-criteria green
- [ ] Full test suite green: V1 + Sprints 5–10
- [ ] Performance budgets green at P95 on 100-patient fixture
- [ ] `requirements.txt` pinned and installable on a clean venv
- [ ] `docs/RELEASE_NOTES_V2.md` reviewed against actual shipped surface
- [ ] `docs/UPGRADE_GUIDE_V1_TO_V2.md` walked through manually with a v1.0 backup
- [ ] `docs/SHORTCUTS.md` matches live registry
- [ ] `docs/DEMO_SCRIPT_V2.md` walked end-to-end on demo DB
- [ ] `docs/V2_RELEASE_SUMMARY.md` written
- [ ] `docs/PROJECT_LOG.md` close-out entry added
- [ ] `v2-sprint10` tag pushed
- [ ] `v2.0.0` release tag pushed

When every box is checked: **V2 ships.**
