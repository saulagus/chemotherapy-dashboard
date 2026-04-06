# Project Log — AC-T Chemotherapy Dashboard

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
