# Sprint 4 Plan — Dashboard Integration & Validation

**Weeks 7–8 | Days 31–40**

---

## Sprint Goal

All components fully integrated into a unified dashboard, end-to-end workflows tested, stakeholder demos completed, and MVP validated for approval.

---

## Stories

| Story | Title | Points | Status |
|-------|-------|--------|--------|
| US-017 | View Patient Dashboard | 5 | To Do |
| US-018 | Patient Header Display | 1 | To Do |

**Total Story Points: 6**

---

## Why This Sprint Is Different

- Fewer story points (6) but significant non-development work
- Integration and polish focus
- Stakeholder-facing activities
- Transition from "building" to "validating"
- Setting up for post-MVP success

---

## Non-Story Work

| Activity | Days |
|----------|------|
| End-to-end integration testing | 34–35 |
| Bug fixes and polish | 36–37 |
| Documentation completion | 38 |
| Demo preparation | 38 |
| Stakeholder demo #1 | 39 |
| Stakeholder demo #2 | 40 |
| Feedback capture and processing | 40 |
| Final sign-off | 40 |

---

## Dependencies

| Sprint | Status |
|--------|--------|
| Sprint 1: Foundation | Done ✅ |
| Sprint 2: Timeline | Done ✅ |
| Sprint 3: Labs | Done ✅ |
| All components ready for integration | Confirmed ✅ |

---

## Success Criteria

- [ ] All features visible on single dashboard
- [ ] End-to-end workflow completes without errors
- [ ] Both oncologists provide positive feedback
- [ ] "Easy to understand" usability rating achieved
- [ ] Patient review time < 30 seconds
- [ ] MVP sign-off received

---

## Day-by-Day Plan

| Day | Focus |
|-----|-------|
| 31 | Sprint planning + dashboard layout design |
| 32 | Dashboard layout implementation |
| 33 | Patient header + component integration |
| 34 | End-to-end integration testing |
| 35 | Additional testing + bug identification |
| 36 | Bug fixes |
| 37 | UI polish + performance |
| 38 | Documentation + demo preparation |
| 39 | Stakeholder demo #1 |
| 40 | Stakeholder demo #2 + wrap-up |

---

## Story Acceptance Criteria

### US-017: View Patient Dashboard

- [ ] All components visible on one screen
- [ ] Patient header prominent
- [ ] Timeline visible
- [ ] Latest labs visible
- [ ] ANC chart visible
- [ ] Dashboard loads < 1 second
- [ ] No scrolling needed for critical info at 1920×1080
- [ ] Updates correctly when data changes

### US-018: Patient Header Display

- [ ] Patient name displayed prominently
- [ ] Patient ID visible
- [ ] Protocol type shown
- [ ] Treatment start date shown
- [ ] Header stays visible
- [ ] Correct patient shown

---

## Dashboard Layout Design

### Recommended Layout: Two-Row (Option A)

```
┌─────────────────────────────────────────────────────────────┐
│ [← Back]   PATIENT NAME - ID | Protocol | Start Date       │
├─────────────────────────────────────────────────────────────┤
│                Current: Cycle X (Phase)                     │
│   [1] [2] [3] [4]     |     [5] [6] [7] [8]                │
│     AC Phase                   T Phase                      │
├────────────────────────────┬────────────────────────────────┤
│    LATEST LABS             │        ANC TREND CHART         │
│    Date: Mar 15 (3d ago)   │   ┌──────────────────────┐     │
│    ANC: 1.8  ● Normal      │   │       ●              │     │
│    WBC: 4.5                │   │   ●       ●          │     │
│    PLT: 165                │   │ ────────── 1.5 ──────│     │
│                            │   │         ●            │     │
│    [+ Add Labs]            │   └──────────────────────┘     │
└────────────────────────────┴────────────────────────────────┘
```

**Grid configuration:**

| Row | Content | Weight |
|-----|---------|--------|
| 0 | Patient header | 0 (fixed) |
| 1 | Timeline | 0 (fixed) |
| 2 | Labs + Chart | 1 (expandable) |

Bottom section columns: Labs 35% | Chart 65%

### Alternate Layout: Three-Column (Option B)

