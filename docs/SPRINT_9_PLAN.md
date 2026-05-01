# Sprint 9 Plan — Reporting & Export

**V2 · Weeks 21–22 · Days 42–50 of V2**

---

## Sprint Goal

Every safety signal V2 has been accumulating — labs, cumulative dose, LVEF, neuropathy, reactions, G-CSF, symptoms, the pre-cycle checklist's `RuleResult` shape — collapses into a **one-click, one-page PDF patient summary** that an oncologist can hand to a PCP, hand to a patient, or fax. Dose modifications gain a **dedicated history view** so a nurse can see, in one screen, every dose change a patient has had and why. Labs export to **CSV** for ad-hoc analysis. The dashboard gets a **print-friendly snapshot** for nurses who still want paper.

**This is the output sprint.** Sprints 5–8 captured the data and made it actionable inside the app. Sprint 9 turns that data into artifacts that travel — paper, PDFs, CSVs — without compromising on the audit trail or the configuration layer.

**By Day 50 a nurse can produce a clinically complete, print-ready patient summary in under five seconds — and the same data path serves three audiences with three layouts.**

---

## Stories

| Story | Title | Points | Status |
|-------|-------|--------|--------|
| US-035 | PDF patient summary export (oncologist + PCP + patient) | 4 | To Do |
| US-036 | Dose modification history view | 2 | To Do |
| US-037 | CSV lab export | 1 | To Do |
| US-038 | Print-friendly dashboard view | 2 | To Do |

**Total: 9 story points · 9 development days**

---

## Sequencing

```
US-036 ─► (warm-up; introduces dose-mod query layer reused by US-035)
   │
   ▼
US-035 ─► oncologist template (must-ship) ─► PCP template ─► patient-facing template
   │
   ├─► US-037 (CSV) — independent, parallelizable Day 47
   └─► US-038 (print view) — second template over the same data path, Days 48–49
```

- **US-036 first.** Smallest story, but it forces the dose-modification query into a service so US-035 can reuse it instead of reinventing one.
- **US-035 next and longest.** Five days. Oncologist template lands first as the must-ship; PCP and patient templates are stretch and degrade gracefully if budget compresses.
- **US-037 in parallel.** CSV export is a 1-pt utility — half a day. Slot it Day 47 morning while the PDF tests stabilise.
- **US-038 last.** It's a second `reports/` template over the same data-gathering query US-035 built — wiring, not new logic.

---

## Dependencies (must be done)

| From | Artifact | Why Sprint 9 needs it |
|------|----------|-----------------------|
| Sprint 5 | Audit log | PDF "recent activity" section reads from `audit_log`; CSV export logs an `export` audit row |
| Sprint 5 | Institution config | Branding (institution name, logo path), PDF audience toggles, CSV column set, reminder cadence — all YAML-driven |
| Sprint 6 | Cumulative dose service + LVEF service | PDF cardiotoxicity section reads `cumulative_dose()` and `lvef_status()` |
| Sprint 7 | Toxicity services (neuropathy, reactions, G-CSF, symptoms) | PDF toxicity section reads each |
| Sprint 8 | `ChecklistResult` / `RuleResult` shape | PDF safety-state block renders the latest checklist outcome verbatim — **the shape is final, do not change it this sprint** |
| Sprint 8 | `clinical/scheduling.py` | PDF "next cycle" block calls `cycle_status()` |
| V1 | Patient list, ANC trend chart, latest labs panel | US-038 print view re-uses these renderers; US-035 embeds the ANC chart as PNG |

If any Sprint 8 carry-over is still open on Day 42 — particularly US-033 — **Sprint 9 cannot start.** The PDF summary depends on a final `RuleResult` shape; reshaping mid-sprint would force template rework.

---

## Pre-Sprint: Specialist YAML Review (Day 42 morning)

Sprint 9 questions for specialist review. Resolve on Day 42 or accept defaults and note in `PROJECT_LOG.md`.

