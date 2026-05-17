# Sprint 9 Summary - Reporting & Export

**Dates:** 2026-05-17 restart and close-out  
**Points delivered:** 9 pts (US-035: 4, US-036: 2, US-037: 1, US-038: 2)  
**Tests:** 834 passing - 0 regressions  
**Tag:** `v2-sprint9`

---

## What Was Built

### US-035 - PDF Patient Summary Export (4 pts)

Reports layer:
- `reports/data.py` now assembles `PatientReportData` with header details, latest cycle, dose modifications, cumulative dose, LVEF, labs, lab history, toxicity summary, checklist state, recent audit rows, and G-CSF marker dates.
- `reports/pdf_oncologist.py`, `reports/pdf_pcp.py`, and `reports/pdf_patient.py` render deterministic ReportLab PDFs from `PatientReportData`.
- Oncologist PDF embeds the ANC trend chart using report lab history.

Export service and dialog:
- `services/exports.py` writes audience-specific PDF files and records `export_pdf` audit rows.
- `ExportPdfDialog` exposes enabled audiences from config and uses a save-as flow.

Tests:
- Added report data, PDF template, and export service coverage.
- PDF tests assert valid PDF bytes and byte-stable repeated renders.

---

### US-036 - Dose Modification History View (2 pts)

Service:
- `services/dose_modifications.py` returns one row per cycle with `dose_percent < 100`, including cycle, date, agent, dose percent, prior percent, reason, actor, and cycle id.
- `reports/data.py` reuses the same service for latest-cycle and full-patient dose modification history.

UI:
- `DoseModHistoryPanel` is mounted in the dashboard as a collapsible panel beneath cardiotoxicity.
- Empty state and sort state are covered by existing panel tests.

Tests:
- `test_dose_modifications_service.py` verifies empty state, multi-cycle history, update-derived prior percent, reason, actor, and cycle-specific lookup.

---

### US-037 - CSV Lab Export (1 pt)

Reports layer:
- `reports/csv_labs.py` writes configured columns through stdlib `csv`.
- Date filtering is applied in SQL.
- `gcsf_within_7d` is computed from G-CSF administration windows.
- Soft-delete filtering is supported when the labs table includes a `deleted_at` column; current schema hard-deletes labs.

Export service and dialog:
- `services/exports.py` writes CSV files and records `export_csv` audit rows.
- `ExportCsvDialog` supports optional from/to dates and config-driven filename defaults.

Tests:
- Added CSV round-trip, date range, G-CSF overlap, soft-delete opt-in, unknown-patient, and filename-pattern tests.

---

### US-038 - Print-Friendly Dashboard View (2 pts)

Reports layer:
- `reports/pdf_print_dashboard.py` renders a print-friendly PDF snapshot from the same `PatientReportData`.
- Portrait and landscape orientation are config-driven.

Export service and dashboard:
- `services/exports.export_print_dashboard_pdf()` writes the print PDF and records `print_dashboard` audit rows.
- Dashboard print flow now delegates PDF generation/audit to the service before invoking the OS print path or fallback open path.

Tests:
- Added print-dashboard PDF render, byte-stability, landscape, and audit-row tests.

---

## Acceptance Audit