```
┌─────────────────────────────────────────────────────────────┐
│ [← Back]   PATIENT NAME - ID | Protocol | Start Date       │
├─────────────────────────────────────────────────────────────┤
│ Timeline                    │ Labs      │ Chart            │
│ [Cycles 1-8]                │ ANC: 1.8  │ [Trend]          │
└─────────────────────────────┴───────────┴──────────────────┘
```

Option A is preferred: cleaner hierarchy, timeline gets full width.

---

## Patient Header Design

```
┌─────────────────────────────────────────────────────────────┐
│ [← Back to List]                         [Treatment Status] │
│                                                             │
│   JANE DOE                                                  │
│   ID: JD-001 │ Dose-Dense AC-T │ Started: January 15, 2024 │
└─────────────────────────────────────────────────────────────┘
```

**Typography:**

| Element | Size | Style |
|---------|------|-------|
| Patient name | FONT_TITLE (24–28pt) | Bold |
| Details row | FONT_LABEL (12–14pt) | Regular |
| Back button | FONT_BODY | Arrow symbol |

**Colors:** Name uses FG; details use FG_MUTED; background uses BG_ALT.

---

## DAY 31: Sprint Planning + Dashboard Layout Design

### Morning: Sprint Kickoff (45–60 min)

- Review Sprint 3 accomplishments — celebrate M3: Labs Working ✅
- Confirm overall progress: 75% complete
- Read Sprint 4 goal aloud; understand what "done" means for MVP
- Review US-017 and US-018 acceptance criteria
- Plan non-story work: integration testing, bug fixes, docs, demos
- Confirm stakeholder demo schedules with both oncologists
- Move US-017 to "In Progress"; create Trello cards for non-story work
- Start Sprint 4 section in PROJECT_LOG.md

**Deliverables:** Clear Sprint 4 plan, demo dates confirmed, Trello organized.

### Development: Dashboard Layout Design (4–5 hours)

- Audit current `src/views/dashboard.py` — list all integrated components
- Define layout requirements (1920×1080 primary, 1024×768 minimum)
- Sketch and finalize Option A two-row layout (see above)
- Decide on `grid` geometry manager (preferred over `pack` for complex layouts)
- Calculate component sizing:
  - Header: ~80px
  - Timeline: ~200px
  - Labs + Chart: ~400px
  - Total: ~680px — fits at both target resolutions
- Document spacing: 10–20px between sections, 10px inner padding

**Deliverables:** Finalized layout sketch with dimensions and ratios.

### Afternoon: Patient Header Design (2–3 hours)

- Review US-018 acceptance criteria
- Design header elements: back button, name, details row, separator
- Specify typography using existing font constants (FONT_TITLE, FONT_LABEL, etc.)
- Specify colors using palette (BG_ALT, FG, FG_MUTED)

**Deliverables:** Header design documented, typography and colors specified.

### End of Day

- Commit any planning documents
- Push to GitHub
- Update PROJECT_LOG.md

---

## DAY 32: Dashboard Layout Implementation

### Morning: Dashboard Grid Structure (3–4 hours)

- Open `src/views/dashboard.py`, review current code
- Create main container and configure grid rows/columns:

```python
self.grid_rowconfigure(0, weight=0)   # Header — fixed
self.grid_rowconfigure(1, weight=0)   # Timeline — fixed
self.grid_rowconfigure(2, weight=1)   # Bottom — expandable
self.grid_columnconfigure(0, weight=1)

self.bottom_frame.grid_columnconfigure(0, weight=1)  # Labs (35%)
self.bottom_frame.grid_columnconfigure(1, weight=2)  # Chart (65%)
```

- Create section frames: `header_frame`, `timeline_frame`, `bottom_frame`, `labs_frame`, `chart_frame`
- Add temporary colored backgrounds to verify grid proportions
- Test window resizing; verify components scale
- Remove test colors before committing

**Deliverables:** Grid structure working, resizing behaves correctly.

### Development: Component Placement (3–4 hours)

- Place patient header in `header_frame`
- Import and place `TimelineComponent` in `timeline_frame`
- Import and place `LatestLabsPanel` in `labs_frame`
- Import and place `ANCTrendChart` in `chart_frame`
- Place "Add Labs" button below labs panel
- Place back button in header area
- Test with patients that have no data, partial data, and full data
- Adjust spacing and padding

**Deliverables:** All components placed, layout looks correct.

