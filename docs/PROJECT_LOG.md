# Project Log — AC-T Chemotherapy Dashboard

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
- Test IDE configuration
- Quick Tkinter test
- Review Sprint 1 stories
- Begin Sprint 1
