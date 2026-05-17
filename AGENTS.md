# Coding Instructions for This Project

## Before Writing Any Code

1. Read every file you are about to touch. Never modify code you have not seen.
2. If the task involves a new component, check existing similar components first for patterns to follow.
3. If anything is unclear about scope or design, ask before building.

## Planning

- Always plan before building. Present the plan as a checklist or table.
- Break implementation into named iterations, such as Step 1, Step 2, and so on.
- Each step should do exactly one thing.
- Get explicit approval before starting to build by asking, "Ready to build?"

## Building

- Build one step at a time. Never skip ahead.
- After each step, verify before moving to the next:
  - Import check: `python3 -c "from module import X; print('OK')"`
  - Logic check: inline assertion script
  - Full test suite: `pytest tests/ -v`
- If a verification fails, fix it before continuing. Never proceed on a broken step.
- Match existing code style exactly: same font constants, same color palette, same layout patterns, including buttons pinned bottom before body and grid layout for forms.

## Code Quality Rules

- No hardcoded font sizes. Use `FONT_HINT`, `FONT_LABEL`, `FONT_BODY`, and related constants.
- No hardcoded colors outside the palette. Use `BG`, `BG_ALT`, `FG`, `FG_MUTED`, `SEPARATOR`, and related constants.
- Do not add features beyond what was asked.
- Do not add error handling for things that cannot happen.

## Testing

- Write tests for every new function and component.
- Cover happy path, empty or `None` state, edge cases such as boundary values, `0`, and negatives, and error paths.
- Tests live in `tests/` and follow existing naming: `test_<module>.py`.
- Run the full suite after adding new tests and verify nothing regressed.

## Committing

- One commit per logical unit of work.
- Message format: `Added [what was built]`. Use a single line, no ticket references, and no `Co-Authored-By claude`.
- Always push immediately after committing with `git push origin master`.

## Anything Else

- Log planning sessions to `docs/PROJECT_LOG.md` when a new day starts.
- If the user asks to validate a story against acceptance criteria, audit every item explicitly in a table. Do not assume.
- Never move to the next user story until the current one is fully verified.