### Development: Refresh Coordination (1–2 hours)

- Update `refresh()` to call refresh on all sub-components
- Update `set_patient(patient_id)` to pass patient to all components
- Test: add lab → all panels update; complete cycle → timeline and status update
- Test patient switching: open A, back to list, open B — verify correct data

**Deliverables:** Refresh coordination working, patient switching clean.

### End of Day

- Screenshot dashboard layout
- Commit: `"Added dashboard grid layout with component placement"`
- Push

---

## DAY 33: Patient Header + Integration Completion

### Morning: Patient Header Component (3–4 hours)

- Create `src/views/components/patient_header.py` — `PatientHeader(tk.Frame)`
- Parameters: `parent`, `controller`, `patient_data`
- Implement elements:
  - Back button ("← Back to List") — top-left, connected to navigation
  - Patient name — FONT_TITLE, FG, prominent
  - Details row — ID, Protocol, Start Date separated by `│`, FONT_LABEL, FG_MUTED
  - Format date as "January 15, 2024" (not raw ISO string)
  - Optional treatment status badge (top-right): "In Progress (Cycle 3 of 8)"
  - Separator line below header
- Write `update_display(patient_data)` method
- Test with long names, different protocols

**Deliverables:** PatientHeader component complete — US-018 done.

### Development: Dashboard Integration Finalization (2–3 hours)

- Replace old header in `dashboard.py` with `PatientHeader`
- Verify all 6 components present: header, timeline, labs, chart, add-labs button, back button
- Verify component communication: lab dialog → refresh labs + chart; cycle dialog → refresh timeline + header status
- Profile dashboard load; confirm < 1 second
- Test window resize at various sizes; enforce minimum size

**Deliverables:** Dashboard fully integrated, all components working together.

### Development: Final Polish Items (2–3 hours)

- Typography, color, spacing, alignment consistency check
- Verify all buttons provide click feedback
- Verify empty states: new patient, patient with cycles but no labs
- Verify keyboard navigation (Tab through interface, Escape returns to list)

**Deliverables:** Visual polish complete, edge cases handled.

### End of Day

- Commit: `"Added patient header component and dashboard integration"`
- Push
- Move US-017 and US-018 to Done ✅
- **Sprint 4: 6/6 story points complete!**

---

## DAY 34: End-to-End Integration Testing

### Master Test Workflow

Execute the complete workflow test below. Record pass/fail for each item. Document every failure as a bug report.

**Phase 1 — Application Startup**

| # | Test | Expected |
|---|------|----------|
| 1.1 | Launch application | Opens in < 3 seconds |
| 1.2 | Initial state | Empty list with "No patients" message |
| 1.3 | Window appearance | Centered, correct size, correct title |

**Phase 2 — Patient Management**

| # | Test | Expected |
|---|------|----------|
| 2.1 | Open Add Patient dialog | Dialog opens |
| 2.2 | Add patient PT-001 "John Smith" | Saved, dialog closes |
| 2.3 | Patient in list | John Smith visible, shows "0/8" |
| 2.4 | Add patient PT-002 "Jane Doe" | Saved, visible in list |
| 2.5 | Empty name validation | Error shown |
| 2.6 | Duplicate ID validation | "Patient ID already exists" error |

**Phase 3 — Dashboard Navigation**

| # | Test | Expected |
|---|------|----------|
| 3.1 | Open patient dashboard | Loads with patient data |
| 3.2 | Load time | < 1 second |
| 3.3 | Header fields | Name, ID, Protocol, Start Date all visible |
| 3.4 | Timeline | 8 cycles, all pending, Cycle 1 highlighted |
| 3.5 | Empty labs state | "No labs recorded yet" |
| 3.6 | Empty chart state | "No data" or hidden |
| 3.7 | Back navigation | Returns to patient list |

**Phase 4 — Cycle Completion**

| # | Test | Expected |
|---|------|----------|
| 4.1 | Open cycle dialog | Opens for Cycle 1 |
| 4.2 | Complete Cycle 1 at 100% | Cycle 1 marked complete |
| 4.3 | Timeline update | Cycle 1 green, Cycle 2 now current |
| 4.4 | Status update | "Current: Cycle 2 (AC Phase)" |
| 4.5 | Complete Cycle 2 at 80% (Neutropenia) | Saved with modification |
| 4.6 | Modification indicator | Warning icon on Cycle 2 |
| 4.7 | Complete Cycle 3 | Cycle 3 complete, now on Cycle 4 |

