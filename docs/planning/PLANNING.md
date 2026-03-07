# COMPLETE PROJECT PLANNING DOCUMENT
## Breast Cancer AC-T Regimen Chemotherapy Dashboard

**Version:** 1.0  
**Date:** [Current Date]  
**Author:** [Your Name]  
**Status:** Final

---

## TABLE OF CONTENTS

1. [Project Scope](#phase-1--project-scope)
2. [User Research](#phase-2--user-research)
3. [Requirements Specification](#phase-3--requirements-specification)
4. [Feature Prioritization & MVP](#phase-4--feature-prioritization--mvp)
5. [User Stories & Use Cases](#phase-5--user-stories--use-cases)
6. [Timeline & Milestones](#phase-6--timeline--milestones)
7. [Methodology](#phase-7--methodology)
8. [Master Checklist](#master-checklist)

---

# PHASE 1 — PROJECT SCOPE

## 1. PROBLEM & SOLUTION STATEMENTS

### 1.1 Problem Statement

Healthcare providers (oncologists and oncology nurses) managing breast cancer patients on the AC-T chemotherapy regimen currently lack a **consolidated, visual tool** to track treatment progress at-a-glance.

**Current Pain Points:**
- Treatment data is scattered across EHR notes, paper flowsheets, or mental recall
- Reviewing a patient's cycle history, dose modifications, and toxicities requires **manual chart review taking 3-5+ minutes per patient**
- No quick way to visualize treatment trajectory (on track vs. delayed, dose reductions over time)
- Difficult to spot patterns across treatment cycles (e.g., recurring neutropenia requiring G-CSF)
- During clinic, providers need rapid access to "where is this patient in treatment?"

**Who Experiences This:**
- **Primary**: Oncologists reviewing patient status before/during appointments
- **Secondary**: Oncology nurses coordinating infusion schedules and monitoring toxicities

**Quantified Impact:**
- [ASSUMPTION] Providers spend ~3-5 minutes per patient reviewing scattered treatment data
- [ASSUMPTION] A typical oncologist sees 10-20 breast cancer patients on AC-T per week
- Potential time savings: **30-100 minutes/week** if reduced to <30 seconds per patient

### 1.2 Proposed Solution

A **single-user desktop application** built in Python that provides:
- A clean dashboard displaying AC-T treatment progress for individual patients
- Visual representation of 8-cycle protocol completion (4 AC cycles + 4 T cycles)
- Key metrics at-a-glance: current cycle, next treatment date, dose modifications, critical lab values, toxicity flags
- Simple data entry or import for synthetic/de-identified patient data

**Why This Solution:**

| Alternative | Why Dashboard is Better |
|-------------|------------------------|
| Spreadsheet tracking | No visualization, manual updates, easy to break formulas |
| EHR alone | Data scattered across notes, no AC-T-specific view |
| Paper flowsheets | Not digital, hard to share, no automatic calculations |
| Commercial oncology software | Expensive, overkill for focused AC-T tracking |

### 1.3 Definition of Success (Launch Criteria)

| Success Metric | Target | Measurement |
|----------------|--------|-------------|
| Time to review patient status | < 30 seconds | Timed observation with oncologist |
| Usability rating | "Easy to understand" from both oncologists | Verbal feedback |
| Core functionality complete | All 8 cycles trackable with key data points | Feature checklist |
| Development feasibility | Buildable by solo developer | Completed within timeline |
| Stakeholder approval | Both oncologists confirm it meets their needs | Sign-off |

---

## 2. SMART OBJECTIVES

```
OBJ-001: Deliver a functional MVP dashboard displaying AC-T cycle progress 
         for at least 5 synthetic patients by end of Week 6.

OBJ-002: Reduce patient treatment status review time from ~3-5 minutes to 
         <30 seconds, validated by oncologist feedback upon MVP completion.

OBJ-003: Achieve "easy to understand" usability rating from both supporting 
         oncologists during MVP demo session.

OBJ-004: Implement visual indicators for treatment delays, dose modifications, 
         and critical toxicities (neutropenia) by end of Week 5.

OBJ-005: Complete development using only free/open-source Python tools with 
         $0 software costs.
```

---

## 3. SCOPE BOUNDARIES

| IN SCOPE (v1.0 MVP) | OUT OF SCOPE (v1.0) |
|------------------------|------------------------|
| AC-T regimen tracking ONLY (8 cycles) | Other chemotherapy regimens |
| Single-user desktop application | Multi-user/web deployment |
| Manual data entry + CSV import | EHR/EMR integration |
| Synthetic/de-identified patient data | Real patient data (PHI) |
| Individual patient dashboard view | Cross-patient analytics/reporting |
| Cycle completion tracking | Appointment scheduling |
| Dose modification logging | Automated dose calculations |
| Key lab values (ANC, WBC, platelets) | Full lab panel integration |
| Critical toxicity flags (neutropenia, neuropathy) | Comprehensive adverse event tracking |
| Visual progress indicators | Printable reports |
| Basic treatment date tracking | Calendar/reminder integrations |
| Local data storage (SQLite/JSON) | Cloud storage or sync |
| Windows/Mac/Linux support via Python | Mobile app |

---

## 4. CONSTRAINTS, ASSUMPTIONS & DEPENDENCIES

### CONSTRAINTS:

| Type | Constraint | Impact |
|------|------------|--------|
| **Budget** | ~$0 (no paid tools/services) | Must use open-source only |
| **Team** | Solo developer | Limited capacity; must prioritize ruthlessly |
| **Skills** | Python proficiency assumed | GUI framework may require learning curve |
| **Timeline** | Flexible but targeting ~6-8 weeks | Keeps scope minimal |
| **Regulatory** | Using synthetic data only | No HIPAA compliance required for v1.0 |
| **Platform** | Desktop application | Simpler than web; no deployment infrastructure |

### ASSUMPTIONS:

```
[ASSUMPTION] AC-T protocol follows standard 8-cycle structure 
   (4 AC + 4 T, every 2-3 weeks). Variations exist but will not be 
   modeled in v1.0.

[ASSUMPTION] Oncologists are comfortable with basic desktop software 
   and do not require mobile access.

[ASSUMPTION] Synthetic data can be generated to realistically 
   represent AC-T treatment patterns (will create 5-10 sample patients).

[ASSUMPTION] Time savings estimate (3-5 min → 30 sec) is based on 
   anecdotal understanding; actual baseline should be validated with 
   oncologists.

[ASSUMPTION] A local desktop app with local storage is acceptable; 
   no need for cloud backup or multi-device sync.

[ASSUMPTION] Both oncologists have similar needs; no conflicting 
   requirements expected.
```

### DEPENDENCIES:

| Dependency | Type | Risk if Unavailable |
|------------|------|---------------------|
| Python 3.9+ | Technical | None (widely available) |
| GUI framework (Tkinter/PyQt) | Technical | Low (fallback options exist) |
| Oncologist availability for feedback | Human | Medium — delays validation |
| Sample AC-T protocol documentation | Domain | Low — oncologists can provide |
| Synthetic data generation | Data | Low — can create manually |

---

## 5. STAKEHOLDERS

| Role | Name/Description | Interest | Involvement Level |
|------|------------------|----------|-------------------|
| Developer | You | Build the application | High (daily) |
| Domain Expert 1 | Oncologist #1 | Define requirements, validate usefulness | Medium (weekly feedback) |
| Domain Expert 2 | Oncologist #2 | Secondary validation, edge cases | Low-Medium (bi-weekly) |
| End Users | Same oncologists + nurses | Use the final product | Medium (testing) |

---

# PHASE 2 — USER RESEARCH

## 1. USER SEGMENTATION

### Primary User Group

| Attribute | Details |
|-----------|---------|
| **Role** | Medical Oncologist |
| **Description** | Physician specializing in cancer treatment who prescribes and monitors chemotherapy regimens. Reviews patient status before/during clinic visits. Makes decisions about dose modifications, treatment delays, and toxicity management. |
| **Technical Proficiency** | Intermediate — Comfortable with EHR systems and clinical software; less experienced with custom/non-standard applications |
| **Device/Platform** | Desktop computer (clinic workstation), Windows or Mac |
| **Usage Context** | Before patient appointments (1-2 min prep), during appointments (quick reference), after clinic (review/documentation) |
| **Frequency of Use** | Multiple times daily during clinic days; 10-20 AC-T patients per week |

### Secondary User Group

| Attribute | Details |
|-----------|---------|
| **Role** | Oncology Nurse / Infusion Nurse |
| **Description** | Registered nurse specializing in oncology care. Coordinates infusion appointments, administers chemotherapy, monitors patients during treatment, documents vital signs and adverse reactions. |
| **Technical Proficiency** | Intermediate — Heavy EHR users; familiar with flowsheets and treatment documentation |
| **Device/Platform** | Desktop computer (nursing station), possibly shared workstation |
| **Usage Context** | Pre-infusion review, during infusion monitoring, post-infusion documentation |
| **Frequency of Use** | Daily; manages multiple patients per infusion session |

---

## 2. USER PERSONAS

### PERSONA 1: Dr. Maria Santos

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PERSONA: Dr. Maria Santos
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Age: 45
Occupation: Medical Oncologist, Breast Cancer Specialist
Tech Skills: Intermediate
Devices: Desktop (clinic), laptop (home for after-hours review)

Background:
Dr. Santos has been practicing oncology for 15 years and sees 60-80 
patients per week across multiple cancer types. Approximately 20% of 
her current caseload are breast cancer patients on AC-T or similar 
regimens. She's efficient but frustrated by how long it takes to 
piece together a patient's treatment history from scattered EHR notes.

Goals:
- Review any patient's AC-T status in under 30 seconds before walking 
  into the exam room
- Quickly identify if dose modifications were made in previous cycles 
  and why
- Spot patterns (e.g., "this patient always nadirs hard on day 10") 
  without re-reading old notes
- Explain treatment progress to patients using simple visuals

Frustrations:
- "I waste 3-4 minutes per patient clicking through old notes to find 
   where they are in treatment"
- "The EHR shows me everything EXCEPT a clean summary of the chemo 
   cycles"
- "I sometimes forget a dose was reduced two cycles ago and have to 
   look it up again"
- "When patients ask 'how much more do I have?', I have to count 
   cycles in my head"

Quote: 
"I don't need fancy. I need fast and accurate. Show me the cycles, 
show me the problems, done."
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### PERSONA 2: James "Jimmy" Okonkwo, RN

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PERSONA: James "Jimmy" Okonkwo, RN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Age: 32
Occupation: Oncology Infusion Nurse
Tech Skills: Intermediate
Devices: Desktop at nursing station (shared workstation)

Background:
Jimmy has worked in oncology infusion for 6 years. He manages 4-6 
patients per infusion shift, administering chemotherapy and monitoring 
for adverse reactions. He's detail-oriented and takes pride in catching 
potential issues before they become problems. He's comfortable with 
the EHR but often frustrated that key treatment information is buried 
in physician notes he doesn't have time to read.

Goals:
- Confirm patient is cleared for today's infusion (labs acceptable, 
  no contraindications)
- Know which cycle this is and whether any modifications apply
- Track toxicities reported in previous cycles to watch for patterns
- Document today's infusion efficiently

Frustrations:
- "I have to ask the patient which cycle they're on because it's not 
   obvious in the chart"
- "Sometimes dose reductions are in a note from last month that I 
   don't have time to find"
- "I want to see the trend — is their ANC getting worse each cycle 
   or recovering?"
- "The doctor and I sometimes have different information because 
   we're looking at different parts of the chart"

Quote: 
"If I can see the whole treatment on one screen, I can do my job 
better and safer."
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 3. USER NEEDS & PAIN POINTS

| Need Type | Description | Current Pain Point | Priority |
|-----------|-------------|-------------------|----------|
| **Functional** | See current cycle number (1-8) instantly | Must count through notes or ask patient | HIGH |
| **Functional** | View all 8 cycles in one visual timeline | No consolidated view exists; data scattered | HIGH |
| **Functional** | Track dose modifications per cycle | Buried in narrative notes; easy to miss | HIGH |
| **Functional** | Monitor key labs (ANC, WBC, platelets) trend | Must manually compare across visits | HIGH |
| **Functional** | Flag critical toxicities (neutropenia, neuropathy) | Relies on memory or re-reading notes | MEDIUM |
| **Functional** | See next scheduled treatment date | Often in separate scheduling system | MEDIUM |
| **Functional** | Record treatment delays and reasons | Inconsistently documented | MEDIUM |
| **Functional** | Import existing patient data easily | No current solution; would be manual | MEDIUM |
| **Emotional** | Feel confident patient data is accurate and complete | Anxiety about missing something in chart | HIGH |
| **Emotional** | Reduce cognitive load during busy clinic | Mental fatigue from information hunting | HIGH |
| **Emotional** | Feel prepared before entering exam room | Rushed preparation leads to stress | MEDIUM |
| **Social** | Explain treatment progress clearly to patients | Hard to visualize verbally | MEDIUM |
| **Social** | Share consistent information between MD and RN | Discrepancies cause confusion | MEDIUM |

---

## 4. USER JOURNEY MAP — Primary Persona (Dr. Maria Santos)

### Journey: Review Patient Before Appointment

| Stage | Actions | Touchpoints | Thoughts | Emotions | Pain Points | Opportunities |
|-------|---------|-------------|----------|----------|-------------|---------------|
| **1. PREPARE** | Opens AC-T Dashboard app before clinic | Desktop app icon | "Let me check on Mrs. Johnson before I see her" | Neutral, focused | App should launch fast | Quick launch, remember window position |
| **2. FIND PATIENT** | Views patient list, locates patient | Patient list view | "Where is she... there" | Efficient | List should be scannable | Alphabetical sort, search (future) |
| **3. SELECT** | Clicks on patient row | Patient list → Dashboard | "Let's see her status" | Anticipating | Click should be responsive | Instant feedback on selection |
| **4. ORIENT** | Sees patient header, confirms identity | Dashboard header | "Yes, this is Mrs. Johnson, started in January" | Confident | Must confirm right patient | Clear prominent name/ID |
| **5. CHECK PROGRESS** | Views treatment timeline | Timeline visualization | "She's on cycle 5, just started Taxol, good" | Informed | Cycle status must be instant to see | Visual timeline with clear states |
| **6. CHECK DOSES** | Scans for dose modification indicators | Timeline icons | "No dose reductions, she's tolerating well" | Reassured | Mods should be visible without clicking | Icons/markers on timeline |
| **7. CHECK LABS** | Views latest ANC value with color | Latest labs panel | "ANC is 1.8, she's good to go" | Relieved | ANC must be immediately visible | Color-coded, prominent display |
| **8. CHECK TREND** | Glances at ANC trend chart | Trend chart | "Counts have been stable, no concerning pattern" | Confident | Chart should be readable at a glance | Clear threshold line, simple chart |
| **9. CONCLUDE** | Synthesizes information mentally | Full dashboard | "She's doing well, on track, no issues" | Satisfied, prepared | All info should be on one screen | Integrated dashboard design |
| **10. PROCEED** | Walks into exam room | Physical (leaves computer) | "I'm ready to see her" | Confident, efficient | — | Time saved: 3-5 min → 30 sec |

---

## 5. RESEARCH RECOMMENDATIONS

| # | Method | What to Ask / Look For | Expected Insight | Priority |
|---|--------|----------------------|------------------|----------|
| **R1** | **Stakeholder Interview** (Oncologist #1) | "Walk me through how you review an AC-T patient before an appointment. What do you click on? What frustrates you?" | Exact current workflow; specific pain points; must-have data fields | HIGH |
| **R2** | **Stakeholder Interview** (Oncologist #2) | Same questions + "What would make you actually use a new tool vs. ignoring it?" | Adoption barriers; validation of persona | HIGH |
| **R3** | **Workflow Observation** | If possible, shadow oncologist during 2-3 patient preps (or have them screen-share) | Real vs. reported behavior; hidden workarounds | MEDIUM |
| **R4** | **Data Field Validation** | Show oncologists a draft list of data fields; ask "What's missing? What's unnecessary?" | Finalize data model; avoid building wrong fields | HIGH |
| **R5** | **Competitor/Alternative Review** | Search for existing oncology dashboards, chemo tracking tools (even screenshots) | UI patterns; standard features; differentiation | MEDIUM |
| **R6** | **Nurse Input** (if accessible) | Brief interview with an oncology nurse: "What do you need to know before infusion?" | Validate secondary persona; identify nurse-specific needs | LOW |

---

# PHASE 3 — REQUIREMENTS SPECIFICATION

## 1. FUNCTIONAL REQUIREMENTS

### 1.1 Patient Management

#### FR-001: Add New Patient

**User Story:** As an oncologist, I want to add a new patient to the system, so that I can begin tracking their AC-T treatment.

**Priority:** CRITICAL

**Acceptance Criteria:**
```
Scenario: Successfully add a new patient
  Given I am on the main dashboard
  When I click "Add Patient" button
  And I enter valid patient information
  And I click "Save"
  Then the patient is added to the patient list
  And I see a confirmation message

Scenario: Prevent duplicate patient ID
  Given a patient with ID "PT-001" already exists
  When I try to add a new patient with ID "PT-001"
  Then I see an error message "Patient ID already exists"
  And the patient is not added
```

**Business Rules:**
- Patient ID must be unique within the system
- Patient ID format: alphanumeric, 3-20 characters
- AC-T Start Date cannot be in the future
- Protocol type must be selected: "Dose-Dense AC-T" or "Standard AC-T"

**Data:**

| Input | Output | Validation |
|-------|--------|------------|
| Patient ID | Stored in DB | Required, unique, 3-20 chars |
| Patient Name/Initials | Stored in DB | Required, 1-50 chars |
| AC-T Start Date | Stored in DB | Required, valid date ≤ today |
| Protocol Type | Stored in DB | Required, enum value |

---

#### FR-002: View Patient List

**User Story:** As an oncologist, I want to see a list of all my patients, so that I can quickly select one to review.

**Priority:** CRITICAL

**Acceptance Criteria:**
```
Scenario: View all patients
  Given I have 5 patients in the system
  When I open the application
  Then I see a list showing all 5 patients
  And each entry shows: Patient ID, Name, Current Cycle, Status

Scenario: Empty state
  Given I have no patients in the system
  When I open the application
  Then I see a message "No patients yet. Click 'Add Patient' to start."
```

---

### 1.2 Treatment Cycle Tracking

#### FR-005: View Treatment Timeline

**User Story:** As an oncologist, I want to see a visual timeline of all 8 AC-T treatment cycles, so that I can instantly understand where the patient is in their treatment.

**Priority:** CRITICAL

**Acceptance Criteria:**
```
Scenario: View 8-cycle timeline
  Given I am viewing a patient who has completed 3 cycles
  When the dashboard loads
  Then I see a visual timeline showing 8 cycles
  And cycles 1-4 are labeled "AC"
  And cycles 5-8 are labeled "T"
  And completed cycles are marked as completed
  And the current/next cycle is highlighted
```

---

#### FR-006: Record Cycle Completion

**User Story:** As an oncology nurse, I want to record when a treatment cycle is completed, so that the system reflects current treatment status.

**Priority:** CRITICAL

**Acceptance Criteria:**
```
Scenario: Mark cycle as completed
  Given I am viewing a patient with Cycle 3 as pending
  When I click on Cycle 3
  And I enter the actual administration date
  And I click "Save"
  Then Cycle 3 status changes to "Completed"
  And Cycle 4 becomes the current cycle
```

---

#### FR-008: Record Dose Modification

**User Story:** As an oncologist, I want to record dose modifications for a cycle, so that I can track cumulative dose reductions over the treatment course.

**Priority:** CRITICAL

**Acceptance Criteria:**
```
Scenario: Record dose reduction
  Given I am recording Cycle 3 completion
  When I set dose percentage to 80%
  And I select reason "Neutropenia - required dose reduction"
  Then Cycle 3 shows dose: 80%
  And the timeline shows a modification indicator
```

---

### 1.3 Lab Value Tracking

#### FR-010: Record Lab Values

**User Story:** As an oncology nurse, I want to record lab values for a patient, so that the oncologist can review blood counts and trends.

**Priority:** CRITICAL

**Acceptance Criteria:**
```
Scenario: Add new lab values
  Given I am viewing a patient dashboard
  When I click "Add Labs" button
  And I enter: Date=today, ANC=1.8, WBC=4.5, Platelets=165
  And I click "Save"
  Then the lab values are saved
  And the "Latest Labs" panel updates
  And the lab trend chart updates
```

**Data:**

| Field | Type | Validation | Default |
|-------|------|------------|---------|
| Lab Date | Date | Required, ≤ today | Today |
| ANC | Decimal | Required, 0.0-20.0 | Empty |
| WBC | Decimal | Optional, 0.0-50.0 | Empty |
| Platelets | Integer | Optional, 0-1000 | Empty |

---

#### FR-011: View Lab Trend Chart

**User Story:** As an oncologist, I want to see a visual chart of lab values over time, so that I can quickly identify trends like worsening neutropenia.

**Priority:** CRITICAL

**Acceptance Criteria:**
```
Scenario: View ANC trend
  Given a patient has lab values recorded for 4 dates
  When I view the patient dashboard
  Then I see a line chart showing ANC over time
  And there is a reference line at ANC = 1.5
  And data points below threshold are highlighted
```

---

#### FR-012: View Most Recent Labs

**User Story:** As an oncologist, I want to see the most recent lab values prominently on the dashboard, so that I immediately know the patient's current blood counts.

**Priority:** CRITICAL

**Acceptance Criteria:**
```
Scenario: Display latest labs
  Given a patient has lab values recorded
  When I view the dashboard
  Then I see a "Latest Labs" panel showing:
    - Lab date
    - ANC value with color indicator
    - WBC, Platelets values
```

---

### 1.4 Dashboard & Visualization

#### FR-015: Patient Dashboard Overview

**User Story:** As an oncologist, I want a single dashboard view that shows everything important about a patient's AC-T treatment, so that I can review their status in under 30 seconds.

**Priority:** CRITICAL

**Acceptance Criteria:**
```
Scenario: Load complete dashboard
  Given I select a patient
  When the dashboard loads
  Then I see in ONE view (no scrolling):
    - Patient header (name, ID, protocol)
    - Treatment timeline (8 cycles)
    - Latest labs panel
    - Lab trend chart
  And the dashboard loads in < 2 seconds
```

---

### 1.5 Data Management

#### FR-019: Data Persistence (Auto-Save)

**User Story:** As a user, I want my data to be saved automatically, so that I don't lose information if I close the application.

**Priority:** CRITICAL

**Acceptance Criteria:**
```
Scenario: Data persists after restart
  Given I have added 3 patients with cycle and lab data
  When I close and reopen the application
  Then all 3 patients are still present
  And all their data is intact
```

---

## 2. NON-FUNCTIONAL REQUIREMENTS

### 2.1 Performance

```
PERFORMANCE:
[x] Application launch time: < 3 seconds
[x] Dashboard load time: < 1 second
[x] UI responsiveness: All clicks respond within 200ms
[x] Chart rendering: < 500ms
[x] Memory usage: < 200MB RAM
[x] Database size: Support up to 100 patients (< 10MB)
```

### 2.2 Reliability

```
RELIABILITY:
[x] Data integrity: Zero data loss under normal operation
[x] Crash recovery: Graceful handling of errors
[x] Uptime target: N/A (desktop app)
[x] Error handling: User-friendly error messages
[x] Logging: Errors logged to local file
```

### 2.3 Security

```
SECURITY:
[x] Authentication: None required (single-user, synthetic data)
[x] Encryption at rest: None (synthetic data only)
[x] Compliance: No PHI, no HIPAA compliance required for v1.0
[x] Data location: All data stored locally on user's machine

[RISK]: If future versions use real patient data, security 
   requirements must be completely re-evaluated.
```

### 2.4 Usability

```
USABILITY:
[x] Accessibility: Basic keyboard navigation support
[x] Font size: Minimum 12pt; key values in 14pt+
[x] Max clicks to view patient status: 2
[x] Learnability: First-time user can navigate without training
[x] Error prevention: Confirmation dialogs for destructive actions
```

### 2.5 Compatibility

```
COMPATIBILITY:
[x] Operating Systems:
  - Windows 10/11 ✓
  - macOS 11+ ✓
  - Linux (Ubuntu 20.04+) ✓
[x] Python version: 3.9 - 3.12
[x] Display resolution: Minimum 1024x768
[x] No internet required: Fully offline capable
```

---

## 3. DATA MODEL

```
┌─────────────────┐       ┌─────────────────┐
│    PATIENT      │       │     CYCLE       │
├─────────────────┤       ├─────────────────┤
│ patient_id (PK) │──────<│ cycle_id (PK)   │
│ name            │       │ patient_id (FK) │
│ age_at_dx       │       │ cycle_number    │
│ diagnosis_date  │       │ phase (AC/T)    │
│ act_start_date  │       │ planned_date    │
│ protocol        │       │ actual_date     │
│ total_cycles    │       │ status          │
│ created_at      │       │ dose_percent    │
│ updated_at      │       │ dose_mod_reason │
└─────────────────┘       │ notes           │
                          └─────────────────┘
                                  │
        ┌─────────────────────────┴─────────────────┐
        │                                           │
        ▼                                           ▼
┌─────────────────┐                       ┌─────────────────┐
│    LAB_VALUE    │                       │    TOXICITY     │
├─────────────────┤                       ├─────────────────┤
│ lab_id (PK)     │                       │ toxicity_id (PK)│
│ patient_id (FK) │                       │ cycle_id (FK)   │
│ cycle_id (FK)   │                       │ neutropenia_gr  │
│ lab_date        │                       │ neuropathy_gr   │
│ anc             │                       │ gcsf_given      │
│ wbc             │                       │ other           │
│ platelets       │                       │ created_at      │
│ hemoglobin      │                       └─────────────────┘
│ created_at      │
└─────────────────┘
```

---

# PHASE 4 — FEATURE PRIORITIZATION & MVP

## 1. MoSCoW CATEGORIZATION

### Must Have (Essential for MVP)

| ID | Feature | Rationale |
|----|---------|-----------|
| F-001 | Add Patient | Cannot function without patient records |
| F-002 | View Patient List | Core navigation requirement |
| F-011 | Visual Timeline (8 cycles) | Primary value proposition |
| F-012 | Cycle Completion Recording | Core tracking functionality |
| F-013 | Dose Modification Tracking | Critical clinical information |
| F-023 | Record Lab Values | ANC monitoring is essential |
| F-024 | Lab Trend Chart | Visual trends enable pattern recognition |
| F-025 | Latest Labs Display | Immediate visibility of current status |
| F-026 | ANC Threshold Indicators | Safety feature |
| F-042 | Patient Dashboard | Single-view summary |
| F-051 | Local Data Storage | Data must persist |
| F-052 | Auto-Save | Data integrity essential |
| F-064 | Desktop Application | Platform commitment |
| F-065 | Simple Navigation | Usability essential |
| F-071 | Error Handling | Production readiness |

**Must Have Count: 15 features**

---

## 2. RICE SCORING

### Top Ranked Features

| Rank | Feature | RICE Score | Priority |
|------|---------|------------|----------|
| 1 | Latest Labs Display | 400.0 | MVP Core |
| 2 | Auto-Save | 400.0 | MVP Core |
| 3 | ANC Threshold Indicators | 360.0 | MVP Core |
| 4 | View Patient List | 200.0 | MVP Core |
| 5 | Desktop Application | 200.0 | MVP Core |
| 6 | Simple Navigation | 200.0 | MVP Core |
| 7 | Add Patient | 160.0 | MVP Core |
| 8 | Cycle Completion | 135.0 | MVP Core |
| 9 | Dose Modification Tracking | 120.0 | MVP Core |
| 10 | Record Lab Values | 120.0 | MVP Core |

---

## 3. MVP DEFINITION

### MVP Feature Set (7 Core Capabilities)

```
MVP FEATURES
═══════════════════════════════════════════════════════════════════

1. PATIENT LIST VIEW — (F-002, F-001)
   See all patients, add new patients
   Rationale: Entry point to app

2. PATIENT DASHBOARD — (F-042, F-065)
   Single view showing complete patient status
   Rationale: Core value proposition

3. 8-CYCLE VISUAL TIMELINE — (F-011, F-016)
   Visual representation of AC-T cycles with phase indicators
   Rationale: Primary differentiator

4. CYCLE TRACKING — (F-012, F-013)
   Record cycle completion with dose modification tracking
   Rationale: Core treatment tracking

5. LAB VALUE MANAGEMENT — (F-023, F-024, F-025, F-026)
   Record labs, view trend chart, see latest values with thresholds
   Rationale: Critical clinical data

6. DATA PERSISTENCE — (F-051, F-052)
   SQLite storage with auto-save
   Rationale: Data must persist

7. APPLICATION FRAMEWORK — (F-064, F-071)
   Desktop app shell with error handling
   Rationale: Technical foundation
```

### MVP Success Metrics

| Metric | Target Value | Measurement Method |
|--------|--------------|-------------------|
| **Time to Review Patient** | < 30 seconds | Timed observation with oncologist |
| **Core Workflow Completion** | 100% success rate | User can complete full workflow |
| **Usability Rating** | "Easy to understand" | Verbal feedback from oncologists |
| **Data Integrity** | 0 data loss incidents | Testing |
| **Build Completion** | All 7 capabilities functional | Feature checklist |
| **Stakeholder Approval** | Both oncologists sign off | Demo session |

---

## 4. POST-MVP ROADMAP

### Version 1.1 — "Feedback Response" (Weeks 7-8)

**Goal:** Address initial user feedback

| Feature | Effort | Rationale |
|---------|--------|-----------|
| Edit Patient | 0.5 days | Users need corrections |
| Delete Patient | 0.5 days | Data cleanup |
| Record Toxicities | 2 days | Clinical completeness |
| Alert System | 2 days | Proactive safety |
| CSV Export | 1 day | Data backup |

**Total Effort:** ~9 days

---

### Version 1.5 — "Enhanced Experience" (Month 3)

**Goal:** Polish and extend functionality

| Feature | Effort |
|---------|--------|
| Search/Filter Patients | 1.5 days |
| Patient Status Badges | 1 day |
| Cycle Detail View | 2 days |
| Stale Labs Warning | 0.5 days |
| CSV Import | 2 days |

**Total Effort:** ~12 days

---

### Version 2.0 — "Platform Expansion" (Month 6+)

**Goal:** Major feature expansion

| Feature Category | Effort |
|------------------|--------|
| Multi-User Support | 3-4 weeks |
| Web Deployment | 4-6 weeks |
| Protocol Variations | 2 weeks |
| Advanced Analytics | 2-3 weeks |
| Reporting | 2 weeks |

---

# PHASE 5 — USER STORIES & USE CASES

## 1. USER STORIES (Selected Examples)

### US-001: Launch Application

```
[US-001]: Launch Desktop Application

As a healthcare provider,
I want to launch the AC-T Dashboard application,
So that I can begin reviewing patient treatment data.

Acceptance Criteria:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Scenario: Successful application launch
  Given the application is installed on my computer
  When I double-click the application icon
  Then the main window opens within 3 seconds
  And I see the patient list view
  And the window title shows "AC-T Chemotherapy Dashboard"

Scenario: Launch with existing data
  Given I have previously added patients
  When I launch the application
  Then I see my existing patients in the patient list
  And all data from my last session is preserved
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Priority: Must Have
Story Points: 2
```

---

### US-005: Add New Patient

```
[US-005]: Add New Patient

As an oncologist,
I want to add a new patient to the system,
So that I can begin tracking their AC-T chemotherapy treatment.

Acceptance Criteria:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Scenario: Successfully add a patient
  Given I am on the patient list view
  When I click the "Add Patient" button
  Then I see a form with required fields
  When I fill in all required fields with valid data
  And I click "Save Patient"
  Then the patient is added to the database
  And the new patient appears in the list

Scenario: Validation - duplicate Patient ID
  Given a patient with ID "PT-001" already exists
  When I try to add a new patient with ID "PT-001"
  Then I see an error message "Patient ID already exists"
  And the patient is not saved
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Priority: Must Have
Story Points: 3
```

---

### US-007: View Treatment Timeline

```
[US-007]: View 8-Cycle Treatment Timeline

As an oncologist,
I want to see a visual timeline of all 8 AC-T treatment cycles,
So that I can instantly understand where the patient is in treatment.

Acceptance Criteria:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Scenario: View timeline with completed and pending cycles
  Given I am viewing a patient who has completed 3 cycles
  When the dashboard loads
  Then I see a visual timeline showing 8 cycles
  And cycles 1-4 are labeled "AC"
  And cycles 5-8 are labeled "T"
  And completed cycles are marked as completed
  And cycle 4 is highlighted as current
  And cycles 5-8 are shown as pending
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Priority: Must Have
Story Points: 5
```

---

### US-016: View Lab Trend Chart

```
[US-016]: Display Lab Value Trend Chart

As an oncologist,
I want to see a chart of ANC values over time,
So that I can quickly identify if blood counts are improving or worsening.

Acceptance Criteria:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Scenario: Display ANC trend chart
  Given a patient has 4 lab values recorded on different dates
  When I view the dashboard
  Then I see a line chart with:
    - X-axis: dates
    - Y-axis: ANC values
    - Data points connected by lines
    - Horizontal reference line at ANC = 1.5

Scenario: Highlight points below threshold
  Given the patient has ANC values: 2.0, 1.8, 0.9, 1.6
  When I view the chart
  Then the point at 0.9 is visually distinct
  And it's clear this value was below threshold
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Priority: Must Have
Story Points: 5
```

---

## 2. STORY SUMMARY

| Story ID | Story Title | Priority | Points | Sprint |
|----------|-------------|----------|--------|--------|
| US-001 | Launch Application | Must | 2 | Sprint 1 |
| US-002 | Navigate Between Views | Must | 2 | Sprint 1 |
| US-003 | Graceful Error Handling | Must | 2 | Sprint 1 |
| US-004 | View Patient List | Must | 2 | Sprint 1 |
| US-005 | Add New Patient | Must | 3 | Sprint 1 |
| US-006 | Select Patient for Dashboard | Must | 1 | Sprint 1 |
| US-019 | Local Data Storage | Must | 3 | Sprint 1 |
| US-020 | Auto-Save | Must | 1 | Sprint 1 |
| US-021 | Generate Synthetic Data | Must | 3 | Sprint 1 |
| US-007 | View Treatment Timeline | Must | 5 | Sprint 2 |
| US-008 | AC/T Phase Distinction | Must | 1 | Sprint 2 |
| US-009 | Dose Mod Indicators | Must | 2 | Sprint 2 |
| US-010 | Record Cycle Completion | Must | 3 | Sprint 2 |
| US-011 | Record Dose Modification | Must | 2 | Sprint 2 |
| US-012 | Current Cycle Status | Must | 1 | Sprint 2 |
| US-013 | Add Lab Values | Must | 3 | Sprint 3 |
| US-014 | View Latest Labs | Must | 1 | Sprint 3 |
| US-015 | ANC Threshold Colors | Must | 1 | Sprint 3 |
| US-016 | Lab Trend Chart | Must | 5 | Sprint 3 |
| US-017 | Patient Dashboard | Must | 5 | Sprint 4 |
| US-018 | Patient Header | Must | 1 | Sprint 4 |
| US-022 | Data Generator Access | Should | 1 | Sprint 1 |

**Total: 22 stories | 50 points | 4 sprints**

---

## 3. USE CASES (Critical Flows)

### UC-001: Review Patient Treatment Status

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
UC-001: Review Patient Treatment Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DESCRIPTION:
Healthcare provider reviews a patient's AC-T treatment status before 
an appointment, gathering all necessary information in under 30 seconds.

ACTOR(S):
- Primary: Oncologist
- Secondary: Oncology Nurse

PRECONDITIONS:
- Application is installed and functional
- At least one patient exists in the system
- Patient has some treatment data recorded

POSTCONDITIONS:
- Provider has viewed current treatment status
- Provider knows: current cycle, dose mods, latest labs, trends
- No data has been modified

BASIC FLOW:
┌─────┬────────────────────────────────────────────────────────┐
│ Step│ Action                                                 │
├─────┼────────────────────────────────────────────────────────┤
│  1  │ Provider launches the application                      │
│  2  │ System displays the patient list view                  │
│  3  │ Provider locates desired patient in the list           │
│  4  │ Provider clicks on the patient row                     │
│  5  │ System loads and displays the patient dashboard        │
│  6  │ Provider views patient header to confirm identity      │
│  7  │ Provider views treatment timeline for cycle progress   │
│  8  │ Provider notes any dose modification indicators        │
│  9  │ Provider views latest labs panel and ANC status        │
│ 10  │ Provider views ANC trend chart for pattern             │
│ 11  │ Provider has completed review                          │
└─────┴────────────────────────────────────────────────────────┘

FREQUENCY: 10-20 times per clinic day per provider
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

# PHASE 6 — TIMELINE & MILESTONES

## 1. EFFORT ESTIMATION

### Three-Point Estimation Summary

| Module | Optimistic | Most Likely | Pessimistic | Expected | Std Dev |
|--------|------------|-------------|-------------|----------|---------|
| Application Framework | 2 | 3 | 5 | 3.2 | 0.50 |
| Data Layer | 3 | 4 | 7 | 4.3 | 0.67 |
| Patient Management | 2 | 3 | 5 | 3.2 | 0.50 |
| Treatment Timeline | 4 | 6 | 10 | 6.3 | 1.00 |
| Cycle Tracking | 2 | 4 | 6 | 4.0 | 0.67 |
| Lab Management | 4 | 6 | 9 | 6.2 | 0.83 |
| Dashboard Integration | 2 | 4 | 6 | 4.0 | 0.67 |
| Testing & Bug Fixes | 3 | 5 | 8 | 5.2 | 0.83 |
| Documentation & Demo | 2 | 3 | 5 | 3.2 | 0.50 |
| **TOTAL** | **24** | **38** | **61** | **39.6** | **2.7** |

### Total Project Duration

```
Base Estimate (Expected):           39.6 days ≈ 8 weeks
With 25% Risk Buffer:               49.5 days ≈ 10 weeks
RECOMMENDED TIMELINE:               10 weeks
```

---

## 2. GANTT CHART (10-Week Schedule)

```
GANTT CHART — 10-Week Schedule
═══════════════════════════════════════════════════════════════════

                    WK1   WK2   WK3   WK4   WK5   WK6   WK7   WK8   WK9   WK10
Phase               D1-5  D6-10 D11-15 D16-20 D21-25 D26-30 D31-35 D36-40 D41-45 D46-50
────────────────────────────────────────────────────────────────────────────────────────

Sprint 1            █████ █████ ░░░
Sprint 1 Buffer                 ███

Sprint 2                        ░░███ █████ ░░░
Sprint 2 Buffer                             ███

Sprint 3                                    ░░███ █████ ░░░
Sprint 3 Buffer                                         ███

Sprint 4                                                ░░███ █████ ░░░
Sprint 4 Buffer                                                     ███

Final Polish                                                        ░░███ █████
Stakeholder Demo                                                          ░░░██

────────────────────────────────────────────────────────────────────────────────────────

MILESTONES:
M1: Foundation Complete (Week 2)
M2: Timeline Working (Week 4)
M3: Labs Working (Week 6)
M4: MVP Feature Complete (Week 8)
M5: MVP Validated (Week 10)

Legend: ███ = Active work, ░░░ = Buffer/transition
═══════════════════════════════════════════════════════════════════
```

---

## 3. MILESTONES

| ID | Milestone | Target | Success Criteria |
|----|-----------|--------|------------------|
| **M1** | Foundation Complete | End Week 2 | App launches, patients can be added/viewed, data persists |
| **M2** | Timeline Working | End Week 4 | 8-cycle timeline displays, cycles can be completed |
| **M3** | Labs Working | End Week 6 | Labs entered, displayed with colors, chart renders |
| **M4** | MVP Feature Complete | End Week 8 | All features integrated, end-to-end flow works |
| **M5** | MVP Validated | End Week 10 | Stakeholder demo completed, approval received |

---

## 4. SPRINT PLAN

### Sprint Summary

| Sprint | Weeks | Duration | Focus | Points |
|--------|-------|----------|-------|--------|
| Sprint 0 | Pre-Week 1 | 1-2 days | Setup & Planning | — |
| Sprint 1 | 1-2 | 10 days | Foundation & Patients | 20 |
| Sprint 2 | 3-4 | 10 days | Timeline & Cycles | 14 |
| Sprint 3 | 5-6 | 10 days | Lab Management | 10 |
| Sprint 4 | 7-8 | 10 days | Integration & Validation | 6 |

---

## 5. CRITICAL PATH

### Critical Path Sequence

```
┌─────────────────┐
│ 1. DB Setup     │ 2 days
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. App Framework│ 3 days
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. Patient Mgmt │ 3 days
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. Timeline     │ 6 days ◀── LONGEST TASK
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 5. Cycle Track  │ 4 days
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 6. Lab Chart    │ 5 days
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 7. Dashboard    │ 4 days
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 8. Testing      │ 5 days
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 9. Documentation│ 3 days
└─────────────────┘

CRITICAL PATH TOTAL: 35 days (7 weeks minimum)
```

---

# PHASE 7 — METHODOLOGY

## 1. METHODOLOGY SELECTION

### Selected Methodology: Agile-Lite (Personal Scrum/Kanban)

**Rationale:**

1. **Solo Developer Optimization** — Traditional Scrum ceremonies add overhead without benefit for one person
2. **Maintains Sprint Structure** — 2-week sprints provide useful timeboxing
3. **Kanban Board for Tasks** — Visual management without ceremony overhead
4. **Flexibility for Changes** — Oncologist feedback will generate changes
5. **Minimal Documentation** — Planning docs complete; development needs working software

---

## 2. ROLES

### Developer (You)

**Responsibilities:**
- Own the entire development process
- Maintain and prioritize the product backlog
- Plan and execute sprints
- Write, test, and document code
- Track progress on Kanban board
- Conduct self-reviews and retrospectives
- Prepare and conduct stakeholder demos

**Time Commitment:** Full-time (6-8 hrs/day)

### Domain Expert / Stakeholder (Oncologist #1)

**Responsibilities:**
- Provide domain expertise on AC-T protocol
- Validate requirements and data fields
- Participate in milestone demos
- Provide feedback on usability
- Approve MVP for completion

**Time Commitment:** ~2-3 hours total

### Domain Expert / Stakeholder (Oncologist #2)

**Responsibilities:**
- Secondary validation of requirements
- Participate in MVP demo
- Co-approve MVP for completion

**Time Commitment:** ~1-2 hours total

---

## 3. CEREMONIES

### Daily Check-in (Self)

**Frequency:** Daily (5 minutes)
**Format:**
1. What did I complete yesterday?
2. What will I work on today?
3. Any blockers?

**Action:** Update Kanban board

---

### Sprint Planning (Self)

**Frequency:** Every 2 weeks (30-60 minutes)
**Format:**
1. Review sprint goal
2. Confirm stories for sprint
3. Break stories into tasks
4. Set up Kanban board
5. Identify dependencies/risks

---

### Sprint Review (Self + Stakeholders)

**Frequency:** End of each sprint (30-60 minutes)
**Format:**
- Self-review: Demo to yourself, check acceptance criteria
- Stakeholder demo (at milestones): Live demonstration, gather feedback

---

### Sprint Retrospective (Self)

**Frequency:** End of each sprint (15-20 minutes)
**Format:**
1. What went well?
2. What could be improved?
3. What will I do differently?
4. Velocity check

---

## 4. TOOLS

| Category | Tool | Cost | Purpose |
|----------|------|------|---------|
| **Task Tracking** | Trello | Free | Kanban board |
| **Version Control** | Git + GitHub | Free | Code repository |
| **Communication** | Email + Zoom | Free | Stakeholder communication |
| **IDE** | VS Code | Free | Development |
| **Documentation** | Markdown | Free | README, guides |
| **Testing** | pytest | Free | Unit testing |

---

## 5. WORKING AGREEMENTS

```
WORKING AGREEMENTS
═══════════════════════════════════════════════════════════════════

1. DAILY RHYTHM
   • Start with 5-minute check-in and board update
   • Work in focused blocks
   • End with a commit (even if WIP)

2. WIP LIMITS
   • Maximum 2 tasks in "In Progress"
   • Finish current task before starting new one

3. DEFINITION OF DONE
   A story is DONE when:
   ☐ Code works
   ☐ Acceptance criteria met
   ☐ Code committed
   ☐ No known critical bugs

4. SCOPE DISCIPLINE
   • NO feature additions to MVP during development
   • Log new ideas in "v1.1 Backlog"

5. COMMIT PRACTICES
   • Commit at least once per day
   • Use meaningful commit messages
   • Push to GitHub at end of each day

6. BLOCKER HANDLING
   If stuck for more than 2 hours:
   1. Step away for 15 minutes
   2. Search for solutions
   3. Try simpler approach
   4. Log blocker, switch tasks

7. STAKEHOLDER COMMUNICATION
   • Respond to oncologist emails within 24 hours
   • Schedule demos 1 week in advance
   • Send summary after each session

8. SUSTAINABLE PACE
   • Target 6-8 hours of focused work per day
   • Do NOT work weekends unless critically behind
   • Take at least one day off per week
═══════════════════════════════════════════════════════════════════
```

---

## 6. RAMP-UP PLAN (First 2 Weeks)

### Week 0: Pre-Project Setup (1-2 Days)

```
DAY 0.1: Environment Setup
──────────────────────────────────────────────────────────────────
☐ Install/verify Python 3.9+
☐ Create project directory
☐ Create virtual environment
☐ Install dependencies (matplotlib, pytest)
☐ Verify Tkinter available
☐ Initialize Git repository
☐ Create folder structure
☐ Create requirements.txt
☐ Initial commit
☐ Create GitHub repository and push

DAY 0.2: Tools & Planning Setup
──────────────────────────────────────────────────────────────────
☐ Set up Trello board with all user stories
☐ Copy planning documents to docs/planning/
☐ Email oncologists to schedule demos
☐ Create project log
☐ Test IDE configuration
☐ Quick Tkinter test
☐ Review Sprint 1 stories
```

---

### Week 1: Sprint 1 - Part 1 (Days 1-5)

```
DAY 1: Sprint Planning + Database Setup
──────────────────────────────────────────────────────────────────
Morning: Sprint Planning (30 min)
Development:
☐ Create database.py with SQLite connection
☐ Design and create tables
☐ Test database creation
☐ Commit

DAY 2: Data Models + CRUD Functions
──────────────────────────────────────────────────────────────────
☐ Create models.py
☐ Patient CRUD functions
☐ Write basic tests
☐ Commit

DAY 3: Application Framework (Main Window)
──────────────────────────────────────────────────────────────────
☐ Create main.py
☐ Create main window
☐ Set window properties
☐ Test window opens/closes
☐ Commit

DAY 4: Navigation + Error Handling
──────────────────────────────────────────────────────────────────
☐ Create frame navigation
☐ Create patient_list.py view
☐ Create dashboard.py view
☐ Add error handling
☐ Commit

DAY 5: Patient List View
──────────────────────────────────────────────────────────────────
☐ Implement patient list with Treeview
☐ Add "Add Patient" button
☐ Click on patient → navigate
☐ Test with empty database
☐ Commit
```

---

### Week 2: Sprint 1 - Part 2 (Days 6-10)

```
DAY 6: Add Patient Form
──────────────────────────────────────────────────────────────────
☐ Create Add Patient dialog
☐ Form fields with validation
☐ Save → database insert
☐ Refresh patient list
☐ Commit

DAY 7: Patient Selection + Dashboard
──────────────────────────────────────────────────────────────────
☐ Patient selection from list
☐ Dashboard structure
☐ Pass patient ID
☐ Display patient header
☐ Commit

DAY 8: Auto-Save + Verification
──────────────────────────────────────────────────────────────────
☐ Verify auto-save
☐ Test persistence
☐ Add cycle/lab CRUD functions
☐ Write tests
☐ Commit

DAY 9: Synthetic Data Generator
──────────────────────────────────────────────────────────────────
☐ Create generate_test_data.py
☐ Generate patients with varied data
☐ CLI access
☐ Commit

DAY 10: Sprint Review + Retrospective
──────────────────────────────────────────────────────────────────
Morning: Bug fixes + polish
Afternoon: Sprint Review (30 min)
           Sprint Retrospective (15 min)
☐ Mark stories Done
☐ Update Trello
☐ Push to GitHub
☐ Tag release: v0.1-m1
```

---

# MASTER CHECKLIST

```
═══════════════════════════════════════════════════════════════════
                    PLANNING & REQUIREMENTS CHECKLIST
═══════════════════════════════════════════════════════════════════

PHASE 1 — Project Goal & Scope
───────────────────────────────────────────────────────────────────
[x] Problem statement written & quantified
[x] SMART objectives defined (5)
[x] Scope boundaries documented (in/out)
[x] Constraints, assumptions, dependencies listed
[x] Scope document complete

PHASE 2 — Target Audience & User Research
───────────────────────────────────────────────────────────────────
[x] User segments identified (2)
[x] User personas created (2)
[x] User needs & pain points documented
[x] Research recommendations provided (6)

PHASE 3 — Requirements Gathering
───────────────────────────────────────────────────────────────────
[x] Functional requirements (22)
[x] Non-functional requirements defined
[x] Requirements traceability matrix created
[x] SRS document complete

PHASE 4 — Features & Prioritization
───────────────────────────────────────────────────────────────────
[x] Full feature brainstorm complete (83 features)
[x] MoSCoW categorization done
[x] RICE scores calculated
[x] MVP features defined (7 capabilities)
[x] Post-MVP roadmap created

PHASE 5 — User Stories & Use Cases
───────────────────────────────────────────────────────────────────
[x] User stories created (22)
[x] INVEST validated
[x] Story points assigned (50 total)
[x] Story map created
[x] User journey map created
[x] Use cases documented (3)

PHASE 6 — Timeline & Milestones
───────────────────────────────────────────────────────────────────
[x] Effort estimated (39.6 days base)
[x] Gantt chart created
[x] Milestones defined (5)
[x] Sprint plan created (4 sprints)
[x] Risk-adjusted schedule (10 weeks)
[x] Critical path identified (35 days)

PHASE 7 — Methodology Selection
───────────────────────────────────────────────────────────────────
[x] Methodology selected (Agile-Lite)
[x] Roles defined (3)
[x] Ceremonies defined (5)
[x] Tools chosen (all free)
[x] Working agreements established (8)
[x] Ramp-up plan created

═══════════════════════════════════════════════════════════════════

DELIVERABLES SUMMARY
───────────────────────────────────────────────────────────────────
[x] PROJECT_SCOPE.md
[x] USER_RESEARCH_REPORT.md
[x] SRS.md
[x] FEATURE_BACKLOG_AND_MVP.md
[x] USER_STORIES.md
[x] TIMELINE_AND_MILESTONES.md
[x] METHODOLOGY.md

═══════════════════════════════════════════════════════════════════

PROJECT SUMMARY
───────────────────────────────────────────────────────────────────
Project:        AC-T Chemotherapy Dashboard
Type:           Desktop Application (Python/Tkinter)
Duration:       10 weeks (with buffer)
Effort:         50 story points / ~40 development days
Team:           Solo developer + 2 oncologist advisors
Budget:         $0 (all open-source tools)
Methodology:    Agile-Lite (Personal Scrum/Kanban)

NEXT STEPS
───────────────────────────────────────────────────────────────────
☐ Execute Week 0 setup tasks
☐ Begin Sprint 1 on planned start date
☐ Deliver M1: Foundation Complete (End of Week 2)


- **Total User Stories:** 22
- **Total Features Identified:** 83
- **MVP Features:** 17
- **Estimated Timeline:** 10 weeks
- **Total Budget:** $0

**This document contains everything you need to begin development of the AC-T Chemotherapy Dashboard MVP.**