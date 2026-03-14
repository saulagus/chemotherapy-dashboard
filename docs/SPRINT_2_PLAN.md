# Sprint 2 Plan: Treatment Timeline & Cycle Tracking
# Weeks 3-4, Days 11-20

## Sprint Goal
Visual 8-cycle timeline displays treatment progress, cycles can be completed with dose modification tracking.

**Total Story Points: 14**

## Stories in Sprint
- US-007: View Treatment Timeline (5 pts)
- US-008: Distinguish AC and T Phases (1 pt)
- US-009: Identify Dose Modifications on Timeline (2 pts)
- US-010: Record Cycle Completion (3 pts)
- US-011: Record Dose Modification (2 pts)
- US-012: View Current Cycle Status (1 pt)

## Sprint 2 Overview

### What We're Building
- Visual timeline showing all 8 chemotherapy cycles
- Clear distinction between AC phase (cycles 1-4) and T phase (cycles 5-8)
- Ability to click on a cycle and mark it as completed
- Dose modification recording with percentage and reason
- Visual indicators showing which cycles had dose reductions
- Display of current cycle status ("Cycle 3 of 8 - AC Phase")

### Key Technical Challenges
- Tkinter Canvas or Frame-based visualization
- Click handling on visual elements
- Dynamic updates after cycle completion
- Visual states (completed, current, pending)
- Dose modification indicators

### Dependencies
- Sprint 1 foundation (complete)
- Patient data model (complete)
- Cycle data model (complete)

---

## DAY 11: Sprint 2 Planning + Timeline Component Design

### Morning: Sprint 2 Kickoff (45-60 min)

#### Welcome Back Review
- [ ] Review Sprint 1 accomplishments
- [ ] Read Sprint 1 summary document
- [ ] Refresh on what was built

#### Sprint 2 Goal Review
- [ ] Read Sprint 2 goal aloud
- [ ] Understand what "done" looks like
- [ ] Visualize the finished timeline feature

#### Story Deep Dive
- [ ] Read each Sprint 2 user story carefully
- [ ] Study acceptance criteria
- [ ] Identify technical requirements

#### US-007: View Treatment Timeline
- [ ] Acceptance: 8 cycles displayed visually
- [ ] Cycles 1-4 labeled "AC"
- [ ] Cycles 5-8 labeled "T"
- [ ] Completed cycles look different from pending
- [ ] Current cycle highlighted

#### US-008: AC/T Phase Distinction
- [ ] Visual separation between phases
- [ ] Different colors or styling
- [ ] Phase labels visible

#### US-009: Dose Modification Indicators
- [ ] Modified cycles show indicator (icon, color)
- [ ] Must be visible without clicking

#### US-010: Record Cycle Completion
- [ ] Click cycle to open dialog
- [ ] Enter completion date
- [ ] Save updates timeline

#### US-011: Record Dose Modification
- [ ] Percentage selection (100%, 85%, 75%, 50%, custom)
- [ ] Reason selection (dropdown)
- [ ] Saved with cycle

#### US-012: Current Cycle Status
- [ ] Text display: "Current: Cycle X (Phase)"
- [ ] Next scheduled date if available

#### Technical Approach Discussion
- [ ] Decide: Canvas-based or Frame-based timeline?
  - Canvas: More flexible drawing, complex click handling
  - Frames: Easier widgets, simpler event binding
- [ ] Recommendation: Frame-based with styled buttons/labels
- [ ] Each cycle = clickable frame/button
- [ ] Styling changes based on status

#### Dependency Mapping
- [ ] US-007 (Timeline) must come first
- [ ] US-008 (Phases) can be done with US-007
- [ ] US-010 (Complete Cycle) depends on US-007
- [ ] US-011 (Dose Mod) is part of US-010
- [ ] US-009 (Mod Indicators) depends on US-011
- [ ] US-012 (Current Status) can be parallel