**Phase 5 — Lab Entry**

| # | Test | Expected |
|---|------|----------|
| 5.1 | Open Add Labs dialog | Dialog opens |
| 5.2 | Add labs: ANC 2.1, WBC 4.5, PLT 180 | Saved |
| 5.3 | Latest Labs panel | Shows values, date, "14 days ago" |
| 5.4 | ANC 2.1 color | Green (Normal) |
| 5.5 | Chart appearance | Single point visible |
| 5.6 | Add labs: ANC 1.2, WBC 3.8, PLT 150 | Chart has 2 points |
| 5.7 | Latest Labs updates | Shows ANC 1.2, "7 days ago" |
| 5.8 | ANC 1.2 color | Yellow (Mild neutropenia) |
| 5.9 | Chart trend | Line connecting points, threshold visible |
| 5.10 | Add labs: ANC 0.7 | Saved, orange/moderate color |
| 5.11 | Chart highlight | Orange point below threshold line |

**Phase 6 — Data Persistence**

| # | Test | Expected |
|---|------|----------|
| 6.1 | Close application | App closes cleanly |
| 6.2 | Reopen application | Opens normally |
| 6.3 | Patients exist | Both patients in list |
| 6.4 | Cycle data persisted | 3 cycles complete, Cycle 2 modification |
| 6.5 | Lab data persisted | 3 entries, chart shows all |

**Phase 7 — Multiple Patient Handling**

| # | Test | Expected |
|---|------|----------|
| 7.1 | Switch to Jane Doe | Dashboard shows Jane's data |
| 7.2 | Jane has no cycles | All 8 pending |
| 7.3 | Jane has no labs | "No labs recorded yet" |
| 7.4 | Add data to Jane | Both save correctly |
| 7.5 | Switch back to John Smith | John's data shown |
| 7.6 | No data mixing | Each patient shows only their data |

**Phase 8 — Edge Cases**

| # | Test | Expected |
|---|------|----------|
| 8.1 | Complete all 8 cycles | "Treatment Complete" displayed |
| 8.2 | Timeline all complete | All 8 cycles green |
| 8.3 | No current cycle | No cycle highlighted as current |

### Bug Report Template

```
BUG-XXX | Severity: Critical / High / Medium / Low
Component: [Patient List / Dashboard / Timeline / Labs / Chart]

Summary: [One-line description]

Steps to Reproduce:
1.
2.
3.

Expected: [What should happen]
Actual: [What actually happens]
```

**Severity Guidelines:**
- **Critical:** Feature completely broken, blocks usage
- **High:** Feature works but poorly, significant UX issue
- **Medium:** Visual issue, minor UX problem
- **Low:** Cosmetic, polish item

### End of Day

- Commit test documentation
- Commit: `"Added end-to-end integration test results"`
- Push

---

## DAY 35: Additional Testing + Bug Identification

### Performance Testing

| Test | Target | Record Actual |
|------|--------|---------------|
| App startup | < 3s | ___ |
| Dashboard load (empty patient) | < 1s | ___ |
| Dashboard load (full patient) | < 1s | ___ |
| Chart render (3 pts) | < 500ms | ___ |
| Chart render (20 pts) | < 500ms | ___ |
| Add lab → refresh | < 500ms | ___ |
| Complete cycle → refresh | < 500ms | ___ |

### Usability Testing

- **First-time user test:** Pretend you've never used the app. Can you add a patient, complete a cycle, add labs, and read the chart without guidance?
- **30-second review test:** Open a patient dashboard. In 30 seconds, can you determine current cycle, any dose modifications, latest ANC value, and ANC trend direction?
- **Error recovery test:** Intentionally make invalid entries. Are error messages helpful? Can you recover easily?
- **Accessibility quick check:** Keyboard-only navigation, text readability, color contrast.

### Edge Case Testing

