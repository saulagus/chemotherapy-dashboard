# Day 6 Plan — Add Patient Form
# DELETE THIS FILE AT END OF DAY

---

## Week 2 Kick-off

- Sprint 1 progress: 9/20 points done
- This week's goal: complete all remaining Sprint 1 stories by Day 10
- Remaining stories:
  - US-005: Add New Patient (3 pts) — today's focus
  - US-019: Local Data Storage (UI integration)
  - US-020: Auto-Save (1 pt)
  - US-021: Generate Synthetic Data (3 pts)
  - US-022: Access Data Generator (1 pt)

---

## Development Checklist

### Form Planning
- [ ] Review Add Patient requirements (US-005)
- [ ] Decide: Toplevel separate window
- [ ] Plan validation rules

### Create Dialog
- [ ] Create `src/views/add_patient_dialog.py`
- [ ] `AddPatientDialog` class extending `tk.Toplevel`
- [ ] Set window title and size
- [ ] Make modal (blocks main window until closed)

### Form Layout
- [ ] Grid layout — labels left, inputs right
- [ ] Patient ID entry (required)
- [ ] Name/Initials entry (required)
- [ ] AC-T Start Date entry with YYYY-MM-DD hint (required)
- [ ] Protocol combobox: ["Dose-Dense AC-T", "Standard AC-T"] (required)
- [ ] Age at Diagnosis entry (optional)
- [ ] Diagnosis Date entry with YYYY-MM-DD hint (optional)

### Buttons
- [ ] Save Patient button
- [ ] Cancel button
- [ ] Place at bottom, styled appropriately

### Validation — validate_inputs()
- [ ] Required fields not empty
- [ ] Patient ID: alphanumeric, 3–20 chars
- [ ] Dates are valid YYYY-MM-DD format
- [ ] Dates not in the future
- [ ] Return list of validation errors

### Save Handler
- [ ] Collect all input values
- [ ] Call validate_inputs()
- [ ] Show errors if invalid — do not save
- [ ] Create patient via Patient.create() / add_patient()
- [ ] Handle duplicate patient ID error
- [ ] Show success message
- [ ] Close dialog
- [ ] Refresh patient list

### Cancel Handler
- [ ] Close dialog without saving
- [ ] Return focus to patient list

### Integration with PatientListView
- [ ] Update `_on_add_patient()` to open AddPatientDialog
- [ ] Pass app reference to dialog
- [ ] Refresh list after dialog closes

### Testing
- [ ] Open dialog from patient list
- [ ] Enter valid data and save — patient appears in list
- [ ] Validation: empty required fields
- [ ] Validation: duplicate patient ID
- [ ] Validation: invalid date format
- [ ] Validation: future dates
- [ ] Cancel without saving

### Error Messaging
- [ ] Clear messages for each validation failure
- [ ] Style errors in red/warning colour

---

## End of Day

- [ ] All testing checklist items green
- [ ] Commit: "Implement Add Patient dialog with form validation (US-005)"
- [ ] Push to GitHub
- [ ] Move US-005 to Done on Trello
- [ ] Update progress: 12/20 points (60% of sprint)
- [ ] Update PROJECT_LOG.md
- [ ] Delete this file