#### Day-by-Day Plan
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

#### Trello Board Update
- [ ] Move Sprint 2 cards to "Sprint 2" list
- [ ] Order cards by dependency
- [ ] Move US-007 to "In Progress"

### Development: Timeline Component Structure (4-5 hours)

#### Folder Setup
- [ ] Create src/views/components/ directory
- [ ] Create __init__.py in components folder

#### Create Timeline Component File
- [ ] Create src/views/components/timeline.py
- [ ] Create TimelineComponent class extending tk.Frame
- [ ] Constructor parameters: parent, controller, patient_id

#### Timeline Data Loading
- [ ] Write method to load cycle data
- [ ] Call get_cycles_by_patient(patient_id)
- [ ] Store cycles in instance variable
- [ ] Plan for refresh functionality

#### Basic Layout Structure
- [ ] Create main timeline frame
- [ ] Plan layout:
  - Title/header area
  - Current status text
  - 8 cycle boxes in a row
  - Phase labels below cycle groups

#### Cycle Box Design
- [ ] Each cycle will be a frame/button (~80x80 pixels)
- [ ] Contains: cycle number, status indicator, phase indicator
- [ ] Clickable to open completion dialog

#### Status-Based Styling Plan
- [ ] Pending: Gray background
- [ ] Current: Highlighted border
- [ ] Completed: Green, checkmark
- [ ] Modified: Warning indicator overlay
- [ ] AC Phase: Blue tones
- [ ] T Phase: Purple tones

#### Create Cycle Frame Method
- [ ] Write create_cycle_frame(cycle_data) method
- [ ] Add cycle number label
- [ ] Add status indicator
- [ ] Bind click event
- [ ] Test with one cycle

#### Layout All 8 Cycles
- [ ] Loop through 8 cycles
- [ ] Arrange in horizontal row
- [ ] Group cycles 1-4 (AC) and 5-8 (T)
- [ ] Add spacing between phase groups

#### Phase Labels
- [ ] Add "AC Phase" label below cycles 1-4
- [ ] Add "T Phase" label below cycles 5-8

#### Basic Integration Test
- [ ] Import TimelineComponent in dashboard.py
- [ ] Add timeline to dashboard layout
- [ ] Verify 8 boxes display

### End of Day Activities
- [ ] Code review — add comments
- [ ] Git commit: "Add timeline component structure with 8 cycle placeholders (US-007 in progress)"
- [ ] Daily log entry

#### Expected Deliverables:
- Timeline component file created
- Basic structure in place
- 8 cycle boxes displaying
- Phase grouping visible
- Timeline integrated into dashboard (basic)

---

## DAY 12: Timeline Visual Implementation & Styling

### Morning Check-in
- [ ] Timeline structure complete
- [ ] 8 cycle boxes displaying
- [ ] Today: Add visual styling and states

### Development: Cycle Status Visualization (3-4 hours)

#### Define Color Scheme
```
COLORS = {
  'pending_bg':    '#E0E0E0',
  'pending_fg':    '#666666',
  'completed_bg':  '#4CAF50',
  'completed_fg':  '#FFFFFF',
  'current_border':'#2196F3',
  'ac_phase':      '#3498DB',
  't_phase':       '#9B59B6',
  'modified':      '#FF9800',
}
```

#### Style Pending Cycles
- [ ] Light gray background, cycle number visible, subtle border

#### Style Completed Cycles
- [ ] Green background, white text, checkmark symbol

#### Identify Current Cycle
- [ ] First cycle with status "Pending" = current
- [ ] If all completed → "Treatment Complete"

#### Style Current Cycle
- [ ] Highlight with colored border
- [ ] Make it stand out visually

#### Apply Styles Dynamically
- [ ] Update create_cycle_frame() to check status
- [ ] Test with 0, 3, and 8 completed cycles