| Question | Default | Decision | Source |
|----------|---------|----------|--------|
| PDF audiences shipped in V2 | oncologist (must) + PCP (stretch) + patient (stretch) | ☐ Accept · ☐ Override | |
| Institution name in PDF header | from `institution.defaults.yaml` `branding.name` | ☐ Accept · ☐ Override | |
| Institution logo path | none (text-only header) | ☐ Accept · ☐ Override | |
| PDF page size | US Letter (8.5×11 in) | ☐ A4 · ☐ Letter | |
| ANC chart embedded in oncologist PDF | yes (PNG, 4×2 in) | ☐ Yes · ☐ No | |
| Patient-facing PDF reading level | 6th-grade plain language; no acronyms unexpanded | ☐ Accept · ☐ Override | |
| PCP PDF includes referral guidance section | yes (rechallenge advice + neuropathy actions) | ☐ Accept · ☐ Override | |
| CSV column set for lab export | date, anc, hgb, plt, wbc, neut_pct, gcsf_within_7d, notes | ☐ Accept · ☐ Override | |
| CSV filename pattern | `labs_{patient_id}_{YYYY-MM-DD}.csv` | ☐ Accept · ☐ Override | |
| Print view orientation | portrait | ☐ Portrait · ☐ Landscape | |
| Print view "recent activity" lookback | last 90 days | ☐ Accept · ☐ Override | |
| PDF retains full patient name vs anonymised id | full name (single-user, in-clinic tool) | ☐ Accept · ☐ Override | |

Deliverable: one YAML diff against `config/institution.defaults.yaml` committed Day 42.

---

## Architecture Additions

Sprint 9 introduces the **`reports/`** package — flagged in the V2 plan, not yet created. It is the second consumer of the `services/` + `clinical/` layers (the first being `views/`). **Reports import freely from `services/` and `clinical/`; they import nothing from `views/` and never touch `sqlite3` directly.** This keeps the PDF/CSV path testable headlessly.

```
src/
├── reports/
│   ├── __init__.py
│   ├── data.py                    ← NEW — single PatientReportData gather query (used by ALL templates)
│   ├── pdf_oncologist.py          ← NEW — dense 1–2 page oncologist layout
│   ├── pdf_pcp.py                 ← NEW — 1 page PCP referral summary (stretch)
│   ├── pdf_patient.py             ← NEW — 1 page plain-language patient handout (stretch)
│   ├── pdf_print_dashboard.py     ← NEW — print-friendly dashboard snapshot (US-038)
│   ├── csv_labs.py                ← NEW — stdlib csv writer for labs
│   └── chart_png.py               ← NEW — matplotlib → BytesIO PNG helper for embedding
├── services/
│   ├── dose_modifications.py      ← NEW — query layer for US-036 + US-035 dose section
│   └── exports.py                 ← NEW — thin wrapper that runs a report + writes audit row
└── views/
    ├── components/
    │   └── dose_mod_history_panel.py    ← NEW — dose-mod history view (US-036)
    └── dialogs/
        ├── export_pdf_dialog.py         ← NEW — audience picker + save-as
        └── export_csv_dialog.py         ← NEW — date range + save-as
tests/
├── test_reports_data.py
├── test_reports_pdf_oncologist.py       ← golden-file: byte-stable PDF on fixed seed/font
├── test_reports_pdf_pcp.py
├── test_reports_pdf_patient.py
├── test_reports_pdf_print_dashboard.py
├── test_reports_csv_labs.py
├── test_dose_modifications_service.py
├── test_exports_service.py
└── test_dose_mod_history_panel.py
```

**Patterns carried forward from Sprints 6–8:**
- `reports/` modules are pure: `(PatientReportData, config) → bytes`. No DB calls, no Tk imports, no filesystem writes inside the renderer.
- The dialog handles the file-save path; the service layer writes the audit row.
- All vocabularies, labels, audience toggles, column sets via config.
- Golden-file tests for each PDF template — fixed font, fixed seed, byte-stable output.

---

## Schema Migrations

**None.** Sprint 9 is read-only against the schema.

The V2 plan flagged `reports/` as a new layer, not new tables. Every datum the PDF, CSV, and print view emit was persisted by Sprints 5–8. If you find yourself adding a column for "report convenience," stop — denormalising for a renderer is a tax we will pay forever.

The one auditable artifact Sprint 9 emits — the export event itself — fits the existing `audit_log` schema with `action='export_pdf'` or `action='export_csv'` and a JSON `details` field carrying audience, date range, and filename. No migration required.

---

## New Dependencies

