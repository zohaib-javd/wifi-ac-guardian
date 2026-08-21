<!--
SYNC IMPACT REPORT
===================
Version Change: INITIAL → 1.0.0
Modified Principles: None (initial creation)
Added Sections: All 10 core principles, Development Standards, Governance
Removed Sections: None
Templates Requiring Updates:
  ✅ .specify/templates/plan-template.md - Constitution Check section references this file
  ✅ .specify/templates/spec-template.md - Aligns with principle-driven requirements
  ✅ .specify/templates/tasks-template.md - Task categorization reflects principles
Follow-up TODOs: None
-->

# WiFi AC Guardian Constitution

## Mission

Build the world's most polished Windows desktop application for automatically protecting high-speed Wi-Fi connections.

The application must feel like a premium commercial Windows application that users immediately trust.

---

## Core Principles

### I. User First

Always optimize for clarity over technical jargon.

Every screen MUST answer:
- Am I protected?
- Is everything healthy?
- What should I do next?

**Rationale**: Users trust applications that communicate clearly. Technical complexity should never leak into the interface. The Guardian's value is protection, not education about networking protocols.

### II. Zero Feature Regression

No existing functionality may be removed unless explicitly approved.

Every redesign MUST preserve feature parity.

**Rationale**: Users depend on the Guardian for continuous Wi-Fi protection. Removing features without consent breaks trust and disrupts workflows. Regressions are never acceptable.

### III. Premium Desktop Experience

Every interface should feel inspired by:
- Microsoft PowerToys
- Docker Desktop
- GitHub Desktop
- Windows 11
- Logitech G Hub
- NordVPN Desktop

**Rationale**: Users compare all desktop applications to best-in-class experiences. The Guardian must match or exceed the polish of professional commercial software. Half-measures in design signal half-measures in reliability.

### IV. Beautiful Simplicity

- Less clutter
- Better spacing
- Modern typography
- Consistent iconography
- High visual hierarchy

**Rationale**: Visual noise creates cognitive load. Every unnecessary element distracts from the core message: "Your Wi-Fi is protected." Clean design is not optional—it communicates competence.

### V. Professional Engineering

- Small commits
- Spec-driven development
- No guessing
- Every feature begins with a specification

**Rationale**: Large commits hide intent. Unspecified features drift from requirements. Professional engineering means predictable outcomes, reviewable changes, and maintainable code.

### VI. Performance First

- Never sacrifice responsiveness for visual effects
- Avoid unnecessary redraws
- Cache reusable assets

**Rationale**: A protection utility that freezes or stutters undermines user confidence. Performance is not negotiable. Every animation, every repaint, every API call must justify its cost.

### VII. Accessibility

- Readable fonts
- High contrast
- Keyboard navigation
- Consistent focus states

**Rationale**: Accessibility is not a feature—it is a baseline requirement. Users with visual impairments, motor limitations, or assistive technology deserve equal access to Wi-Fi protection.

### VIII. Consistency

Every card. Every icon. Every button. Every spacing value. Every animation.

Should follow one design language.

**Rationale**: Inconsistency signals carelessness. When buttons have different padding, icons different sizes, or cards different corner radii, users subconsciously distrust the software. Consistency builds confidence.

### IX. Reliability

The Guardian must appear dependable.

Users should feel the software is always protecting their Wi-Fi.

**Rationale**: A protection utility lives or dies on reliability. Users must trust that the Guardian is monitoring, detecting, and restoring their connection without intervention. Perceived reliability is as important as actual reliability.

### X. Code Quality

- Minimal duplication
- Reusable components
- Centralized icon management
- Clear separation of UI and business logic

**Rationale**: Technical debt compounds. Duplicated code becomes maintenance burden. Coupled components resist change. Code quality today determines development velocity tomorrow.

---

## Development Standards

### Architecture Requirements

1. **Single Instance Enforcement**: All GUI and daemon launchers MUST execute `SingleInstanceChecker.try_claim_single_instance()` to prevent duplicate processes.

2. **Process Isolation**: Every `subprocess.run()` or `subprocess.Popen()` call MUST pass `creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)` to suppress console windows.

3. **Thread Safety (Tkinter)**: Any callback triggered from a background thread that modifies Tkinter widgets MUST be dispatched using `widget.after(0, callback)`.

4. **GDI Handle Management**: In `tray.py`, icon updates MUST only occur when `state != self._last_icon_state` to prevent excessive GDI handle allocation.

### Testing Requirements

- Unit tests MUST pass before every commit
- Integration tests MUST cover hardware adapter reset sequences
- UI tests MUST verify responsive layout at minimum window size (760×600)

### Quality Gates

1. **Syntax Check**: `python -m compileall -q wifi_ac_guardian_win` MUST pass
2. **Unit Tests**: `python -m pytest -q` MUST show all tests passing
3. **UI Verification**: Manual visual inspection for layout, spacing, and iconography consistency

---

## Governance

### Amendment Process

1. Proposed amendments MUST be documented in an issue or PR description
2. Amendments MUST increment the constitution version according to semantic versioning:
   - **MAJOR**: Backward incompatible governance/principle removals or redefinitions
   - **MINOR**: New principle/section added or materially expanded guidance
   - **PATCH**: Clarifications, wording, typo fixes, non-semantic refinements
3. Amendments MUST be approved before merging to main branch
4. After ratification, constitution changes MUST propagate to dependent templates

### Compliance Review

- All PRs MUST verify compliance with applicable principles
- Complexity MUST be justified against Principle V (Professional Engineering) and Principle X (Code Quality)
- Feature removals MUST be explicitly approved per Principle II (Zero Feature Regression)

### Template Synchronization

The following templates MUST remain synchronized with constitution changes:
- `.specify/templates/plan-template.md` — Constitution Check section
- `.specify/templates/spec-template.md` — Requirements alignment
- `.specify/templates/tasks-template.md` — Task categorization

### Runtime Guidance

For development workflow guidance, see `CLAUDE.md` (agent-specific) and `HANDOFF.md` (human handoff documentation).

---

**Version**: 1.0.0  
**Ratified**: 2026-08-05  
**Last Amended**: 2026-08-05
