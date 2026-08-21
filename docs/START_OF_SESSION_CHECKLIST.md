# Start of Session Checklist — WiFi AC Guardian

Follow this checklist at the beginning of every development session to ensure continuity and context.

---

## 1. Read Project Memory

Load the permanent project memory in this order:

- [ ] **Read `PROJECT_STATUS.md`**
  - Current development stage
  - Active milestone and feature
  - Technology stack
  - Current blockers
  - Next action

- [ ] **Read `docs/DECISIONS.md`**
  - Architectural decisions (D-001 onwards)
  - Status of each decision (Accepted/Proposed/Rejected)
  - Alternatives considered
  - Rationale and consequences

- [ ] **Read `docs/SESSION_LOG.md`**
  - Most recent session entry (top of log)
  - Work completed last session
  - Problems encountered
  - Outstanding questions
  - Next recommended action

- [ ] **Read `docs/ROADMAP.md`**
  - Current version scope
  - Completed items (✅)
  - In-progress items (🔨)
  - Upcoming features

---

## 2. Read Constitution & Guidelines

- [ ] **Read `.specify/memory/constitution.md`**
  - 10 core principles (I–X)
  - Development Standards
  - Architecture invariants
  - Governance rules

- [ ] **Read `CLAUDE.md`** (if using Claude Code)
  - Spec-Driven Development workflow
  - PHR recording requirements
  - ADR suggestion rules
  - Execution contract

- [ ] **Read `AGENT_STATUS.md`**
  - 4 mandatory AI agent design rules
  - Current UI snapshot
  - Architecture & module map

---

## 3. Read Current Feature Specification (if applicable)

If working on a specific feature:

- [ ] **Read `specs/<feature-name>/spec.md`**
  - User scenarios & testing
  - Acceptance criteria
  - In scope / out of scope

- [ ] **Read `specs/<feature-name>/plan.md`** (if exists)
  - Architecture decisions
  - Phase breakdown
  - Constitution Check results

- [ ] **Read `specs/<feature-name>/tasks.md`** (if exists)
  - Task list and dependencies
  - Current task status
  - Test requirements

---

## 4. Review Repository State

- [ ] **Check git status**
  ```powershell
  git status
  ```
  - Any uncommitted changes?
  - Current branch clean?

- [ ] **Check current branch**
  ```powershell
  git branch
  ```
  - On correct branch?
  - Should a feature branch be created?

- [ ] **View recent commits**
  ```powershell
  git log --oneline -5
  ```
  - What was the last change?
  - Commit messages clear?

- [ ] **Check for updates from remote**
  ```powershell
  git fetch
  git status
  ```
  - Branch ahead/behind?
  - Need to pull?

---

## 5. Verify Development Environment

- [ ] **Test compilation**
  ```powershell
  python -m compileall -q wifi_ac_guardian_win
  ```
  - All modules compile?
  - No syntax errors?

- [ ] **Run test suite**
  ```powershell
  python -m pytest -q
  ```
  - All tests passing?
  - Expected test count (currently 6)?

- [ ] **Launch application** (if needed)
  ```powershell
  pythonw -m wifi_ac_guardian_win --gui
  ```
  - GUI opens correctly?
  - No errors in log?

---

## 6. Confirm Task Understanding

Before starting implementation:

- [ ] **Task is clear**
  - Understand what needs to be done?
  - Success criteria defined?
  - Acceptance tests known?

- [ ] **Scope is bounded**
  - Small, focused change?
  - No feature creep?
  - Spec exists (if required by Principle V)?

- [ ] **Constitution compliance verified**
  - Does this preserve all existing functionality? (Principle II)
  - Is this the smallest viable change? (Principle V)
  - Are UI and business logic separated? (Principle X)

- [ ] **Dependencies identified**
  - Blocking on other work?
  - Requires approval?
  - External inputs needed?

---

## 7. Plan the Session

- [ ] **Set session goal**
  - One sentence describing what will be accomplished
  - Should be achievable in one session
  - Should be independently committable

- [ ] **Identify deliverables**
  - What files will be created/modified?
  - What tests will be added/updated?
  - What documentation will change?

- [ ] **Note constraints**
  - Time limits
  - Approval requirements
  - Technical constraints

---

## 8. Begin Implementation

When all checks pass:

- [ ] **Create feature branch** (if needed)
  ```powershell
  git checkout -b <branch-name>
  ```

- [ ] **Start work**
  - Focus on session goal
  - Make small commits
  - Run tests frequently

---

## Quick Start (Minimum)

If short on time, **at minimum** read these three files before starting:

1. `PROJECT_STATUS.md` — current state
2. `docs/SESSION_LOG.md` (top entry) — last session context
3. `.specify/memory/constitution.md` — principles

Then verify:
- `git status` (clean?)
- `python -m pytest -q` (passing?)

---

## Notes

- **Context is in the files, not the chat history.** Past conversations are useful for reference but should never be required to understand the current state.
- **When in doubt, read the constitution.** Every decision should trace back to one of the 10 principles.
- **Session logs are permanent memory.** They should contain everything needed to understand what happened and why.
- **Small sessions are better than large ones.** It's better to commit a small, correct change than to batch many risky changes together.

---

**Last Updated**: 2026-08-05
