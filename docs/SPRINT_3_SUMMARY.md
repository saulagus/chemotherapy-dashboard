# Sprint 3 Summary — Lab Value Management

## Sprint Goal
Lab values can be entered with validation, latest labs display prominently with ANC color coding, and ANC trend chart visualizes blood count patterns over time.

---

## Completed Stories

| Story | Title | Points | Status |
|-------|-------|--------|--------|
| US-013 | Add Lab Values | 3 | Done ✅ |
| US-014 | View Latest Lab Values | 1 | Done ✅ |
| US-015 | ANC Threshold Color Indicators | 1 | Done ✅ |
| US-016 | View Lab Trend Chart | 5 | Done ✅ |

**Velocity: 10 / 10 points delivered**

---

## Milestone

**M3: Labs Working — ACHIEVED ✅**

- Lab values can be entered with validation
- Latest labs displayed with date and age
- ANC color-coded by neutropenia threshold
- Trend chart visualizes ANC over time
- Chart updates automatically after new lab entry

---

## Key Accomplishments

- **Add Lab Dialog** — modal form with date, ANC (required), WBC/Platelets/Hemoglobin (optional), numeric validation, range warnings for clinically unusual values
- **Latest Labs Panel** — shows most recent lab draw with date, all values, empty state, and inline Add Labs shortcut
- **ANC Color Coding** — single `get_anc_status()` utility reused by both the panel and chart, ensuring color consistency across the dashboard
- **ANC Trend Chart** — matplotlib `FigureCanvasTkAgg` embedded in Tkinter; neutral trend line with per-point colored markers; dashed threshold line at 1.5 K/μL; handles empty, single-point, and 50+ lab datasets
- **Dashboard Integration** — chart and labs panel refresh together after every new lab entry via `_refresh_labs()`
- **Test Coverage** — 145 tests passing across all Sprint 3 modules

---

## Technical Highlights

- Integrated matplotlib with Tkinter using `FigureCanvasTkAgg` — figure background matches dashboard dark theme
- Color-coded markers implemented as individual `ax.plot` calls over a neutral line (cleaner than segmented colored lines)
- `AutoDateLocator` + `DateFormatter` handles date ranges from days to months automatically
- `anc_utils.py` as a single source of truth for thresholds — panel and chart both import from it

---

## Metrics

| Metric | Value |
|--------|-------|
| Planned points | 10 |
| Delivered points | 10 |
| Stories | 4 / 4 |
| Tests at sprint end | 145 |
| Bugs found in acceptance testing | 0 |

**Velocity trend:** Sprint 1: 20 pts · Sprint 2: 14 pts · Sprint 3: 10 pts
Decreasing point count reflects increasing complexity per story — expected and healthy.

---

## Lessons Learned

- Researching matplotlib theming upfront saved time — dark background required setting both `figure.facecolor` and `axes.facecolor` separately
- Color coding is the highest-value feature for clinical users — ANC status is immediately visible without reading numbers
- Keeping `anc_utils.py` independent of UI code prevented circular imports and made it trivially testable

---

## Next Sprint

**Sprint 4: Dashboard Integration & Polish (6 pts)**
- Final dashboard refinements
- Stakeholder demo preparation
- Lightest sprint by design — focus on quality and validation