| Scenario | Expected Behavior |
|----------|------------------|
| ANC = 0.0 | Accepted, red (Severe) |
| ANC = 0.01 | Accepted, red (Severe) |
| ANC = 15.0 | Accepted, green (Normal) |
| Negative ANC | Validation error |
| Future date | Validation error |
| Year 1900 | Validation error |
| Patient name 50 chars | Accepted, displays correctly |
| Patient with no data at all | All empty states shown |
| Patient with cycles, no labs | Labs panel shows empty state |
| All 8 cycles complete | Treatment complete state |
| Add labs after treatment complete | Still works |
| 20 patients in list | List usable, performance acceptable |

### Final Bug List Template

```
SPRINT 4 BUG LIST

CRITICAL (Fix immediately):
BUG-001: ...

HIGH (Fix before demo):
BUG-002: ...

MEDIUM (Fix if time allows):
BUG-003: ...

LOW (Post-MVP):
BUG-004: ...

Total: __ | Critical: __ | High: __ | Medium: __ | Low: __
```

### End of Day

- Commit bug reports
- Commit: `"Added additional testing results and bug list"`
- Push

---

## DAY 36: Bug Fixing Sprint

### Process for Each Bug

1. Reproduce the bug
2. Identify root cause
3. Implement fix
4. Test the fix
5. Verify no regression
6. Commit with bug reference in message

### Order of Attack

1. All **Critical** bugs first
2. All **High** priority bugs
3. **Medium** bugs — fix quick wins (< 30 min each), defer the rest

### Commit Format

`"Fixed BUG-XXX: [short description]"` — one commit per bug.

### End of Day Bug Fix Summary

```
Critical fixed: __/__
High fixed:     __/__
Medium fixed:   __/__
Deferred to v1.1: __ bugs
```

- Run quick regression pass through main workflow
- Push all commits

---

## DAY 37: UI Polish & Performance Optimization

### Visual Consistency Checklist

- [ ] All headings consistent size — uses FONT_TITLE / FONT_LABEL / FONT_BODY
- [ ] No hardcoded font sizes or colors anywhere in Sprint 4 code
- [ ] Colors use BG, BG_ALT, FG, FG_MUTED, SEPARATOR from palette
- [ ] Consistent margins (10–20px between sections) and inner padding (10px)
- [ ] Elements properly aligned — no jagged edges
- [ ] ANC color indicators correct on all panels

### Component Polish Checklist

| Component | Polish Item |
|-----------|-------------|
| Patient list | Row heights, column widths, empty state styled |
| Dashboard header | Name prominent, details readable, back button obvious |
| Timeline | Cycles evenly spaced, phase labels clear, modification icons visible |
| Labs panel | Values easy to scan, color indicators visible, date prominent |
| Chart | Legend readable, axis labels clear, threshold line visible |

### Interaction Refinement

- Buttons: normal / hover / pressed states working
- Click feedback immediate — no perceived lag
- Dialogs centered, fields aligned, error messages clear
- Window resize smooth, minimum size enforced

### Performance Optimization

- Cache frequently used data if queries are slow
- Reduce unnecessary refreshes
- Re-run performance tests after any optimization
- Verify nothing broken

### Screenshots to Capture

- Patient list (empty)
- Patient list (with patients)
- Dashboard (empty patient)
- Dashboard (full patient)
- Cycle completion dialog
- Add labs dialog
- Dashboard showing all four ANC colors

### End of Day

- Commit: `"Added Sprint 4 UI polish and visual refinements"`
- Push

---

## DAY 38: Documentation & Demo Preparation

### README Completion

Sections to complete:

- [ ] Features list
- [ ] Screenshots
- [ ] Installation instructions (virtualenv + pip + run command)
- [ ] Usage: adding a patient, completing a cycle, adding labs
- [ ] ANC color key
- [ ] Project structure
- [ ] Test data generation instructions

**Verify:** Follow your own installation instructions on a clean path. Fix any missing steps.

### User Guide Updates

Ensure `docs/USER_GUIDE.md` covers Sprint 4 additions:

- [ ] Dashboard overview (layout, all panels)
- [ ] Patient header fields
- [ ] Tips for 30-second patient review

### Demo Script

