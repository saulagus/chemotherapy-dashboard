# Project Summary — AC-T Chemotherapy Dashboard v1.0

---

## Overview

A desktop application for tracking patient progress through AC-T (Adriamycin + Cyclophosphamide → Taxol) chemotherapy treatment. Built with Python 3.12 and Tkinter; SQLite database; matplotlib for ANC trend visualization.

**Timeline:** March 6, 2026 → April 15, 2026 — 6 weeks

---

## Milestones

| Milestone | Target | Status |
|-----------|--------|--------|
| M1: Foundation Complete | Day 10 | ✅ Done |
| M2: Timeline Working | Day 20 | ✅ Done |
| M3: Labs Working | Day 30 | ✅ Done |
| M4: MVP Feature Complete | Day 33 | ✅ Done |
| M5: MVP Validated | Day 40 | ✅ Done |

---

## Velocity

| Sprint | Days | Story Points | Focus |
|--------|------|-------------|-------|
| Sprint 1 | 1–10 | 20 pts | Foundation — patient CRUD, navigation, database |
| Sprint 2 | 11–20 | 14 pts | Timeline — 8-cycle tracker, cycle completion, dose modifications |
| Sprint 3 | 21–30 | 10 pts | Labs — lab entry, latest labs panel, ANC color coding, trend chart |
| Sprint 4 | 31–40 | 6 pts | Integration — unified dashboard, patient header, testing, polish, demos |
| **Total** | **40** | **50 pts** | |

---

## Features Delivered

- Patient management — add, view, remove patients with ID, protocol, start date
- 8-cycle treatment timeline grouped into AC Phase (1–4) and T Phase (5–8)
- Cycle completion recording — date, dose percentage, modification reason, notes
- Dose modification indicators — orange ⚠ badge on reduced-dose cycles with tooltip
- Lab value tracking — ANC, WBC, Platelets, Hemoglobin per visit
- ANC color coding — four-tier neutropenia threshold system across all displays
- ANC trend chart — matplotlib line chart with threshold line and color-coded markers
- Unified dashboard — all components on one screen, no scrolling required
- Patient header — name, ID, protocol, start date; back navigation; Add Labs button

---

## Test Coverage

214 tests across 11 test files:

| File | Coverage |
|------|---------|
| `test_database.py` | Schema, connection, constraints |
| `test_models.py` | CRUD operations, data integrity |
| `test_dialog_validation.py` | Input validation rules |
| `test_save_flow.py` | End-to-end save workflows |
| `test_lab_entry.py` | Lab dialog validation |
| `test_latest_labs_panel.py` | Panel rendering, empty states |
| `test_anc_utils.py` | ANC threshold logic |
| `test_anc_trend_chart.py` | Chart data loading, rendering |
| `test_patient_header.py` | Header display, date formatting |
| `test_e2e_integration.py` | 8-phase full workflow (40 tests) |
| `test_performance.py` | Timing assertions, edge cases (14 tests) |

---

## Performance

| Operation | Target | Actual |
|-----------|--------|--------|
| Dashboard load | < 1s | < 0.1s |
| `get_all_patients()` 20 patients | < 100ms | 0.1ms |
| `get_latest_lab()` | < 100ms | 0.0ms |
| `chart.refresh()` 20 lab draws | < 500ms | 26.4ms |

---

## Stakeholder Sign-Off

| Demo | Stakeholder | Date | Approval |
|------|-------------|------|---------|
| Demo #1 | _______________ | 2026-04-14 | ☐ Approved  ☐ Conditional  ☐ Not approved |
| Demo #2 | _______________ | 2026-04-15 | ☐ Approved  ☐ Conditional  ☐ Not approved |

**Overall MVP Status:** ☐ APPROVED  ☐ NEEDS WORK

---

## Known Limitations (v1.0)

- Single-user desktop app — no multi-user or server-side database
- AC-T protocol only — no support for other chemotherapy regimens
- No EHR integration — data is entered manually
- No export — no PDF, CSV, or print view
- Local data only — SQLite file on the local machine, no network sync

All limitations are documented in `docs/DEMO_SCRIPT.md` anticipated Q&A and flagged for v1.1 consideration.

---

## Repository

- **Branch:** `master`
- **Release tag:** `v1.0.0`
- **Commits:** 60+
- **Languages:** Python 3.12
- **Dependencies:** Tkinter (stdlib), matplotlib, pytest
