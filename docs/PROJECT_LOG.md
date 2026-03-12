# Project Log — AC-T Chemotherapy Dashboard

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