### Development: Phase Visual Distinction (2-3 hours)
- [ ] AC Phase cycles (1-4): Blue accent
- [ ] T Phase cycles (5-8): Purple accent
- [ ] Phase labels with matching colors
- [ ] Visual separator between phase groups
- [ ] Accessibility check — don't rely only on color

### Development: Timeline Refresh & Integration (1-2 hours)
- [ ] Write refresh() method — reload and rebuild timeline
- [ ] Update dashboard.py to include timeline
- [ ] Test with multiple patients

### End of Day Activities
- [ ] Git commit: "Add timeline styling with status-based colors, phase distinction (US-007, US-008)"
- [ ] Trello: US-008 nearly complete

#### Expected Deliverables:
- Cycles styled by status
- Phase distinction complete
- Timeline refreshes properly

---

## DAY 13: Click Handling & Cycle Completion Dialog Planning

### Development: Cycle Click Handling (2-3 hours)
- [ ] Bind <Button-1> to cycle frames
- [ ] Write on_cycle_click(cycle_data) method
- [ ] Pending/current → open completion dialog
- [ ] Completed → show info
- [ ] Hover effects: cursor change, slight highlight

### Development: Cycle Completion Dialog Design (3-4 hours)

#### Create Dialog File
- [ ] Create src/views/components/cycle_completion_dialog.py
- [ ] CycleCompletionDialog class extending tk.Toplevel
- [ ] Modal, centered, non-resizable

#### Fields
- [ ] Cycle number (read-only display)
- [ ] Phase (read-only display)
- [ ] Date completed (Entry, YYYY-MM-DD, default today)
- [ ] Dose percentage (Combobox: 100%, 85%, 75%, 50%, Custom)
- [ ] Dose reason (Combobox, shown when dose < 100%)
- [ ] Notes (optional Entry)

#### Dose Reason Options
- Neutropenia, Neuropathy, Thrombocytopenia, Hepatotoxicity, Patient tolerance, Physician discretion, Other

#### Buttons
- [ ] Save and Cancel at bottom

### End of Day Activities
- [ ] Git commit: "Add cycle click handling and completion dialog layout (US-010 in progress)"

#### Expected Deliverables:
- Clickable cycles
- Dialog structure complete

---

## DAY 14: Cycle Completion Save Functionality

### Development: Dialog Validation (2-3 hours)
- [ ] get_form_data() method
- [ ] validate() method:
  - Date not empty, valid format, not future, not before treatment start
  - Dose valid (1-100)
  - Reason required if dose < 100%
- [ ] Display validation errors inline

### Development: Save Cycle Completion (3-4 hours)
- [ ] on_save() method
- [ ] Call update_cycle() with new status/date/dose/reason
- [ ] Close dialog on success
- [ ] Trigger timeline refresh (callback or direct call)
- [ ] Error handling for DB failures

### Development: Dose Modification Recording (1-2 hours)
- [ ] "Other" reason shows text entry
- [ ] Confirm all reason options appropriate for AC-T
- [ ] Dose < 100% highlights reason field

### End of Day Activities
- [ ] Full flow test: click cycle → complete → verify update
- [ ] Git commit: "Implement cycle completion save with validation and dose modification (US-010, US-011)"
- [ ] Trello: Move US-010 and US-011 to Done

#### Expected Deliverables:
- Cycle completion fully working
- Dose modifications saved
- US-010 and US-011 complete (9/14 pts)

---

## DAY 15: Dose Modification Indicators & Current Status

### Development: Modification Indicator (2-3 hours)
- [ ] Check dose_percent < 100 in create_cycle_frame()
- [ ] Add small warning label/icon (orange) to cycle frame
- [ ] Position in corner without obscuring cycle number
- [ ] Test: indicator only on modified cycles

### Development: Current Cycle Status Text (2-3 hours)
- [ ] Write method to determine current cycle and phase
- [ ] Add status label above or below timeline
- [ ] Format: "Current: Cycle X (AC Phase)"
- [ ] Treatment complete state: "Treatment Complete"
- [ ] Optional: show next planned date
- [ ] Update on timeline refresh