| Package | Purpose | Notes |
|---------|---------|-------|
| `reportlab` (pinned) | PDF rendering | First non-pydantic, non-matplotlib top-level dep added in V2. Pin a known-stable version; vendor the license file. |
| (none for CSV) | CSV via stdlib `csv` | No new dep |
| (none for chart embed) | matplotlib already in V1 | Render to `BytesIO` PNG |

`requirements.txt` updated Day 42 with one line. No transitive surprises beyond reportlab's own deps; document any in the Sprint 9 summary.

---

## Config Additions (`config/institution.defaults.yaml`)

```yaml
reports:
  page_size: letter            # 'letter' | 'a4'
  margin_in: 0.5
  branding:
    institution_name: ""       # blank = "Chemotherapy Dashboard" fallback
    logo_path: ""              # blank = text-only header
    footer_text: "Generated by Chemotherapy Dashboard"

  audiences:
    oncologist: { enabled: true,  must_ship: true  }
    pcp:        { enabled: true,  must_ship: false }
    patient:    { enabled: true,  must_ship: false }

  oncologist:
    include_anc_chart: true
    chart_size_in: [4.0, 2.0]
    recent_activity_days: 90
    show_audit_summary: true

  pcp:
    include_referral_guidance: true
    reading_level: clinical

  patient:
    reading_level: plain_6th_grade
    expand_acronyms: true        # "ANC" → "Absolute Neutrophil Count (ANC)"

  print_dashboard:
    orientation: portrait
    recent_activity_days: 90

  csv:
    labs:
      columns:
        - date
        - anc
        - hgb
        - plt
        - wbc
        - neut_pct
        - gcsf_within_7d
        - notes
      filename_pattern: "labs_{patient_id}_{YYYY_MM_DD}.csv"
      include_soft_deleted: false

exports:
  audit_actions:
    pdf: export_pdf
    csv: export_csv
```

**Sources of truth, restated:**
- Institution name, logo, footer → consumed by every template; nothing else.
- Audience toggles → if `enabled: false`, the audience does not appear in the export dialog and the template is not registered. PCP/patient flip to `false` is the graceful-degradation lever if Sprint 9 runs hot.
- CSV column set → fully YAML-driven; new columns require zero code changes.

Sprint 9 **does not introduce new clinical thresholds**. Every clinical value in a report comes from the same config keys Sprints 5–8 already defined.

---

## PDF Section Catalogue (US-035 oncologist template)

The oncologist template is the contract. PCP and patient templates re-use the same data model with different layouts. Each row below = one section of the 1–2 page oncologist PDF, sourced from one service call.

