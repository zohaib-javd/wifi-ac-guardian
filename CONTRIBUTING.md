# Contributing to WiFi AC Guardian

Thanks for working on the Guardian. This document covers how the project is built, the workflow every
change follows, and the standards a change must meet before it lands.

Read `.specify/memory/constitution.md` first — it is the governing document. This guide explains how
to *apply* it.

---

## Project Philosophy

### Guardian-First Design

WiFi AC Guardian is not a network analyzer, a speed tester, or a diagnostic suite. It is a
**Wi-Fi 5+ enforcer** with one job: keep the connection at 802.11ac/ax/be above 300 Mbps, without the
user thinking about it.

Every proposed change should answer: *does this make the Guardian more dependable, or more
understandable?* If neither, it probably belongs in `docs/ROADMAP.md` under Future Ideas rather than
in the codebase.

Three consequences follow:

**The engine is load-bearing.** The detection and reset logic works against a real, reproducible
hardware bug. Treat it as verified-and-working. Changes there need a specification and a test, not a
hunch.

**Presentation and behavior change separately.** UI work changes layout, spacing, typography, and
color. It does not change thresholds, timings, or engine logic unless explicitly asked
(decision D-003). Mixing the two makes regressions impossible to isolate.

**Nothing gets removed silently.** Constitution Principle II is absolute: no existing functionality
is removed without explicit approval. A redesign is additive or transformative, never subtractive.

### The User's Three Questions

Constitution Principle I requires every screen to answer:

1. Am I protected?
2. Is everything healthy?
3. What should I do next?

If a change makes any of these harder to answer at a glance, it is a regression regardless of how
much functionality it adds.

---

## Spec-Driven Development Workflow

Every feature begins with a specification. This is not ceremony — it is what keeps the project from
drifting between sessions and between assistants.

```
Constitution  →  Spec  →  Plan  →  Tasks  →  Implement  →  Verify  →  Document  →  Commit
```

### The Commands

| Command | Produces | When |
|---------|----------|------|
| `/sp.constitution` | `.specify/memory/constitution.md` | Once; amended rarely |
| `/sp.specify` | `specs/<feature>/spec.md` | Start of every feature |
| `/sp.clarify` | Updated `spec.md` | When the spec has gaps |
| `/sp.plan` | `specs/<feature>/plan.md` | After the spec is settled |
| `/sp.tasks` | `specs/<feature>/tasks.md` | After the plan passes the Constitution Check |
| `/sp.implement` | Code | After tasks exist |
| `/sp.adr` | `history/adr/<id>-<title>.md` | For architecturally significant decisions |
| `/sp.phr` | `history/prompts/…` | Automatically, after every session |

### Rules

- **No implementation without a spec.** Bug fixes and typo corrections are exempt. New behavior is
  not.
- **The Constitution Check in `plan.md` is a gate, not a formality.** If a principle cannot be
  satisfied, either change the approach or amend the constitution — do not proceed with a known
  violation.
- **ADRs require consent.** When a decision meets the significance test (long-term impact + multiple
  viable alternatives + cross-cutting scope), *suggest* an ADR. Never create one unprompted.
- **PHRs are mandatory.** Every session records the prompt verbatim under `history/prompts/`.

---

## Session Workflow

The project's memory lives in files, not in conversation history. This is what makes it possible to
hand the project to a different assistant mid-stream.

### Starting a Session

Work through `docs/START_OF_SESSION_CHECKLIST.md`. The short version:

1. `PROJECT_STATUS.md` — where the project is
2. `docs/SESSION_LOG.md` (top entry) — what happened last
3. `docs/DECISIONS.md` — what has already been decided and why
4. `docs/ROADMAP.md` — where it is going
5. `.specify/memory/constitution.md` — the rules
6. `git status` and `git log --oneline -5` — the actual repository state

### Ending a Session

Work through `docs/END_OF_SESSION_CHECKLIST.md`, or run the checkpoint script:

```powershell
python scripts/end_session.py --append-log
```

It refreshes the `PROJECT_STATUS.md` timestamp, appends a session-log stub, verifies the memory
documents exist, warns when they were not updated, and prints the repository state. It writes to
exactly two files and refuses to touch anything else.

Fill in the appended stub before committing. A stub left with placeholder text is worse than no
entry — it looks like a record and contains nothing.