| Story | Acceptance item | Status | Evidence |
|-------|-----------------|--------|----------|
| US-035 | `reports/data.py` gathers all sections in one assembler call; templates do not hit DB directly | Pass | `test_reports_data.py`; renderers consume `PatientReportData` |
| US-035 | Oncologist template renders all 10 catalogue sections | Pass | `test_reports_pdf_oncologist.py`; section renderers in template |
| US-035 | ANC trend chart embedded as PNG and config-toggleable | Pass | `test_oncologist_chart_receives_report_lab_history`; `include_anc_chart` gate |
| US-035 | Pre-cycle checklist renders `RuleResult` list with status icons | Pass | Oncologist checklist renderer; PDF render tests |
| US-035 | Cumulative dose, LVEF, neuropathy delegate to Sprint 6/7 services | Pass | `reports/data.py` calls existing service/clinical functions |
| US-035 | PCP template renders when enabled | Pass | `test_reports_pdf_pcp.py`; config default enabled |
| US-035 | Patient template renders when enabled | Pass | `test_reports_pdf_patient.py`; config default enabled |
| US-035 | Patient template avoids unexpanded acronyms in visible labels | Pass | Patient PDF uses plain labels and expanded terms |
| US-035 | Save-as dialog with audience picker and default filename | Pass | `ExportPdfDialog` implementation |
| US-035 | One `export_pdf` audit row per export with audience, filename, size | Pass | `test_export_patient_pdf_writes_file_and_audit_row` |
| US-035 | Golden/byte-stable tests for shipped templates | Pass | Repeated-render byte-stability tests for all PDF templates |
| US-035 | Report/template coverage added | Pass | New report PDF/data/export test files |
| US-036 | `list_for_patient()` returns one row per modification with reason and actor | Pass | `test_dose_modifications_service.py` |
| US-036 | Dose mod history panel mounts as collapsible dashboard section | Pass | `dashboard.py`; panel tests |
| US-036 | Empty state shown when patient has no modifications | Pass | `test_dose_mod_history_panel.py` |
| US-036 | Sortable by cycle number and date | Pass | `test_panel_sort_cycle`; `test_panel_sort_date` |
| US-036 | Same query layer reused by `reports/data.py` | Pass | `reports/data.py` imports `list_for_patient`, `list_for_cycle` |
| US-036 | Service and panel render covered | Pass | Service and panel tests |
| US-037 | CSV columns come from config | Pass | `test_write_csv_uses_configured_columns_and_round_trips` |
| US-037 | Date range applied at query layer | Pass | SQL filter in `_query_labs`; date range test |
| US-037 | `gcsf_within_7d` computed from overlap | Pass | `test_write_csv_marks_gcsf_window` |
| US-037 | Soft-deleted labs excluded by default; include opt-in | Pass | Soft-delete column compatibility tests |
| US-037 | Filename follows config pattern | Pass | `test_build_csv_filename_uses_config_pattern` |
| US-037 | One `export_csv` audit row per export | Pass | `test_export_patient_csv_writes_file_and_audit_row` |
| US-037 | CSV round-trip via `csv.DictReader` | Pass | `test_reports_csv_labs.py` |
| US-038 | Print dashboard renders one-page snapshot from `PatientReportData` | Pass | `test_reports_pdf_print_dashboard.py` |
| US-038 | Print button invokes OS print path | Pass | Dashboard delegates to service then `lpr`/Windows print |
| US-038 | Print failure fallback saves/opens PDF | Pass | Dashboard fallback path retained |
| US-038 | One `print_dashboard` audit row per print | Pass | `test_export_print_dashboard_pdf_writes_file_and_audit_row` |
| US-038 | Layout configurable: orientation and recent activity lookback | Pass | Landscape test; config-driven recent activity |
| US-038 | Byte-stable test on print-dashboard template | Pass | `test_print_dashboard_pdf_is_byte_stable` |

---

## Verification

| Check | Result |
|-------|--------|
| Import check | `python3 -c "from reports.data import gather; from reports.csv_labs import write_csv; from reports.pdf_oncologist import render; from services.exports import export_print_dashboard_pdf; print('OK')"` - OK |
| Logic check | `_get_all_labs_for_report()` returns report lab history - OK |
| Focused Sprint 9 tests | 43 passed |
| Broad non-GUI regression suite | 580 passed |
| Full suite with GUI access | 834 passed, 1 ReportLab deprecation warning |
| Warm report timing check | Oncologist 67.9 ms, print 0.7 ms, CSV 0.2 ms |

---

## Decisions

- Report PDFs use ReportLab `invariant=1` so repeated renders are byte-stable in tests.
- `PatientReportData` now carries `lab_history`; chart rendering reads from the assembler instead of querying inside the template.
- Print PDF generation and audit logging live in `services/exports.py`; the dashboard only handles the OS print/open path.
- CSV soft-delete behavior is schema-compatible: the current labs schema hard-deletes, but the exporter honors `deleted_at` if that column exists.
- The cold first render can spend time building Matplotlib/font caches; timing was measured on a warmed render path.

---

## Carry-Over

None for Sprint 9. Sprint 10 can start from the `v2-sprint9` tag.
