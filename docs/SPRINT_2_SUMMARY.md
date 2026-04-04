# Sprint 2 Summary — AC-T Chemotherapy Dashboard

**Sprint dates:** 2026-03-14 — 2026-04-04
**Sprint goal:** Visual timeline displays, cycles can be completed with dose tracking

---

## Sprint Goal — Achieved

The treatment timeline renders all 8 cycles with clear AC/T phase distinction, cycles can be completed via a validated modal dialog, dose modifications are recorded and displayed visually, and the current cycle status updates dynamically after each save.

---

## Stories Completed — 14/14 points

| Story | Title | Points | Status |
|-------|-------|--------|--------|
| US-007 | View Treatment Timeline | 5 | Done |
| US-008 | AC/T Phase Distinction | 1 | Done |
| US-009 | Dose Modification Indicators | 2 | Done |
| US-010 | Record Cycle Completion | 3 | Done |
| US-011 | Record Dose Modification | 2 | Done |
| US-012 | Current Cycle Status | 1 | Done |

**Velocity: 14 points**

---

## What Was Built

- **Treatment Timeline** — 8 clickable cycle boxes grouped into AC Phase (1-4) and T Phase (5-8); phase color accent strips (blue/purple); phase group labels with drug names; vertical separator between phases
- **Cycle States** — Pending (gray), Current (navy with blue border), Completed (green with checkmark); hover highlight on all boxes
- **Dose Modification Indicator** — Orange ⚠ badge in top-right corner of any completed cycle with dose below 100%
- **Cycle Completion Dialog** — Modal form with completion date (pre-filled today), dose percentage dropdown (100%/85%/75%/50%/Custom), dose reason dropdown (shown and required when dose < 100%), "Other" free-text reason, notes field with 500-char counter; Enter to save, Escape to cancel, unsaved-changes confirmation on close
- **Validation** — Date format, future date prevention, date before treatment start prevention, dose range (1-100%), reason required when dose reduced, "Other" text required
- **Current Cycle Status** — Bold status label above timeline; "Current: Cycle X (AC/T Phase)"; phase transition indicator on Cycle 5; "Treatment Complete" when all 8 done
- **Hover Tooltips** — Completion date on completed cycles; dose % and reason appended for modified cycles
- **UI Polish** — Consistent font scale via constants (`FONT_HINT` through `FONT_NAME`) in `utils/__init__.py`; matching header margins across all screens; patient row hover effect; auto-hiding scrollbar; Labs panel moved below timeline

---

## Key Learnings

- `tk.Frame` with `pack_propagate(False)` is reliable for fixed-size cycle boxes — avoids Canvas complexity
- `grid_remove()` preserves grid options for later `grid()` re-show; critical for show/hide form fields
- Buttons must be packed `side='bottom'` **before** the scrollable body frame, otherwise `expand=True` on the body pushes them off screen
- ttk Treeview hover: adding a `hover` tag alongside `even`/`odd` doesn't work because `even`/`odd` takes priority — must replace the stripe tag entirely with `hover`, then restore on leave
- Font size consistency is best enforced via constants in a shared utils module, not hardcoded values per widget
- `place()` inside a `weight=0` grid row collapses the frame — use `pack()` for placeholder content in variable-height containers

---

## Demo Notes

Demo sequence (~12 min):
1. Launch app → patient list with existing patients, hover effects visible
2. Open a patient mid-treatment → timeline shows AC/T phase distinction, current cycle highlighted
3. Click a pending cycle → completion dialog opens (date auto-focused), fill and save → cycle turns green
4. Click another cycle → change dose to 80%, select Neutropenia → save → orange ⚠ badge appears
5. Hover over modified cycle checkmark → tooltip shows date + dose + reason
6. Navigate back to list → reopen same patient → all data persisted
7. Open a fully completed patient → "Treatment Complete" status

---

## What's Next — Sprint 3 Preview

Sprint 3 focuses on **Lab Value Management**:
- Record and display ANC, WBC, platelets, hemoglobin
- ANC trend chart (Matplotlib)
- Latest labs panel on dashboard
- Planned: 10 story points