```
MVP DEMO — ~15-20 minutes

0:00  Intro (2 min)
      - Project background, problem being solved, agenda

0:02  Patient Management (3 min)
      - Show list, add new patient, demonstrate validation

0:05  Dashboard Overview (2 min)
      - Point out all panels: header, timeline, labs, chart

0:07  Cycle Tracking (4 min)
      - Explain timeline, complete a cycle, show dose modification,
        point out indicators, show current status update

0:11  Lab Management (4 min)
      - Add lab values, show latest labs panel, explain ANC colors,
        show chart update, explain threshold line

0:15  30-Second Review Demo (2 min)
      - Demonstrate full patient review in < 30 seconds

0:17  Wrap-Up (3 min)
      - Summary, acknowledge limitations, v1.1 discussion, questions
```

### Demo Data Setup

Create and verify three demo patients:

| Patient | State |
|---------|-------|
| Demo Patient 1 | Mid-treatment, mixed ANC values (shows all 4 colors) |
| Demo Patient 2 | Early treatment (for live cycle completion during demo) |
| Demo Patient 3 | All 8 cycles complete |

Back up demo database before each demo day.

### Feedback Collection Form

```
STAKEHOLDER FEEDBACK FORM

Stakeholder: _______________  Date: _______________

Overall Impression:
☐ Very Positive  ☐ Positive  ☐ Neutral  ☐ Needs Work

Usability:
☐ Easy to understand  ☐ Somewhat easy  ☐ Confusing

Would this save time?
☐ Definitely  ☐ Probably  ☐ Unsure  ☐ No

30-Second Review Test: ___ seconds  ☐ Pass  ☐ Close  ☐ Fail

Key Feedback:
1.
2.
3.

Requested Features (v1.1):
1.
2.

Concerns:
1.

Approval:
☐ Approved for MVP  ☐ Needs changes first  ☐ Major revision needed

Signature: _______________
```

### Anticipated Questions & Honest Answers

| Question | Answer |
|----------|--------|
| Can it connect to our EHR? | Not in v1.0 — planned for v1.1 roadmap |
| Can multiple users access it? | Single-user desktop app; multi-user is a v1.1 consideration |
| What about other regimens? | AC-T only in v1.0 — framework allows extension |
| Is patient data secure? | Local SQLite; no network transmission in v1.0 |

### Technical Preparation

- [ ] Test on demo machine (if different from dev machine)
- [ ] Verify all dependencies installed on demo machine
- [ ] Test screen sharing if demo is remote
- [ ] Check display resolution settings (1920×1080 preferred)
- [ ] Prepare video recording as backup
- [ ] Calendar invites sent to both oncologists

### End of Day

- Commit all documentation updates
- Commit: `"Added Sprint 4 documentation and demo preparation materials"`
- Push

---

## DAY 39: Stakeholder Demo #1

### Pre-Demo Setup (1–2 hours before)

- [ ] Launch application — confirm it opens cleanly
- [ ] Verify demo data is loaded and correct
- [ ] Close unnecessary applications
- [ ] Set display for presentation (resolution, font scaling)
- [ ] Test screen sharing / audio if remote
- [ ] Review demo script one final time

### Demo Execution (60–90 min)

Follow demo script. Key points to emphasize:
- 30-second patient review time savings
- Visual clarity of ANC color coding
- Dose modification tracking at a glance

For unknown questions: "That's a great question — I'll add it to the v1.1 discussion."

### Post-Demo: Feedback Capture (30 min)

- Complete feedback form immediately after
- Write detailed notes while fresh
- Document all suggestions, concerns, and approval status

### Demo #1 Summary Template

```
DEMO #1 SUMMARY

Stakeholder: _______________
Date/Time: _______________  Duration: ___ min

Overall Reception: ☐ Very Positive  ☐ Positive  ☐ Mixed  ☐ Needs Work

Key Positive Feedback:
1.
2.
3.

Suggestions/Requests:
1.
2.

30-Second Review: ___ seconds  ☐ Passed  ☐ Close  ☐ Failed

Approval: ☐ Approved  ☐ Conditional  ☐ Changes needed

Required Changes (if any):
1.

Follow-up Actions:
1.
```

### Afternoon: Process Feedback + Prepare for Demo #2

- Categorize feedback: positive / quick fixes / v1.1 features / concerns
- Implement any critical quick fixes; test thoroughly before committing
- Adjust demo script based on what resonated or confused
- Confirm Demo #2 logistics

### End of Day

- Commit any quick fixes: `"Fixed post-demo #1 issues"`
- Push
- Log demo results in PROJECT_LOG.md