### End of Day Activities
- [ ] Git commit: "Add dose modification indicators and current cycle status (US-009, US-012)"
- [ ] Trello: Move US-009 and US-012 to Done (12/14 pts)

#### Expected Deliverables:
- Modification indicators working
- Current status text displayed
- US-009 and US-012 complete

---

## DAY 16: Full Dashboard Integration

### Development: Dashboard Layout with Timeline (3-4 hours)

#### Target Layout
```
┌──────────────────────────────────────────────┐
│ [<- Back]              Patient Name          │
│            Patient ID | Protocol | Start     │
├──────────────────────────────────────────────┤
│    Current: Cycle 3 (AC Phase)               │
│                                              │
│  [1] [2] [3] [4]    [5] [6] [7] [8]         │
│  ── AC Phase ──     ── T Phase ──            │
│                                              │
├──────────────────────────────────────────────┤
│  Latest Labs: (Coming in Sprint 3)           │
└──────────────────────────────────────────────┘
```

- [ ] Position timeline in dashboard content area
- [ ] Keep labs placeholder below timeline
- [ ] Ensure back button accessible
- [ ] Test responsive layout

### Development: Data Flow & Refresh Logic (2-3 hours)
- [ ] Trace patient selection → dashboard → timeline data flow
- [ ] Verify refresh after cycle completion
- [ ] Test multiple patients — no data bleed between them
- [ ] Edge cases: new patient (0 cycles), complete patient (8 cycles)

### Development: Dialog Polish (1-2 hours)
- [ ] Tab order, Enter key = Save, Escape = Cancel
- [ ] Focus first input on open
- [ ] Center dialog on parent

### End of Day Activities
- [ ] Full end-to-end test
- [ ] Git commit: "Complete dashboard integration with timeline and interaction polish"

#### Expected Deliverables:
- Dashboard layout complete
- Data flow solid
- Professional interaction feel

---

## DAY 17: Testing & Bug Fixing

### Testing: Story Acceptance Criteria (3-4 hours)

#### US-007 Test Checklist
- [ ] 8 cycles displayed
- [ ] Cycles 1-4 labeled "AC"
- [ ] Cycles 5-8 labeled "T"
- [ ] Completed cycles look different from pending
- [ ] Current cycle highlighted

#### US-008 Test Checklist
- [ ] Phases visually separated
- [ ] Phase labels visible
- [ ] Color coding by phase

#### US-009 Test Checklist
- [ ] Modified cycles show indicator
- [ ] Non-modified cycles clean

#### US-010 Test Checklist
- [ ] Click cycle opens dialog
- [ ] Can enter completion date
- [ ] Save updates cycle status
- [ ] Timeline updates immediately
- [ ] Data persists after restart

#### US-011 Test Checklist
- [ ] Dose percentage selectable
- [ ] Reason field appears when dose < 100%
- [ ] Reason required when dose < 100%
- [ ] Data saved to database

#### US-012 Test Checklist
- [ ] Status text displays
- [ ] Phase name shown
- [ ] Treatment complete state works
- [ ] Updates when switching patients

### Bug Fixing (3-4 hours)
- [ ] Prioritize: Critical / High / Medium / Low
- [ ] Fix critical bugs first, test immediately
- [ ] Fix high priority bugs
- [ ] Document deferred bugs for backlog

### End of Day Activities
- [ ] Git commit: "Sprint 2 bug fixes and testing improvements"
- [ ] Trello update based on test results

---

## DAY 18: Edge Cases & Polish

### Edge Case Testing (3-4 hours)
- [ ] New patient (0 cycles completed) — timeline all pending
- [ ] Fully completed treatment (8/8) — "Treatment Complete"
- [ ] All cycles modified — indicators visible, not cluttered
- [ ] Out-of-order completion — document behavior
- [ ] Date validation: future date, pre-treatment date, invalid format
- [ ] Dose validation: 0%, 1%, 200%
- [ ] Very long reason text
- [ ] Special characters in notes

