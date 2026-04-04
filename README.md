# AC-T Chemotherapy Dashboard

Desktop application for tracking AC-T chemotherapy treatment progress. Built with Python and Tkinter.

## Features

- **Patient Management** — Add, view, and remove patients with treatment details
- **Treatment Timeline** — Visual 8-cycle timeline grouped into AC Phase (cycles 1-4) and T Phase (cycles 5-8)
- **Cycle Completion** — Record completion dates, dose percentages, modification reasons, and notes
- **Dose Modification Indicators** — Orange warning badge on cycles where dose was reduced below 100%
- **Current Cycle Status** — Live status label showing current cycle and phase
- **Labs Tracking** — Coming in Sprint 3

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python3 src/main.py
```

## Test Data

Generate 5 synthetic patients:
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
pytest
```

## Project Structure

```
src/
  main.py                        # App entry point
  models.py                      # Database models and CRUD
  database.py                    # Schema and connection
  utils/                         # Theme colours and font scale
  views/
    patient_list.py              # Patient list screen
    dashboard.py                 # Patient dashboard screen
    add_patient_dialog.py        # Add patient modal
    components/
      timeline.py                # Treatment timeline component
      cycle_dialog.py            # Cycle detail / edit dialogs
    dialogs/
      cycle_completion_dialog.py # Cycle completion form
docs/
  USER_GUIDE.md                  # End-user documentation
```

## User Guide

See [docs/USER_GUIDE.md](docs/USER_GUIDE.md) for full usage instructions.
