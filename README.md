# AC-T Chemotherapy Dashboard

Desktop application for tracking patient progress through AC-T chemotherapy treatment. Built with Python and Tkinter.

## Features

- **Patient Management** — Add, view, and remove patients with ID, protocol, and treatment start date
- **Treatment Timeline** — Visual 8-cycle timeline grouped into AC Phase (cycles 1–4) and T Phase (cycles 5–8)
- **Cycle Completion** — Record completion dates, dose percentages, modification reasons, and notes
- **Dose Modification Indicators** — Orange ⚠ badge on cycles where dose was reduced below 100%
- **Current Cycle Status** — Live status label showing current cycle and phase
- **Lab Value Tracking** — Record ANC, WBC, Platelets, and Hemoglobin per visit
- **ANC Color Coding** — Color-coded neutropenia thresholds on all lab displays
- **ANC Trend Chart** — Matplotlib line chart with threshold line and color-coded markers
- **Unified Dashboard** — All components visible on one screen: header, timeline, labs, chart

## ANC Color Key

| Color | ANC Range | Status |
|-------|-----------|--------|
| Green | ≥ 1.5 K/μL | Normal |
| Yellow | 1.0 – 1.49 K/μL | Mild Neutropenia |
| Orange | 0.5 – 0.99 K/μL | Moderate Neutropenia |
| Red | < 0.5 K/μL | Severe Neutropenia |

## Setup

```bash
cd chemotherapy-dashboard
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python3 src/main.py
```

## Test Data

Generate 5 synthetic patients with varied treatment profiles:

```bash
python3 generate_test_data.py
```

Clear all data and regenerate:

```bash
python3 generate_test_data.py --clear --patients 5
```

Or use the **Developer** menu in the app menu bar.

## Tests

```bash
pytest tests/ -v
```

214 tests across database, models, validation, components, integration, and performance.

## Project Structure

```
src/
  main.py                           # App entry point and navigation
  models.py                         # Patient, Cycle, Lab dataclasses + CRUD
  database.py                       # SQLite schema and connection
  utils/
    __init__.py                     # Dark theme palette and font constants
    anc_utils.py                    # ANC threshold logic (shared by panel + chart)
  views/
    patient_list.py                 # Patient list screen
    dashboard.py                    # Unified patient dashboard
    add_patient_dialog.py           # Add patient modal
    components/
      patient_header.py             # Patient identity header component
      timeline.py                   # Treatment timeline component
      latest_labs_panel.py          # Latest lab values panel
      anc_trend_chart.py            # ANC trend chart (matplotlib)
      cycle_dialog.py               # Cycle detail / edit dialog
    dialogs/
      cycle_completion_dialog.py    # Cycle completion form
      add_lab_dialog.py             # Lab entry form
docs/
  USER_GUIDE.md                     # End-user documentation
  DEMO_SCRIPT.md                    # Stakeholder demo script
  FEEDBACK_FORM.md                  # Stakeholder feedback form
  SPRINT_4_PLAN.md                  # Sprint 4 planning document
  PROJECT_LOG.md                    # Development log
tests/
  test_database.py
  test_models.py
  test_dialog_validation.py
  test_save_flow.py
  test_lab_entry.py
  test_latest_labs_panel.py
  test_anc_utils.py
  test_anc_trend_chart.py
  test_patient_header.py
  test_e2e_integration.py
  test_performance.py
data/
  dashboard.db                      # SQLite database (auto-created on first run)
generate_test_data.py               # CLI tool for synthetic data
```

## User Guide

See [docs/USER_GUIDE.md](docs/USER_GUIDE.md) for full usage instructions.