### UI Polish (2-3 hours)
- [ ] Cycle boxes evenly sized and aligned
- [ ] Phase labels centered under groups
- [ ] Status text prominent
- [ ] Indicators correctly positioned
- [ ] Hover effects on cycles
- [ ] Consistent fonts, colors, spacing throughout

### Documentation (1-2 hours)
- [ ] Docstrings on timeline component methods
- [ ] Docstrings on cycle completion dialog
- [ ] README: add timeline feature to feature list

### End of Day Activities
- [ ] Git commit: "Sprint 2 edge case handling, UI polish, and documentation"

---

## DAY 19: Final Integration Testing & Sprint Prep

### Full Workflow Test
- [ ] Launch app — empty list
- [ ] Add patient PT-001
- [ ] Open dashboard — 8 pending cycles
- [ ] Complete cycle 1 (100% dose)
- [ ] Complete cycle 2 (80% dose, Neutropenia)
- [ ] Complete cycle 3 (100% dose)
- [ ] Navigate back and return — progress preserved
- [ ] Add second patient PT-002
- [ ] Verify PT-002 independent from PT-001
- [ ] Close and reopen — all data persisted

### Demo Preparation (2-3 hours)

#### Demo Script (~12 min)
1. **(1 min)** Sprint 2 goal intro
2. **(3 min)** Timeline visualization — 8 cycles, AC/T phases, color coding
3. **(3 min)** Complete a cycle — dialog, date, 100% dose, save, visual update
4. **(3 min)** Dose modification — 80% dose, reason dropdown, indicator on timeline
5. **(2 min)** Current status text, treatment complete state

- [ ] Practice demo twice, time it
- [ ] Prepare demo patients:
  - Patient 1: mid-treatment with one dose modification
  - Patient 2: early treatment (use for live completion demo)
  - Patient 3: fully complete treatment

### Code Cleanup
- [ ] Remove print statements and debug code
- [ ] Review all Sprint 2 files

### End of Day Activities
- [ ] Git commit: final Sprint 2 commit
- [ ] Optional tag: v0.2-sprint2-prerelease

---

## DAY 20: Sprint 2 Review & Retrospective

### Morning: Final Preparations (1 hour)
- [ ] Load demo test data
- [ ] Test app one final time
- [ ] Demo rehearsal — time it

### Sprint Review (Self) — 45-60 min
- [ ] Conduct full demo following script
- [ ] Story-by-story verification (all 6 stories)
- [ ] Sprint goal: achieved YES / NO
- [ ] Story points completed: ___/14
- [ ] Optional: record screen capture

### Sprint Retrospective (Self) — 30 min
- [ ] What went well? (3-5 items)
- [ ] What could be improved? (2-3 items)
- [ ] What will I do differently in Sprint 3? (1-2 actionable items)
- [ ] Velocity: ___/14 pts — compare to Sprint 1
- [ ] Sprint 3 capacity check (10 pts planned — lab values + charts)

### Afternoon: Sprint 2 Wrap-Up (2-3 hours)
- [ ] Final code cleanup
- [ ] Git tag: v0.2-sprint2
- [ ] Create docs/SPRINT_2_SUMMARY.md
- [ ] Trello: move all Sprint 2 cards to Done, set up Sprint 3

### Milestone M2 Check
- [ ] 8-cycle timeline displays
- [ ] Completed/pending states shown
- [ ] Cycles can be completed
- [ ] Dose modifications tracked
- [ ] Visual indicators present

### Expected Deliverables:
- Release tagged v0.2-sprint2
- Sprint 2 summary document
- Trello organized for Sprint 3
- Ready for Sprint 3: Lab Value Management
