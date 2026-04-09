# AC-T Chemotherapy Dashboard — User Guide

## Overview

The AC-T Chemotherapy Dashboard is a desktop application for tracking patient progress through AC-T (Adriamycin + Cyclophosphamide → Taxol) chemotherapy treatment. It provides a visual timeline of all 8 treatment cycles, supports recording cycle completions, and tracks dose modifications.

---

## Getting Started

Launch the application:
```bash
python3 src/main.py
```

The app opens on the **Patient List** screen, showing all patients currently in the system.

---

## Viewing the Patient List

The patient list displays:
- **Patient ID** — unique identifier (e.g. PT-001)
- **Name / Initials**
- **Current Cycle** — completed cycles out of total (e.g. 3/8)
- **Protocol** — Dose-Dense AC-T or Standard AC-T
- **Age** and **Diagnosis Date**

**Hover** over a row to highlight it. **Double-click** a row to open that patient's dashboard.

---

## Adding a Patient

1. Click **+ Add Patient** in the top-right corner
2. Fill in the required fields (marked with *)
   - Patient ID, Name / Initials, AC-T Start Date, Protocol
3. Optionally add Age and Diagnosis Date
4. Click **Save Patient**

Dates must be in **YYYY-MM-DD** format.

---

## Viewing the Treatment Timeline

Open a patient's dashboard by double-clicking their row in the patient list.

The **Treatment Timeline** shows all 8 cycles grouped into two phases:

| Phase | Cycles | Drug |
|---|---|---|
| AC Phase | 1 – 4 | Adriamycin + Cyclophosphamide |
| T Phase | 5 – 8 | Taxol (Paclitaxel) |

### Cycle States

| Appearance | Meaning |
|---|---|
| Gray box | Pending — not yet completed |
| Navy box with blue border | Current cycle |
| Green box with checkmark | Completed |
| Green box with orange ⚠ | Completed with dose reduction |

The **status label** above the timeline shows the current cycle and phase (e.g. "Current: Cycle 3 (AC Phase)"). When all 8 cycles are done it shows "Treatment Complete".

**Hover** over a completed cycle's checkmark to see the completion date and any dose modification details.

---

## Completing a Cycle

1. Click any **pending or current** cycle box on the timeline
2. The **Cycle Completion** dialog opens, pre-filled with today's date and 100% dose
3. Fill in the fields:
   - **Completion Date** — defaults to today (YYYY-MM-DD format)
   - **Dose Given** — select from 100%, 85%, 75%, 50%, or Custom
   - **Dose Reason** — required if dose is below 100%
   - **Notes** — optional, up to 500 characters
4. Click **Mark Complete** or press **Enter** to save
5. Press **Escape** or click **Cancel** to discard

After saving, the cycle box turns green and the timeline updates immediately.

---

## Recording a Dose Modification

1. Click the cycle box to open the Completion dialog
2. Change **Dose Given** to a value below 100%
3. A **Dose Reason** field appears (required):
   - Neutropenia
   - Neuropathy
   - Thrombocytopenia
   - Hepatotoxicity
   - Patient Tolerance
   - Physician Discretion
   - Other (enter custom reason in the text field)
4. Save as normal

Cycles with a dose reduction display an orange **⚠** badge in the top-right corner of their timeline box.

---

## Editing a Completed Cycle

1. Click a **completed** (green) cycle box
2. The **Cycle Detail** dialog shows the recorded data
3. Click **Edit** to modify the completion details
4. Save changes — the timeline refreshes automatically

---

## Removing a Patient

1. Select the patient row in the patient list (single click)
2. Click **- Remove Patient**
3. Confirm the deletion

This action is permanent and cannot be undone.

---

## Adding Lab Values

1. Open a patient's dashboard
2. Click **+ Add Labs** in the top-right navigation bar
3. Fill in the fields:
   - **Lab Date** — defaults to today (YYYY-MM-DD format, required)
   - **ANC** — Absolute Neutrophil Count in K/μL (required)
   - **WBC**, **Platelets**, **Hemoglobin** — optional
4. Click **Save Labs** or press **Enter** to save
5. Press **Escape** or click **Cancel** to discard

The **Latest Labs** panel and **ANC Trend Chart** refresh automatically after saving.

---

## Understanding the Latest Labs Panel

The **Latest Labs** panel (lower-left of the dashboard) shows the most recent lab draw for the current patient:

- **Date** and how many days ago it was recorded (e.g. "Mar 15, 2026 · 3 days ago")
- **ANC**, **WBC**, **Platelets**, and **Hemoglobin** values (optional fields only shown if recorded)

When no labs have been entered, the panel shows "No labs recorded yet" with a shortcut link to add labs.

---

## Understanding ANC Color Coding

ANC values are color-coded throughout the dashboard based on neutropenia thresholds:

| Color | ANC Range | Status |
|-------|-----------|--------|
| Green | ≥ 1.5 K/μL | Normal |
| Yellow | 1.0 – 1.49 K/μL | Mild Neutropenia |
| Orange | 0.5 – 0.99 K/μL | Moderate Neutropenia |
| Red | < 0.5 K/μL | Severe Neutropenia |

A color legend is shown at the bottom of the Latest Labs panel. The same colors are used in the ANC Trend Chart markers.

---

## Understanding the ANC Trend Chart

The **ANC Trend Chart** (lower-right of the dashboard) shows how ANC has changed over time:

- **X-axis** — lab dates, formatted automatically based on the date range
- **Y-axis** — ANC value in K/μL
- **Gray line** — the trend connecting all data points
- **Colored markers** — each point is colored by its ANC threshold category
- **Dashed red line** — the 1.5 K/μL threshold (lower edge of Normal range)

If no labs have been recorded, the chart shows "No lab data to display." If only one lab exists, it shows the single point with a note to add more labs to see a trend.

---

## Keyboard Shortcuts

| Key | Action |
|---|---|
| Enter | Save in completion dialog |
| Escape | Cancel / close dialog |
| Double-click | Open patient dashboard |
