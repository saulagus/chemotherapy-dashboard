# v1.1 Feature Backlog — AC-T Chemotherapy Dashboard

Compiled from stakeholder demo feedback (Demo #1 and Demo #2) plus pre-identified gaps.
Priority set after both demos; re-rank based on final stakeholder input.

---

## Priority Tiers

### High — Address First

| # | Feature | Source | Notes |
|---|---------|--------|-------|
| H1 | Edit / delete patients | Anticipated | No way to correct a patient record once saved |
| H2 | EHR integration | Demo feedback | Top request — pull lab values automatically |
| H3 | Alert system for low ANC | Anticipated | Visual or email alert when ANC drops below threshold |
| H4 | Toxicity tracking | Anticipated | Record nausea, neuropathy, fatigue alongside labs |
| H5 | Export to PDF / CSV | Demo feedback | Oncologist wants to print a one-page patient summary |

### Medium — Next Wave

| # | Feature | Source | Notes |
|---|---------|--------|-------|
| M1 | Multi-user support | Demo feedback | Requires server-side database (SQLite → PostgreSQL or similar) |
| M2 | Search / filter patient list | Anticipated | Useful as list grows beyond ~20 patients |
| M3 | Enhanced reporting / print view | Demo feedback | Cycle summary + labs on one printable page |
| M4 | Other chemotherapy regimens | Anticipated | CMF, FEC, TCHP — framework is extensible |
| M5 | Dose modification history view | Anticipated | Dedicated view showing all modifications with dates and reasons |

### Low — Future Consideration

| # | Feature | Source | Notes |
|---|---------|--------|-------|
| L1 | Web deployment | Anticipated | Flask or FastAPI backend; browser-based UI |
| L2 | Mobile access | Anticipated | Depends on web deployment first |
| L3 | CSV import | Anticipated | Bulk-import historical patient data |
| L4 | Audit trail | Anticipated | Log who changed what and when |
| L5 | Notification / reminder system | Anticipated | Alert when next cycle is due |
| L6 | Protocol comparison view | Anticipated | Side-by-side Dose-Dense vs Standard outcomes |

---

## Stakeholder-Requested Items (Demo #1)

*(Fill in after Demo #1 feedback form is reviewed)*

1.
2.
3.

## Stakeholder-Requested Items (Demo #2)

*(Fill in after Demo #2 feedback form is reviewed)*

1.
2.
3.

---

## Technical Debt

Items deferred from v1.0 that should be addressed before major v1.1 work:

| Item | Location | Impact |
|------|----------|--------|
| Hardcoded hex colors in dialogs | `cycle_completion_dialog.py`, `add_lab_dialog.py` | Visual inconsistency if theme changes |
| Hardcoded colors in labs panel | `latest_labs_panel.py` | Same |
| No logging / error reporting | App-wide | Hard to diagnose field issues |

---

## Architecture Notes for v1.1

- **Multi-user:** Replace SQLite with PostgreSQL; add user authentication layer; keep existing model classes, swap `database.py` connection logic
- **EHR integration:** HL7 FHIR R4 is the target standard; lab results via `DiagnosticReport` resource
- **Web deployment:** Keep current business logic in `models.py` and `utils/`; replace Tkinter views with a Flask/Jinja2 or React frontend
- **Other regimens:** Parameterize cycle count and phase structure in `Patient` model; move AC-T-specific constants out of hardcoded values
