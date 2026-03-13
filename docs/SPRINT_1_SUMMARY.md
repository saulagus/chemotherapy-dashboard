# Sprint 1 Summary — AC-T Chemotherapy Dashboard

**Sprint dates:** 2026-03-07 — 2026-03-13
**Sprint goal:** Application launches, patients can be added and viewed, data persists

---

## Sprint Goal — Achieved

The application launches cleanly, displays a patient list, allows adding patients via a validated form, shows a patient dashboard with real data, and persists all data to SQLite across restarts and force-quits.

---

## Stories Completed — 20/20 points

| Story | Title | Points | Status |
|-------|-------|--------|--------|
| US-001 | Launch Application | 1 | Done |
| US-002 | Navigate Between Views | 2 | Done |
| US-003 | Graceful Error Handling | 2 | Done |
| US-004 | View Patient List | 2 | Done |
| US-005 | Add New Patient | 3 | Done |
| US-006 | Select Patient | 1 | Done |
| US-017 | SQLite Local Database | 2 | Done |
| US-018 | Patient Header | 2 | Done |
| US-019 | Local Data Storage | 1 | Done |
| US-020 | Auto-Save | 1 | Done |
| US-021 | Synthetic Data Generator | 2 | Done |
| US-022 | In-App Data Generator Access | 1 | Done |

**Velocity: 20 points in 10 days**

---

## What Was Built

- **Patient List** — Treeview with Patient ID, Name, Current Cycle, Protocol, Age, Diagnosis Date; alternating row colours; empty state
- **Add Patient Form** — Modal dialog with 6 fields, inline validation, duplicate ID detection
- **Remove Patient** — Confirmation dialog, instant list refresh
- **Patient Dashboard** — Header card with name, ID, protocol, start date; Treatment Timeline and Latest Labs placeholders
- **Dark Theme** — Full dark UI (`#1e1e1e`) with consistent palette across all views
- **SQLite Persistence** — Auto-commit on every write; data survives force-quit
- **Synthetic Data Generator** — CLI (`generate_test_data.py`) + in-app Developer menu; 5 profiles with varied cycle completion and lab trends

---

## Key Learnings

- `tk.Button` on macOS shows system gray regardless of styling — replaced with `tk.Label` + click binding
- `ttk.Style` requires `theme_use('default')` to allow full colour customisation on macOS
- Treeview row identification: store DB id in both `iid` and `tags` for reliable retrieval
- SQLite foreign keys don't cascade by default — delete in order: labs → cycles → patients
- macOS Tkinter menu bar replaces the default Python menus when `self.config(menu=menubar)` is called

---

## Demo Notes

Demo sequence (~10 min):
1. Launch app → patient list with 5 synthetic patients
2. Show empty state via Developer → Clear All Data
3. Add patient via form — show validation (duplicate ID, empty fields)
4. Double-click patient → dashboard with header data
5. Navigate back, click through multiple patients
6. Close and reopen — data persists

---

## What's Next — Sprint 2 Preview

Sprint 2 focuses on the **Treatment Timeline**:
- Visual cycle timeline (AC cycles 1-4, T cycles 5-8)
- Cycle status indicators (completed, pending, delayed)
- Dose modification display
- ANC trend chart
- Planned: 14 story points