| # | Section | Source | Notes |
|---|---------|--------|-------|
| 1 | Header (institution + patient ID + name + DOB + protocol + phase + cycle #) | `services/patients.get(patient_id)` + `clinical/scheduling.cycle_status()` | One-line summary at top |
| 2 | Latest cycle summary (date, agents, BSA, dose mg/m², dose %, mods) | `services/cycles.latest()` + `services/dose_modifications.list_for_cycle()` | Sprint 6 + new Sprint 9 service |
| 3 | Cumulative anthracycline dose + cardiotoxicity badge | `clinical/cardiotoxicity.cumulative_dose()` (Sprint 6) | Number + status word + headroom |
| 4 | Latest LVEF + delta from baseline | `services/lvef.latest()` + Sprint 6 status fn | Date, value, status |
| 5 | Latest labs (ANC, Hgb, Plt, WBC, draw date, age in hours) | `services/labs.latest()` | Stale-flag if >72h |
| 6 | ANC trend chart (last 90 d, embedded PNG) | `reports/chart_png.render_anc_trend()` | G-CSF marker glyph honoured |
| 7 | Toxicity summary (neuropathy effective grade, last reaction grade + agent, last G-CSF, symptoms ≥ advisory grade) | Sprint 7 services | One-line per modality |
| 8 | Pre-cycle checklist last outcome (rule list with status icons + worst_status) | Sprint 8 `ChecklistResult` shape | Verbatim render — no logic |
| 9 | Recent activity (last 90 d audit summary; configurable) | `services/audit.list_recent()` | "3 cycle saves · 1 override · 2 lab edits" |
| 10 | Footer (generated-on timestamp, institution footer text, page #) | config + `datetime.now()` | Same on every page |

**PCP template (stretch):** sections 1, 2, 3 (summary line only), 5, 7 (one paragraph), plus a referral-guidance section keyed off the most severe rule in the latest `ChecklistResult`. One page.

**Patient template (stretch):** sections 1 (without protocol jargon), 2 (next-cycle date prominent), 5 (ANC + simple "your blood counts are: low / borderline / fine"), and a plain-language explainer paragraph keyed off the latest checklist's worst rule. One page. Reading level enforced by avoiding any acronym not expanded on first use.

---

## Day-by-Day Plan

### DAY 42 — Sprint planning, specialist review, scaffolding
**Morning (~2h)** — Specialist YAML review; commit overrides (or accept defaults and note in `PROJECT_LOG.md`). Add `reportlab` to `requirements.txt`, install in venv, smoke-test `from reportlab.pdfgen.canvas import Canvas`.
**Afternoon (~3h)** — Add `reports:` and `exports:` blocks to `config/institution.defaults.yaml`. Scaffold `src/reports/` package with empty signatures: `data.py`, `pdf_oncologist.py`, `pdf_pcp.py`, `pdf_patient.py`, `pdf_print_dashboard.py`, `csv_labs.py`, `chart_png.py`. Scaffold `services/dose_modifications.py` and `services/exports.py`. Empty test files. Verify Sprint 8 test suite still green (783).
**Commit:** `Added Sprint 9 reporting package scaffolding`

### DAY 43 — US-036: dose modification history view
- Implement `services/dose_modifications.py`:
  - `list_for_patient(conn, patient_id) -> list[DoseMod]` — query `cycle` rows where `dose_pct < 100` joined with the audit row that explains *why* (reason text + actor + timestamp). Soft-deleted excluded.
  - `list_for_cycle(conn, cycle_id) -> list[DoseMod]` — for US-035 reuse.
  - Dataclass `DoseMod(cycle_number, date, agent, dose_pct, prior_pct, reason, actor)`.
- Implement `views/components/dose_mod_history_panel.py`: tabular list with columns *Cycle · Date · Agent · % · Reason · Actor*. Empty state: "No dose modifications recorded for this patient." Sortable by cycle number (default) or date.
- Mount in dashboard as a collapsible section beneath the toxicity panel (collapsed by default — most patients have none).
- Tests: query correctness on 3-cycle fixture (one C2 reduction, one C5 reduction); empty-state render; sort behavior.
**Commit:** `Added dose modification history view`
**US-036 DONE — 2 pts**

### DAY 44 — US-035 part 1: report data gather + chart embedder
- Implement `reports/data.py`:
  - `PatientReportData` dataclass — every field every template will need (header info, latest cycle, cumulative dose, LVEF, labs, toxicity summary, last checklist result, recent audit, dose mod list).
  - `gather(conn, patient_id, config, today) -> PatientReportData` — calls every relevant service exactly once, assembles the dataclass. Pure assembler over service calls.
- Implement `reports/chart_png.py`:
  - `render_anc_trend(labs, gcsf_admins, size_in, config) -> bytes` — matplotlib figure → BytesIO PNG. Honours G-CSF marker glyph (Sprint 7). DPI fixed (150) for byte-stable output in golden tests.
- Tests: `gather()` against the demo DB returns a fully-populated dataclass; chart renders to non-zero PNG bytes; chart renders deterministically on a fixed-seed fixture.
**Commit:** `Added patient report data gather and ANC chart embedder`

### DAY 45 — US-035 part 2: oncologist PDF template
- Implement `reports/pdf_oncologist.py`:
  - `render(data: PatientReportData, config) -> bytes` — reportlab Canvas, single function, top-down section-by-section per the catalogue above.
  - Layout: 0.5 in margins, two-column header, single-column body, ANC chart embedded mid-page, footer on every page.
  - Pre-cycle checklist block renders the `RuleResult` list with the same status icons used in the dialog (✓ ℹ ⚠ ⛔) and the worst-status banner.
- Golden-file test: render against a fixed fixture (seeded patient, fixed `today`), assert byte-stable output. Lock the font (reportlab's built-in Helvetica — no system font dependency).
- Render-on-screen smoke test: open the PDF in `Preview.app` once manually; commit a screenshot to `docs/sprint9_assets/` for the summary.
**Commit:** `Added oncologist PDF summary template`

### DAY 46 — US-035 part 3: export dialog + service + audit row
- Implement `services/exports.py`:
  - `export_patient_pdf(conn, patient_id, audience, target_path, config, today) -> ExportResult` — calls `reports.data.gather()`, dispatches to the audience template, writes bytes to `target_path`, writes one `audit_log` row with `action='export_pdf'` and details `{audience, patient_id, filename, size_bytes}`.
  - `ExportResult(path, size_bytes, audience, audit_id)`.
- Implement `views/dialogs/export_pdf_dialog.py`:
  - Audience radio (oncologist / PCP / patient — disabled options for audiences with `enabled: false` in config).
  - Save-as file picker (default filename `summary_{patient_id}_{audience}_{YYYY-MM-DD}.pdf`).
  - "Export" button → calls service → toast on success / error dialog on failure.
- Hook button into patient dashboard header: "Export PDF".
- Integration test: full path on demo DB → file written → audit row recorded → file readable as PDF (ReportLab parser round-trip or `pypdf` minimal probe).
**Commit:** `Added PDF export dialog and audit-logged service`

### DAY 47 — US-035 part 4: PCP + patient templates (stretch) + US-037 CSV export
- **Morning — PCP template** (`reports/pdf_pcp.py`): one page, sections 1/2/3/5/7 + referral guidance keyed to the most severe rule from the latest `ChecklistResult`. Golden-file test.
- **Morning — patient template** (`reports/pdf_patient.py`): one page, plain-language. Acronyms expanded on first use ("ANC (Absolute Neutrophil Count)") via a small expansion map in config. Golden-file test.
- **Stretch handling:** if either template is not byte-stable by 16:00, flip its `enabled` flag to `false` in config and document in the Sprint 9 summary. **Oncologist template is the must-ship; PCP and patient are stretch per V2 plan.**
- **Afternoon — US-037 CSV labs export** (`reports/csv_labs.py` + `views/dialogs/export_csv_dialog.py`):
  - Date-range picker (from / to), default "all".
  - Column set from config; `gcsf_within_7d` computed from `services/gcsf.list_for_patient()` overlap.
  - Service writes one `audit_log` row with `action='export_csv'`.
  - Tests: column-set correctness, date-range filtering, soft-deleted exclusion, CSV round-trip via stdlib `csv.DictReader`.
**Commit:** `Added PCP and patient PDF templates and CSV lab export`
**US-035 DONE — 4 pts**
**US-037 DONE — 1 pt**

### DAY 48 — US-038 part 1: print-friendly dashboard PDF
- Implement `reports/pdf_print_dashboard.py`:
  - Reuses `reports/data.py` gather — **no new query layer**.
  - Layout differs from oncologist: full-width sections, larger type, no chart embed (it's a snapshot, not a referral artifact). Single-page portrait by default; landscape configurable.
  - Sections: header, latest cycle, latest labs, toxicity summary, pre-cycle checklist last outcome, recent activity (90 d).
- Golden-file test against the same fixture used for oncologist; output differs in layout, not data.
**Commit:** `Added print-friendly dashboard PDF template`

### DAY 49 — US-038 part 2: print button + integration sweep
- Add "Print" button to dashboard header (next to "Export PDF").
- On click: render `pdf_print_dashboard`, save to a temp path, hand to OS print dialog (`subprocess.run(["lpr", path])` on macOS / `os.startfile(path, "print")` on Windows). On failure, fall back to "save PDF and open" with a toast.
- One audit row written with `action='print_dashboard'` and details `{patient_id}`.
- End-to-end test: button click → PDF rendered → temp file exists → audit row written. (The OS print pipe itself is mocked in tests.)
- Regression sweep: every Sprint 5/6/7/8 test passes; PDF exports do not mutate any clinical data.
- Performance: PDF gather + render (oncologist) < 800 ms at P95 on demo DB. CSV export < 200 ms.
**Commit:** `Added print-friendly dashboard view and integration coverage`
**US-038 DONE — 2 pts**

### DAY 50 — Demo, retro, summary
- Demo walkthrough on demo DB: open dashboard for a mid-T-phase patient → click "Export PDF" → pick "Oncologist" → save → open PDF in Preview, walk through every section. Repeat for PCP and patient (or note disabled). Click "Export CSV" → 90-day range → open in Numbers. Click "Print" → confirm OS print dialog appears. Open the dose-mod history view and walk through reductions on a fixture patient.
- Write `docs/SPRINT_9_SUMMARY.md` matching the Sprint 8 summary shape.
- Update `docs/PROJECT_LOG.md` close-out entry.
- Tag `v2-sprint9`.
**Commit:** `Added Sprint 9 summary and close-out`

---

## Story Acceptance Criteria

### US-035 — PDF patient summary export (4 pts)
- [ ] `reports/data.py` gathers all sections in one assembler call; no template hits the DB directly
- [ ] Oncologist template renders all 10 sections of the PDF Section Catalogue
- [ ] ANC trend chart embedded as PNG in oncologist template (config-toggleable)
- [ ] Pre-cycle checklist block renders the `RuleResult` list verbatim with status icons
- [ ] Cumulative dose / LVEF / neuropathy values **delegate** to Sprint 6/7 services (no reimplementation)
- [ ] PCP template renders if `audiences.pcp.enabled: true` (stretch — graceful disable allowed)
- [ ] Patient template renders if `audiences.patient.enabled: true` (stretch — graceful disable allowed)
- [ ] Patient template expands acronyms on first use; reading level documented
- [ ] Save-as dialog with audience picker; default filename per pattern
- [ ] One `export_pdf` audit row written per export with audience + filename + size
- [ ] Golden-file tests for every shipped template (byte-stable)
- [ ] Coverage on `reports/data.py` ≥ 90%; on each shipped template ≥ 85%

### US-036 — Dose modification history view (2 pts)
- [ ] `services/dose_modifications.list_for_patient()` returns one row per modification with reason + actor
- [ ] Dose mod history panel mounts as collapsible section in dashboard
- [ ] Empty state shown when patient has no modifications
- [ ] Sortable by cycle number (default) and date
- [ ] Same query layer reused by `reports/data.py` (no duplicate logic)
- [ ] Test coverage on the service ≥ 90%; panel render covered

### US-037 — CSV lab export (1 pt)
- [ ] `reports/csv_labs.py` writes columns per `csv.labs.columns` config
- [ ] Date-range filter applied at query layer (not post-filter)
- [ ] `gcsf_within_7d` boolean column computed from G-CSF admin overlap
- [ ] Soft-deleted labs excluded by default; `include_soft_deleted: true` opt-in
- [ ] Filename follows `csv.labs.filename_pattern`
- [ ] One `export_csv` audit row written per export
- [ ] Round-trip test: write CSV → read with stdlib `csv.DictReader` → row count + column set match

### US-038 — Print-friendly dashboard view (2 pts)
- [ ] `reports/pdf_print_dashboard.py` renders one-page snapshot from same `PatientReportData`
- [ ] "Print" button in dashboard header invokes OS print dialog
- [ ] Fallback path on print failure: save PDF + toast
- [ ] One `print_dashboard` audit row written per print
- [ ] Layout configurable: orientation (portrait default), recent-activity lookback
- [ ] Golden-file test on the same fixture used for oncologist template

---

## Success Criteria (sprint-level)

- [ ] All four stories merged to master, tagged `v2-sprint9`
- [ ] Coverage on `src/reports/` ≥ 85%; on `src/services/dose_modifications.py` and `src/services/exports.py` ≥ 90%
- [ ] No regressions in Sprint 5/6/7/8 test suites
- [ ] Oncologist PDF render < 800 ms at P95 on demo DB; CSV export < 200 ms; print-dashboard PDF < 600 ms
- [ ] Demo walkthrough (Day 50) covers all four stories without manual DB poking
- [ ] Zero magic numbers in code — every label, audience toggle, column set, filename pattern resolves through config
- [ ] Audit viewer (US-022) shows `export_pdf`, `export_csv`, and `print_dashboard` rows with correct details
- [ ] No new schema migrations shipped this sprint
- [ ] `requirements.txt` updated with one new pinned dep (`reportlab`); license vendored

---

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| US-035 grows past 4 pts because PDF layout iteration is open-ended | High | Oncologist template is the only must-ship; PCP and patient flip to disabled in config if Day 47 budget compresses. V2 plan explicitly allows this. |
| Golden-file PDF tests are flaky across reportlab/font versions | High | Pin `reportlab` version exactly; use built-in Helvetica only (no system fonts); fix DPI; commit goldens with the tests. |
| `PatientReportData` becomes a god-object that every template chips at | Medium | One assembler per service call; no per-template fields on the dataclass — if a template needs a derived value, compute it in the template, not the assembler. |
| The print path on Day 49 hits OS-specific behavior late | Medium | Mock the OS pipe in tests; manual smoke on macOS Day 49; document Windows path as untested in Sprint 9 summary. |
| ANC chart embed dependency on matplotlib renders differently across runs | Medium | Fixed DPI, fixed seed, fixed figure size; chart-only golden test isolated from full-PDF golden so failures localise. |
| Patient-facing template tone audit is subjective | Medium | Reading-level rule is mechanical: every acronym expanded on first use. No subjective tone review beyond that in V2; defer to V2.1. |
| Adding `reportlab` introduces transitive deps that break demo install | Low | Pin and vendor; CI install on a clean venv on Day 42 to confirm. |
| Sprint 8 carry-over (US-033) leaves `RuleResult` shape unstable | Low | Sprint 8 closed clean (verified in `SPRINT_8_SUMMARY.md`); shape is final. If a Sprint 8 follow-up commit ever reshapes it, Sprint 9 templates break loudly via golden tests — by design. |
| Print button on Windows defaults to wrong app | Low | macOS-first this sprint; Windows path is best-effort and documented. |
| Schema-creep: a column that "would make the PDF easier" | High | None this sprint. Confirmed in *Schema Migrations* section. |

---

## Out of Scope (reject on sight)

- Multi-patient batch PDF export ("print every patient's summary") → V3 reporting
- Scheduled/automatic exports → V3 (needs job runner)
- Email-PDF-from-app → V3 (needs SMTP config and consent flow)
- HL7 FHIR export → V3 (the EHR integration story)
- DOCX / RTF export → V3 (PDF is the V2 print format)
- Custom user-built report templates → V3 (all V2 templates are code, not config-built)
- Per-cycle PDF (vs per-patient) → V3 if requested
- Watermark / "DRAFT" overlay → V2.1 polish if a regulator requires it
- Encrypted/password-protected PDFs → V3 (paired with SQLCipher backups)
- Charts other than ANC trend embedded in PDF → V3 (cumulative-dose chart, LVEF chart)
- Export of audit log itself → V3 (compliance feature, separate scope)
- Print preview window → V2.1 polish (the OS dialog covers it)

If any of the above surfaces mid-sprint, log to `docs/BACKLOG_V3.md` and move on.

---

## Definition of Done (per story)

1. Code committed with single-line `Added ...` message
2. Unit tests on every pure function + golden-file test on every shipped PDF template
3. Config values, vocabularies, audience toggles, column sets read from YAML, not hardcoded
4. Audit entries written for every export and print
5. PDF rendered cleanly at default page size; tested manually in Preview at least once
6. Component / button / dialog visible on dashboard
7. No regression in Sprint 5/6/7/8 test suite
8. Entry in `PROJECT_LOG.md` for the day

---

## Post-Sprint Carry-Over Protocol

If any story is incomplete at end of Day 50:

- **US-036 incomplete** → carry into Sprint 10 Day 1 (no downstream dependency).
- **US-035 oncologist template incomplete** → **Sprint 9 cannot close.** This is the must-ship per V2 plan. Extend by 1–2 days rather than ship without an oncologist PDF.
- **US-035 PCP or patient template incomplete** → flip the audience's `enabled: false` in config and document in summary. The V2 plan explicitly permits this; both are stretch.
- **US-037 incomplete** → carry into Sprint 10 Day 1 (no downstream dependency; tiny scope).
- **US-038 incomplete** → carry into Sprint 10 Day 1; the print button hides until ready. The PDF path is the same; only the button + OS pipe differ.

**Do not start Sprint 10 with the oncologist PDF still incomplete.** Sprint 10 is polish + release prep — it assumes the V2 reporting surface is final and tested. A partial reporting surface entering Sprint 10 means Sprint 10 absorbs reporting work it was not budgeted for, and V2 ships late.