### Log Honestly

Session logs record what actually happened, including dead ends, contradictions found in existing
docs, and things that turned out to be wrong. A session that discovered a documented claim was false
is a productive session. Write that down.

---

## Branch Strategy

**Default branch**: `main`

**Feature branches**: `NNN-short-description`, matching the spec directory.

```powershell
git checkout -b 001-design-system-foundation
```

| Prefix | Use |
|--------|-----|
| `NNN-` | Feature work, numbered to match `specs/NNN-*/` |
| `fix/` | Bug fixes with no spec |
| `docs/` | Documentation and tooling only |
| `chore/` | Dependencies, build config, housekeeping |

Keep branches short-lived. Rebase or merge from `main` often rather than letting a branch drift.

See `docs/GITHUB_SETUP.md` for remote configuration and the pull-request flow.

---

## Commit Message Style

```
<type>: <summary>

<optional body explaining why, not what>
```

**Types**: `feat` · `fix` · `docs` · `style` · `refactor` · `test` · `chore`

**Rules**

- Summary under 72 characters, imperative mood ("add", not "added")
- No trailing period
- Explain *why* in the body; the diff already shows *what*
- One logical change per commit (Constitution Principle V)

**Good**

```
feat: add design token module for palette and spacing

Principle VIII requires one design language, but colors were
hardcoded across 40+ call sites in ui.py. Extracting them makes
consistency mechanically checkable rather than aspirational.
```

```
docs: record terminology decision as proposed, not accepted
fix: guard tray icon update against None state on first poll
```

**Avoid**

```
update stuff
fixed it
WIP
feat: add design tokens, fix tray bug, update README, bump deps
```

That last one is four commits wearing one hat.

---

## Documentation Requirements

Documentation is part of the deliverable, not an afterthought.

| Change type | Must also update |
|-------------|------------------|
| New feature | `PROJECT_STATUS.md`, `SESSION_LOG.md`, `ROADMAP.md`, `specs/<feature>/` |
| Architectural decision | `DECISIONS.md` (new `D-###`), possibly an ADR |
| Scope or priority change | `ROADMAP.md` |
| Any session at all | `SESSION_LOG.md`, `PROJECT_STATUS.md` |
| User-facing behavior | `README.md` |
| New invariant or rule | `.specify/memory/constitution.md`, `AGENT_STATUS.md` |

### Decisions

Append to `docs/DECISIONS.md` with the next sequential ID. Never rewrite a past decision — mark it
`Superseded` and add a new entry referencing it.

Status values carry weight. `Accepted` means it is true of the code right now. `Proposed` means it is
agreed but not implemented. Marking an unimplemented change `Accepted` corrupts the log's value as a
description of reality.

---

## Repository Structure

```
WiFi_AC_Guardian_Windows/
├── wifi_ac_guardian_win/       # Application package — production code
│   ├── cli.py                  # Entry point and argument parsing
│   ├── config.py               # JSON config persistence, autostart shortcut
│   ├── icons.py                # Generated tray icons (Pillow)
│   ├── logger.py               # Rotating file + stream logging
│   ├── single_instance.py      # Loopback IPC, 127.0.0.1:39145
│   ├── tray.py                 # pystray applet
│   ├── ui.py                   # Tkinter dashboard, SegmentedSpeedBar
│   ├── core/                   # Business logic — no UI imports
│   │   ├── models.py           # Dataclasses, quality rules, enums
│   │   ├── detector_win.py     # netsh parsing, link detection
│   │   ├── guardian.py         # Monitoring loop, state machine
│   │   ├── reconnector_win.py  # Hardware radio reset
│   │   └── notifier_win.py     # Windows toast notifications
│   └── assets/                 # Icons and status artwork
├── tests/                      # Unit tests
├── scripts/                    # Developer tooling — never ships to users
│   └── end_session.py          # End-of-session checkpoint
├── specs/                      # Feature specifications
├── docs/                       # Permanent project memory
│   ├── DECISIONS.md            # Engineering decision log
│   ├── ROADMAP.md              # Version roadmap
│   ├── SESSION_LOG.md          # Engineering journal
│   ├── GITHUB_SETUP.md         # Remote configuration
│   ├── START_OF_SESSION_CHECKLIST.md
│   └── END_OF_SESSION_CHECKLIST.md
├── history/
│   ├── prompts/                # Prompt History Records
│   └── adr/                    # Architecture Decision Records
├── .specify/
│   ├── memory/constitution.md  # Governing document
│   └── templates/              # Spec Kit templates
├── PROJECT_STATUS.md           # Current state — read this first
├── CONTRIBUTING.md             # This file
├── AGENT_STATUS.md             # AI agent architecture reference
├── HANDOFF.md                  # Human handoff documentation
├── CLAUDE.md                   # Agent development guidelines
└── README.md                   # User-facing documentation
```

