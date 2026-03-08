# Project Log — AC-T Chemotherapy Dashboard

---

## 2026-03-08 — Sprint 1 Day 4

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
- Day 5: Implement patient list (Treeview, columns: ID/Name/Cycle/Status, empty state, Add Patient button, click-to-navigate, test empty + manual data)
- Day 6: Add Patient form (ID, name, start date, protocol, validation, duplicate check, save/cancel, refresh list)
- Day 7: Patient selection, pass patient_id to dashboard, display patient name in header, test full List→Dashboard→Back flow
- Day 8: Verify auto-save, test persistence across restarts, handle DB errors, cycle/lab CRUD + tests
- Day 9: generate_test_data.py — 5 synthetic patients, varied cycles/labs, CLI flag --patients N
- Day 10: Sprint 1 review — bug fixes, self-demo against acceptance criteria, retrospective, tag v0.1-m1

---

## 2026-03-07 — Day 0.2 & Sprint 1 (Days 1-3)

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
- Day 4: Frame navigation, `patient_list.py` view, `dashboard.py` view, error handling
- Day 5: Patient list with Treeview, Add Patient button, click-to-navigate, test with empty DB

---

## 2026-03-07 — Day 0.1 & 0.2 (Setup)

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
