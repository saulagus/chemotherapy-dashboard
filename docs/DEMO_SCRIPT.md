# MVP Demo Script — AC-T Chemotherapy Dashboard

**Total time:** 15–20 minutes
**Audience:** Oncologist stakeholders
**Format:** Live screen share or side-by-side

---

## Before the Demo

- [ ] Launch the app: `python3 src/main.py`
- [ ] Verify demo data is loaded (3 patients in varying states)
- [ ] Close all other applications
- [ ] Set display to 1920×1080 if possible
- [ ] Have this script and the feedback form ready

---

## 0:00 — Introduction (2 min)

**Say:**
> "Thank you for your time. I want to show you something I built to help oncology teams track AC-T chemotherapy progress more efficiently. The problem I'm solving is that reviewing a patient's treatment status — current cycle, any dose modifications, recent ANC — currently requires pulling from multiple sources. This dashboard brings it all together in one view."

**Cover:**
- What the app does in one sentence
- What you'll demonstrate today
- Ask if they have a hard stop time

---

## 0:02 — Patient Management (3 min)

**Show:** Patient list screen

**Say:**
> "This is the main screen. All your AC-T patients are listed here. You can see their ID, name, current cycle progress, and protocol at a glance."

**Do:**
1. Point out the `0/8`, `3/8`, `8/8` cycle counts in the list
2. Click **+ Add Patient**
3. Fill in a new patient — show the required fields
4. Show a validation error (leave name blank, try to save)
5. Fill correctly and save — patient appears in list

**Key point:** Data saves instantly — no Save button needed anywhere in the app.

---

## 0:05 — Dashboard Overview (2 min)

**Show:** Open Demo Patient 1 (mid-treatment)

**Say:**
> "Double-clicking opens the patient dashboard. Everything you need to review this patient is on one screen — no scrolling required."

**Point out each panel:**
- Header: name, ID, protocol, start date
- Timeline: all 8 cycles, phases labeled, current cycle highlighted
- Latest Labs: most recent blood draw with ANC color coding
- ANC Trend Chart: history over time with threshold line

---

## 0:07 — Cycle Tracking (4 min)

**Show:** Timeline on Demo Patient 2 (early treatment)

**Say:**
> "The timeline shows cycle status at a glance. Green means complete, navy is the current cycle, gray is upcoming."

**Do:**
1. Click the current cycle box → Completion dialog opens
2. Show the date field (defaults to today), dose field (defaults to 100%)
3. Change dose to 80%, show the Dose Reason field appear
4. Select "Neutropenia" as reason
5. Save → cycle turns green, orange ⚠ badge appears, status label updates

**Say:**
> "That orange badge means this cycle had a dose reduction. Hover over the checkmark to see the details."

6. Hover over the completed cycle — tooltip shows date and dose info

---

## 0:11 — Lab Management (4 min)

**Show:** Latest Labs panel on Demo Patient 1

**Say:**
> "Lab values are entered after each blood draw. The panel shows the most recent result immediately."

**Do:**
1. Click **+ Add Labs**
2. Enter today's date, ANC 0.7, WBC 2.5, Platelets 120
3. Save → panel updates, ANC shows orange dot and "Moderate Neutropenia"
4. Point to the chart — new data point appears below the threshold line

**Say:**
> "The dashed red line is the 1.5 threshold — below that we're in neutropenia territory. Each point is color-coded the same way as the panel. This gives you an instant visual of the trend across cycles."

5. Switch to Demo Patient 1's earlier labs — show green and yellow points above threshold

---

## 0:15 — 30-Second Review Demo (2 min)

**Say:**
> "One of my goals was that an oncologist could review a patient's full status in under 30 seconds. Let me show you."

**Do:**
1. Open Demo Patient 1
2. Start a visible timer (or count aloud)
3. Narrate: "Current cycle 5 — T phase. Cycle 3 had a dose reduction — neutropenia. Latest ANC is 1.2, mild neutropenia, seven days ago. Trend is recovering upward."
4. Stop timer

**Say:**
> "That's the core value: everything in one place, no switching between systems."

---

## 0:17 — Wrap-Up (3 min)

**Say:**
> "To summarize: patient list with cycle progress, full dashboard with header, timeline, lab panel, and ANC trend chart. Dose modifications are tracked and visible. Labs update the chart in real time."

**Acknowledge limitations honestly:**
> "This is version 1.0. It's a single-user desktop app — it doesn't connect to your EHR, and it only supports AC-T protocol right now. Those are things I'd prioritize for a version 1.1 based on your feedback."

**Open for questions** — see anticipated Q&A below.

---

## Anticipated Questions & Honest Answers

| Question | Answer |
|----------|--------|
| Can it connect to our EHR? | Not in v1.0 — it's a standalone desktop app. EHR integration is the top v1.1 candidate. |
| Can multiple users access it? | Single-user only right now. Multi-user would require a server-side database — a v1.1 decision. |
| What about other regimens? | AC-T only in v1.0. The framework is designed to be extensible — other regimens could be added. |
| Is patient data secure? | Data stays local — SQLite file on the machine, no network transmission. |
| Can we export to PDF or CSV? | Not in v1.0 — export is on the v1.1 feature list. |
| What if a cycle needs to be edited? | Click any completed (green) cycle box — it opens a detail view with an Edit button. |

---

## After the Demo — Feedback Collection

Hand over or read through the **FEEDBACK_FORM.md** questions.

Key questions to ask verbally:
1. "Is this easy to understand at a glance?"
2. "Would this save time in your current workflow?"
3. "What's the one thing you'd most want to see added?"
4. "Any concerns about using this in practice?"

Ask them to attempt the 30-second review themselves and record the time.

---

## If Something Goes Wrong

| Problem | Recovery |
|---------|---------|
| App won't launch | Open screenshots backup (have them ready) |
| Data missing | Run `python3 generate_test_data.py` from terminal |
| Dialog won't close | Press Escape |
| Chart doesn't render | Restart app — matplotlib occasionally needs a second init |