**Boundary that matters**: `core/` contains no UI imports and `ui.py` contains no subprocess calls.
Constitution Principle X depends on this staying true.

---

## Coding Standards

### Architecture Invariants

These four are non-negotiable and enforced by the Constitution Check. Breaking any of them produces a
visible, user-facing defect.

**1. Console isolation.** Every `subprocess.run()` and `subprocess.Popen()` passes
`CREATE_NO_WINDOW`. Without it, a black console window flashes on screen every poll interval.

```python
subprocess.run(
    command,
    capture_output=True,
    text=True,
    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000),
)
```

**2. Main-thread dispatch for Tkinter.** Any background-thread callback that touches a widget
dispatches through `widget.after(0, ...)`. Tkinter is not thread-safe; direct cross-thread updates
crash intermittently and unreproducibly.

```python
def _on_state_change(self, state):
    self.after(0, lambda: self._render_state(state))
```

**3. Tray GDI handle caching.** In `tray.py`, reassign `icon_instance.icon` only when the state
actually changed. Reassigning every poll leaks GDI handles until the tray icon vanishes.

```python
if state != self._last_icon_state:
    self.icon_instance.icon = self._icon_for(state)
    self._last_icon_state = state
```

**4. Single-instance enforcement.** Every GUI and daemon launcher calls
`SingleInstanceChecker.try_claim_single_instance(...)`. Two engines racing to reset the same adapter
fight each other.

### Style

- Follow PEP 8; match the surrounding code where it differs
- Type hints on public functions
- Docstrings on modules and public functions; explain *why* for non-obvious logic
- Named constants over magic numbers, especially thresholds and timings
- Specific exceptions, never bare `except:`
- Log at appropriate levels — `debug` for polling, `info` for state changes, `warning` for
  recoverable failures, `error` for reset failures

### Performance

Constitution Principle VI: responsiveness is not traded for visual effect.

- Cache reusable assets — never reload an image per frame or per poll
- Avoid redraws when state has not changed
- Keep polling work off the UI thread
- Measure before shipping an animation

### Testing

```powershell
python -m compileall -q wifi_ac_guardian_win   # syntax gate
python -m pytest -q                            # test gate
pythonw -m wifi_ac_guardian_win --gui          # manual smoke test
```

Both gates must pass before committing. Tests live in `tests/` as `test_<module>.py`. Engine changes
need a test that reproduces the behavior being fixed or added; UI changes need a manual smoke test
noted in the session log.

Mock `subprocess` calls in tests. Never let a test toggle a real network adapter.

### Security

- No secrets, tokens, or credentials in the repository — ever
- No network requests beyond local adapter queries
- Quote and escape all values interpolated into shell commands
- Prefer argument lists over string interpolation for subprocess calls

---

## Pull Requests

1. Branch from `main`
2. Commit in small, logical steps
3. Run both verification gates
4. Update the documentation listed above
5. Push and open a PR

**PR description should cover**: what changed, why, which principles apply, how it was verified, and
anything intentionally left out.

**Title**: under 70 characters, same format as a commit summary.

---

## Getting Help

| Question | Look here |
|----------|-----------|
| What are the rules? | `.specify/memory/constitution.md` |
| Where is the project now? | `PROJECT_STATUS.md` |
| Why was it built this way? | `docs/DECISIONS.md` |
| What happened last session? | `docs/SESSION_LOG.md` |
| What is planned? | `docs/ROADMAP.md` |
| How does the code fit together? | `AGENT_STATUS.md` |
| How do I connect the remote? | `docs/GITHUB_SETUP.md` |

---

**Creator & Lead Developer**: Zohaib Javed  
**Last Updated**: 2026-08-05
