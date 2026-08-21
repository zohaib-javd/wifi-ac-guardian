---
id: 0001
title: WiFi AC Guardian Constitution
stage: constitution
date: 2026-08-05
surface: agent
model: Opus 5 (1M context)
feature: none
branch: master
user: Zohaib Javed
command: /sp.constitution
labels: ["constitution", "governance", "design-system", "windows-desktop"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
  - .specify/templates/plan-template.md
tests:
  - none (documentation-only change)
---

## Prompt

Create the constitution for WiFi AC Guardian.

Project Name:

WiFi AC Guardian

Mission

Build the world's most polished Windows desktop application for automatically protecting high-speed Wi-Fi connections.

The application must feel like a premium commercial Windows application that users immediately trust.

Core Principles

1. User First

Always optimize for clarity over technical jargon.

Every screen should answer

• Am I protected?

• Is everything healthy?

• What should I do next?

2. Zero Feature Regression

No existing functionality may be removed unless explicitly approved.

Every redesign must preserve feature parity.

3. Premium Desktop Experience

Every interface should feel inspired by

Microsoft PowerToys

Docker Desktop

GitHub Desktop

Windows 11

Logitech G Hub

NordVPN Desktop

4. Beautiful Simplicity

Less clutter.

Better spacing.

Modern typography.

Consistent iconography.

High visual hierarchy.

5. Professional Engineering

Small commits.

Spec-driven development.

No guessing.

Every feature begins with a specification.

6. Performance First

Never sacrifice responsiveness for visual effects.

Avoid unnecessary redraws.

Cache reusable assets.

7. Accessibility

Readable fonts.

High contrast.

Keyboard navigation.

Consistent focus states.

8. Consistency

Every card.

Every icon.

Every button.

Every spacing value.

Every animation.

Should follow one design language.

9. Reliability

The Guardian must appear dependable.

Users should feel the software is always protecting their Wi-Fi.

10. Code Quality

Minimal duplication.

Reusable components.

Centralized icon management.

Clear separation of UI and business logic.

The Constitution should become the governing document for every future feature.

## Response snapshot

Created `.specify/memory/constitution.md` at **v1.0.0** (initial ratification), replacing every
placeholder token in the template. Structure:

- **Mission** — verbatim from user input.
- **Core Principles I–X** — the ten supplied principles, each with its original rules plus a
  **Rationale** paragraph explaining why the rule is non-negotiable.
- **Development Standards** — encoded the four pre-existing mandatory architecture rules discovered
  in `AGENT_STATUS.md` (single-instance enforcement, `CREATE_NO_WINDOW` on all subprocess calls,
  `widget.after(0, ...)` for background-thread Tkinter updates, tray GDI handle caching) as
  invariants, plus testing requirements and three quality gates.
- **Governance** — amendment process, semantic versioning policy (MAJOR/MINOR/PATCH), compliance
  review expectations, template synchronization list, runtime guidance pointers.
- **Sync Impact Report** — prepended as an HTML comment.

Propagated to `.specify/templates/plan-template.md`: replaced the placeholder
`[Gates determined based on constitution file]` with a concrete 10-principle checklist plus the four
architecture invariants as a hard gate.

Reviewed `spec-template.md` and `tasks-template.md` — both are principle-agnostic and required no
edits. Ratification date set to today (2026-08-05) since this is the initial adoption.

## Outcome

- ✅ Impact: Project now has a governing constitution at v1.0.0 with all 10 principles ratified and an enforceable Constitution Check gate wired into the planning workflow.
- 🧪 Tests: None run — documentation-only change, no source code touched.
- 📁 Files: `.specify/memory/constitution.md` (created/filled), `.specify/templates/plan-template.md` (gate populated).
- 🔁 Next prompts: Run `/sp.specify` for the first feature under the new constitution; consider `/sp.adr` for the Tkinter-vs-alternative-UI-framework decision given Principle III.
- 🧠 Reflection: Existing repo docs (`AGENT_STATUS.md`, `HANDOFF.md`) already contained hard technical invariants; promoting them into the constitution's Development Standards keeps them enforceable rather than advisory.

## Evaluation notes (flywheel)

- Failure modes observed: None. Template had one malformed placeholder (`[PRINCIPLE__DESCRIPTION]` under `[PRINCIPLE_6_NAME]`) which was resolved by the 10-principle expansion.
- Graders run and results (PASS/FAIL): PASS — no unresolved bracket tokens; version line matches Sync Impact Report; dates in ISO YYYY-MM-DD; principles use MUST/SHOULD rather than vague language.
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): Add a design-token appendix (palette, spacing scale, type ramp) to the constitution so Principle VIII (Consistency) becomes mechanically checkable.
