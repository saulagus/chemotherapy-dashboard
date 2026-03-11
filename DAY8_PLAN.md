# DAY 8: Synthetic Data Generator

## Morning Check-in (5 min)
### Sprint 1 Home Stretch
- [ ] 14/20 points done (70%)
- [ ] 3 days left in sprint
- [ ] Today: Generate test data
- [ ] Tomorrow: Sprint polish and integration
- [ ] Friday: Sprint review and retrospective

---

## Development: Data Generation Script (5-6 hours)

### Planning
- [ ] Review US-021 requirements
- [ ] Generate 5 realistic patients
- [ ] Varied treatment progress (early, mid, late)
- [ ] Realistic lab values
- [ ] Some with dose modifications

### Create Generator Script
- [ ] Create generate_test_data.py in project root
- [ ] Import models (Patient, Cycle, LabValue)
- [ ] Import random, datetime modules

### Patient Generation Function
- [ ] Create generate_patients(count) function
- [ ] Generate realistic patient IDs (e.g., "TEST-001", "TEST-002")
- [ ] Generate realistic names or initials
- [ ] Random protocol selection (Dose-Dense or Standard)
- [ ] Random start dates (within past 6 months)
- [ ] Random age at diagnosis (40-70)

### Cycle Progression Logic
- [ ] For each patient, decide how many cycles to complete
- [ ] Variation:
  - Patient 1: 0-2 cycles (early treatment)
  - Patient 2: 3-5 cycles (mid treatment)
  - Patient 3: 6-7 cycles (late treatment)
  - Patient 4: 8 cycles (treatment complete)
  - Patient 5: Some cycles with dose modifications
- [ ] Mark cycles as completed
- [ ] Set actual dates for completed cycles
- [ ] Some cycles: add dose modifications (80%, 85%, 75%)

### Lab Value Generation
- [ ] For each completed cycle, generate pre-treatment labs
- [ ] Realistic ANC values: range 0.5 to 4.0
- [ ] Create some low values (below 1.5 threshold)
- [ ] Create trend: some patients' ANC decreases over treatment
- [ ] Generate WBC, platelets, hemoglobin as well

### Clear Data Function
- [ ] Create clear_all_data() function
- [ ] Deletes all patients (cascades to cycles, labs)
- [ ] Useful for resetting to clean state

### Command-Line Interface
- [ ] Add argument parsing (argparse)
- [ ] Arguments:
  - `--patients [number]` (default 5)
  - `--clear` (to clear all data first)
- [ ] Example usage: `python generate_test_data.py --patients 5`

### Testing
- [ ] Run generator script
- [ ] Verify 5 patients created
- [ ] Open app, verify patients appear in list
- [ ] Verify varied cycle completion
- [ ] Select patients, verify some have labs
- [ ] Run with --clear flag, verify data is cleared

### Documentation
- [ ] Add usage instructions to README.md
- [ ] Document how to generate test data
- [ ] Document how to clear data

### Expected Deliverables:
- Working test data generator script
- Can generate varied, realistic patient data
- Can clear all data
- US-021 complete

---

## Development: In-App Data Generator Access (Optional - 1-2 hours)

### Review US-022
- [ ] Optional: Add in-app access to generator
- [ ] Could be a menu item or hidden shortcut
- [ ] Or: Keep as CLI-only (simpler)

### If Implementing In-App Access:
- [ ] Add "Developer" menu to main window
- [ ] Menu item: "Generate Test Data"
- [ ] Menu item: "Clear All Data"
- [ ] Both show confirmation dialogs
- [ ] Call generator functions from menu

### If Skipping In-App Access:
- [ ] Document that generator is CLI-only
- [ ] Add comment to US-022 that CLI is sufficient
- [ ] Move US-022 to "Won't Do" or "Done" with note

### Decision:
- [ ] Decide if in-app access is needed
- [ ] CLI is simpler and sufficient for solo dev
- [ ] In-app is nice for oncologists if they'll use it

### Expected Deliverables:
- Either in-app access OR documented CLI usage
- US-022 complete or consciously deferred

---

## End of Day Activities (15 min)

### Testing with Fresh Data
- [ ] Clear all data
- [ ] Generate 5 test patients
- [ ] Launch app
- [ ] Review all patients in list
- [ ] Click through each patient's dashboard
- [ ] Verify data looks realistic

### Git Commit
- [ ] Stage generate_test_data.py
- [ ] Stage any README updates
- [ ] Commit: "Add synthetic test data generator with CLI interface (US-021)"
- [ ] Push to GitHub

### Trello Update
- [ ] Move US-021 to "Done" ✅
- [ ] Move US-022 to "Done" or note decision ✅
- [ ] Update progress: 19 or 20/20 points complete!

### Daily Log
- [ ] Document test data generator complete
- [ ] Note that Sprint 1 is nearly done
- [ ] Tomorrow: Integration testing and polish

### Expected Deliverables:
- Test data generator working
- Sprint 1 features essentially complete
- Ready for final testing tomorrow
