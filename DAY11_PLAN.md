# DAY 11: Sprint 2 Planning + Timeline Component Design

## Morning: Sprint 2 Kickoff (45-60 min)

### Welcome Back Review
- [ ] Review Sprint 1 accomplishments
- [ ] Read Sprint 1 summary document
- [ ] Refresh on what was built

### Sprint 2 Goal Review
- [ ] Read Sprint 2 goal aloud
- [ ] Understand what "done" looks like
- [ ] Visualize the finished timeline feature

### Story Deep Dive
- [ ] Read each Sprint 2 user story carefully
- [ ] Study acceptance criteria
- [ ] Identify technical requirements
- [ ] Note questions or uncertainties

### US-007: View Treatment Timeline
- [ ] Acceptance: 8 cycles displayed visually
- [ ] Cycles 1-4 labeled "AC"
- [ ] Cycles 5-8 labeled "T"
- [ ] Completed cycles look different from pending
- [ ] Current cycle highlighted

### US-008: AC/T Phase Distinction
- [ ] Visual separation between phases
- [ ] Different colors or styling
- [ ] Phase labels visible

### US-009: Dose Modification Indicators
- [ ] Modified cycles show indicator (icon, color)
- [ ] Must be visible without clicking

### US-010: Record Cycle Completion
- [ ] Click cycle to open dialog
- [ ] Enter completion date
- [ ] Save updates timeline

### US-011: Record Dose Modification
- [ ] Percentage selection (100%, 85%, 75%, 50%, custom)
- [ ] Reason selection (dropdown)
- [ ] Saved with cycle

### US-012: Current Cycle Status
- [ ] Text display: "Current: Cycle X (Phase)"
- [ ] Next scheduled date if available

### Technical Approach Discussion
- [ ] Decide: Canvas-based or Frame-based timeline?
  - Canvas: More flexible drawing, complex click handling
  - Frames: Easier widgets, simpler event binding
- [ ] Recommendation: Frame-based with styled buttons/labels
- [ ] Each cycle = clickable frame/button
- [ ] Styling changes based on status

### Dependency Mapping
- [ ] US-007 (Timeline) must come first
- [ ] US-008 (Phases) can be done with US-007
- [ ] US-010 (Complete Cycle) depends on US-007
- [ ] US-011 (Dose Mod) is part of US-010
- [ ] US-009 (Mod Indicators) depends on US-011
- [ ] US-012 (Current Status) can be parallel

### Day-by-Day Plan
- [ ] Day 11: Planning + Timeline structure
- [ ] Day 12: Timeline visual implementation
- [ ] Day 13: Phase distinction + styling
- [ ] Day 14: Cycle completion dialog
- [ ] Day 15: Dose modification recording
- [ ] Day 16: Indicators on timeline
- [ ] Day 17: Current cycle status
- [ ] Day 18: Integration with dashboard
- [ ] Day 19: Testing and bug fixes
- [ ] Day 20: Sprint review and retrospective

### Trello Board Update
- [ ] Move Sprint 2 cards to "Sprint 2" list
- [ ] Order cards by dependency
- [ ] Add comments about approach
- [ ] Move US-007 to "In Progress"

### Create Daily Log Entry
- [ ] Start Sprint 2 section in daily log
- [ ] Note sprint planning complete
- [ ] Document technical decisions

### Expected Deliverables:
- Clear understanding of Sprint 2 scope
- Technical approach decided
- Day-by-day plan created
- Trello updated

---

## Development: Timeline Component Structure (4-5 hours)

### Folder Setup
- [ ] Create src/views/components/ directory
- [ ] Create __init__.py in components folder

### Create Timeline Component File
- [ ] Create src/views/components/timeline.py
- [ ] Create TimelineComponent class extending tk.Frame
- [ ] Constructor parameters: parent, controller, patient_id

### Timeline Data Loading
- [ ] Write method to load cycle data
- [ ] Call get_cycles_by_patient(patient_id)
- [ ] Store cycles in instance variable
- [ ] Plan for refresh functionality

### Basic Layout Structure
- [ ] Create main timeline frame
- [ ] Plan layout:
  - Title/header area
  - Current status text
  - 8 cycle boxes in a row
  - Phase labels below cycle groups

### Cycle Box Design
- [ ] Each cycle will be a frame (~80x80 pixels)
- [ ] Contains: cycle number, status indicator, phase indicator (AC/T)
- [ ] Clickable to open completion dialog

### Status-Based Styling Plan
- [ ] Pending: Gray background, empty
- [ ] Current: Highlighted border, different color
- [ ] Completed: Green, checkmark
- [ ] Modified: Warning indicator overlay
- [ ] AC Phase: Blue tones
- [ ] T Phase: Purple tones

### Create Cycle Frame Method
- [ ] Write create_cycle_frame(cycle_data) method
- [ ] Add cycle number label
- [ ] Add status indicator
- [ ] Bind click event
- [ ] Return configured frame
- [ ] Test with one cycle

### Layout All 8 Cycles
- [ ] Create method to build full timeline
- [ ] Loop through 8 cycles
- [ ] Arrange in horizontal row
- [ ] Group cycles 1-4 (AC) and 5-8 (T)
- [ ] Add spacing between phase groups

### Phase Labels
- [ ] Add "AC Phase" label below cycles 1-4
- [ ] Add "T Phase" label below cycles 5-8
- [ ] Style and center labels under their cycles

### Basic Integration Test
- [ ] Import TimelineComponent in dashboard.py
- [ ] Add timeline to dashboard layout
- [ ] Pass patient_id when dashboard loads
- [ ] Verify 8 boxes display

### Expected Deliverables:
- Timeline component file created
- Basic structure in place
- 8 cycle boxes displaying
- Phase grouping visible
- Timeline integrated into dashboard (basic)

---

## End of Day Activities (15 min)

### Code Review
- [ ] Review timeline.py code
- [ ] Check code organization
- [ ] Add comments explaining structure
- [ ] Note any technical debt

### Git Commit
- [ ] Stage timeline.py
- [ ] Stage any dashboard.py changes
- [ ] Commit: "Add timeline component structure with 8 cycle placeholders (US-007 in progress)"

### Trello Update
- [ ] US-007 remains "In Progress"
- [ ] Add comment: "Basic structure complete, styling tomorrow"

### Daily Log
- [ ] Document what was built
- [ ] Note technical decisions made
- [ ] Plan for tomorrow: styling and visual states

### Self-Check
- [ ] Does the timeline appear in dashboard?
- [ ] Are 8 cycles visible?
- [ ] Is the code organized?
- [ ] Ready for styling tomorrow?

### Expected Deliverables:
- Timeline structure committed
- Progress documented
- Clear plan for Day 12
