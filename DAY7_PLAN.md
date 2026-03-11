# DAY 7: Dashboard Integration & Patient Data Display

## Morning Check-in (5 min)
### Status
- [ ] 12/20 points done
- [ ] Today: Connect dashboard to patient data
- [ ] Show real patient information in dashboard

---

## Development: Patient Dashboard Header (3-4 hours)

### Dashboard Planning
- [ ] Review dashboard requirements (US-017, US-018)
- [ ] For now, focus on patient header
- [ ] Later sprints will add timeline, labs, etc.

### Update Dashboard View
- [ ] Open src/views/dashboard.py
- [ ] Import Patient model
- [ ] Import Cycle and LabValue models (for future use)

### Load Patient Data
- [ ] In set_patient(patient_id) method:
  - Call Patient.get_by_id(patient_id)
  - Store patient data in instance variable
  - Call refresh() to update display

### Patient Header Design
- [ ] Create header frame at top of dashboard
- [ ] Display patient information:
  - Patient Name (large, prominent)
  - Patient ID
  - Protocol type
  - AC-T Start Date
- [ ] Style header with background color
- [ ] Use large font for name

### Patient Header Implementation
- [ ] Create labels for each piece of info
- [ ] Arrange in clean layout
- [ ] Update labels in refresh() method with patient data
- [ ] Handle case where patient data is None

### Testing
- [ ] Select different patients from list
- [ ] Verify correct patient info displays in header
- [ ] Verify name, ID, protocol, start date are all correct
- [ ] Test with multiple patients

### Expected Deliverables:
- Dashboard displays real patient data in header
- Header looks clean and professional
- US-018 (Patient Header) complete

---

## Development: Dashboard Placeholders for Future Content (2-3 hours)

### Timeline Placeholder
- [ ] Create frame for where timeline will go
- [ ] Add placeholder text: "Treatment Timeline (Coming in Sprint 2)"
- [ ] Size and position appropriately

### Labs Placeholder
- [ ] Create frame for labs section
- [ ] Add placeholder: "Latest Labs (Coming in Sprint 3)"
- [ ] Position below or beside timeline

### Layout Planning
- [ ] Sketch overall dashboard layout
  - Patient header at top
  - Timeline in center
  - Labs on right or bottom
  - Back button easily accessible

### Styling
- [ ] Use frames with borders to show sections
- [ ] Add section titles
- [ ] Use consistent spacing

### Expected Deliverables:
- Dashboard has clear sections for future content
- Layout is planned and placeholders in place

---

## Development: Auto-Save Implementation (1-2 hours)

### Review US-020: Auto-Save
- [ ] Understand requirement: data saves automatically
- [ ] Verify that our current implementation auto-saves
- [ ] Patient.create() commits to database immediately ✅
- [ ] No additional "Save" button needed ✅

### Verification
- [ ] Add a patient
- [ ] Immediately close app (kill process)
- [ ] Reopen app
- [ ] Verify patient still exists
- [ ] If yes, auto-save is working!

### Document Behavior
- [ ] Add comment in patient creation code
- [ ] Note that SQLite commits are immediate
- [ ] No additional save mechanism needed

### Expected Deliverables:
- Confirmation that auto-save works
- US-020 complete (may have been complete already)

---

## End of Day Activities (15 min)

### Testing
- [ ] Test full patient workflow:
  - Add patient
  - View in list
  - Select patient
  - View dashboard with correct data
  - Navigate back to list
- [ ] Test data persistence

### Git Commit
- [ ] Stage dashboard.py changes
- [ ] Commit: "Add patient header to dashboard and section placeholders (US-018)"
- [ ] Push to GitHub

### Trello Update
- [ ] Move US-018 to "Done" ✅
- [ ] Move US-020 to "Done" ✅
- [ ] Update progress: 14/20 points

### Daily Log
- [ ] Document dashboard header complete
- [ ] Note auto-save verified
- [ ] Tomorrow: Synthetic data generator

### Expected Deliverables:
- Patient header in dashboard ✅
- Auto-save verified ✅
- 14 story points complete (70% of sprint)