---

## DAY 40: Stakeholder Demo #2 + Project Wrap-Up

### Demo #2 Execution

Same structure as Demo #1. Incorporate Demo #1 learnings:
- Emphasize points that resonated
- Clarify any areas of confusion
- Be prepared for different questions

### Post-Demo: Compile All Feedback

```
MVP APPROVAL STATUS

Stakeholder 1: ☐ Approved  ☐ Conditional  ☐ Not approved
Stakeholder 2: ☐ Approved  ☐ Conditional  ☐ Not approved

OVERALL MVP STATUS: ☐ APPROVED  ☐ NEEDS WORK

Conditions (if any):
1.

Sign-off: ☐ Verbal  ☐ Written  ☐ Pending
```

### Sprint 4 Story Verification

```
US-017: View Patient Dashboard (5 pts)
☐ All components integrated on one screen
☐ Layout correct at 1920x1080 and 1024x768
☐ Loads < 1 second
☐ Updates correctly when data changes
STATUS: ☐ DONE  ☐ NOT DONE

US-018: Patient Header Display (1 pt)
☐ Name prominent
☐ ID visible
☐ Protocol shown
☐ Start date shown
STATUS: ☐ DONE  ☐ NOT DONE

SPRINT 4: ___/6 points
```

### Sprint 4 Retrospective

**Metrics to record:**
- Story points planned vs. delivered
- Bugs found and fixed
- Performance test results
- Demo outcomes

**Retro questions:**
- What went well?
- What could be improved?
- What would you do differently next sprint?

### Final Project Documentation

**Create `docs/PROJECT_SUMMARY.md`:**

```
# Project Summary — AC-T Chemotherapy Dashboard v1.0

Timeline: [Start Date] → [End Date] — [X] weeks
Total story points: 50 (US-001 through US-022)

Milestones:
M1: Foundation Complete ✅
M2: Timeline Working ✅
M3: Labs Working ✅
M4: MVP Feature Complete ✅
M5: MVP Validated ✅

Velocity:
Sprint 1: 20 pts
Sprint 2: 14 pts
Sprint 3: 10 pts
Sprint 4:  6 pts

Stakeholder sign-off: ☐ Received  Date: ___
```

**Create `docs/BACKLOG_V1_1.md`:**

Compile all stakeholder-requested features with rough priority:

| Feature | Source | Priority |
|---------|--------|----------|
| Edit / delete patients | Feedback | High |
| Toxicity tracking | Feedback | High |
| CSV import / export | Feedback | Medium |
| Multi-user support | Feedback | Medium |
| Alert system | Feedback | Medium |
| Enhanced reporting | Feedback | Low |
| EHR integration | Feedback | Low |
| Other regimens | Feedback | Low |
| Mobile access | Feedback | Low |

### Final Repository Cleanup

- [ ] All code committed and pushed
- [ ] Tag release: `git tag v1.0.0 && git push origin v1.0.0`
- [ ] README complete with screenshots
- [ ] All sprint summaries in `docs/`
- [ ] No debug prints, temp files, or test databases committed

### Project Completion Checklist

```
Code & Repository:
☐ All code committed
☐ Release tagged v1.0.0
☐ README complete
☐ Code documented

Documentation:
☐ User guide complete
☐ Project summary written
☐ Sprint summaries archived (1–4)
☐ v1.1 backlog created

Stakeholders:
☐ Demo #1 completed
☐ Demo #2 completed
☐ Feedback documented
☐ Approval obtained
☐ Thank you notes sent

Personal:
☐ Daily logs complete
☐ Lessons learned documented
☐ Celebrated!
```

---

## Milestones

| Milestone | Target Day | Description |
|-----------|-----------|-------------|
| M4: MVP Feature Complete | Day 33 | All 22 stories implemented |
| M5: MVP Validated | Day 40 | Stakeholder approval received |

---

## Post-MVP: Potential v1.1 Features

Based on anticipated feedback — prioritize after demos:

- Edit / delete patients
- Toxicity tracking
- Alert system for low ANC
- CSV import / export
- Enhanced reporting / print view
- Search / filter patient list
- Multi-user support
- Web deployment
- EHR integration
- Other chemotherapy regimens
- Mobile access
