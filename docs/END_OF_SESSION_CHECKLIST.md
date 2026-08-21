# End of Session Checklist — WiFi AC Guardian

Complete this checklist before ending every development session.

---

## Documentation

- [ ] **`PROJECT_STATUS.md` updated**
  - [ ] Last Updated timestamp refreshed
  - [ ] Current Milestone accurate
  - [ ] Current Feature reflects work done
  - [ ] Next Action updated
  - [ ] Blockers section current

- [ ] **`docs/SESSION_LOG.md` entry added**
  - [ ] Session number incremented
  - [ ] Date and AI assistant recorded
  - [ ] Session goal stated
  - [ ] Work completed documented
  - [ ] Files modified listed
  - [ ] Problems encountered noted
  - [ ] Next recommended action stated
  - [ ] Outstanding questions captured

- [ ] **`docs/DECISIONS.md` updated** (if applicable)
  - [ ] New decision documented with D-### ID
  - [ ] Reason and alternatives captured
  - [ ] Status set correctly (Accepted/Proposed/Rejected)

- [ ] **`docs/ROADMAP.md` updated** (if applicable)
  - [ ] Version scope adjusted
  - [ ] Completed items marked ✅
  - [ ] New items added to appropriate version

---

## Code Quality

- [ ] **Tests executed and passing**
  ```powershell
  python -m compileall -q wifi_ac_guardian_win
  python -m pytest -q
  ```
  - [ ] No compilation errors
  - [ ] All tests passing
  - [ ] No new test failures introduced

- [ ] **Application launches successfully**
  ```powershell
  pythonw -m wifi_ac_guardian_win --gui
  ```
  - [ ] GUI opens without errors
  - [ ] No console window flicker
  - [ ] System tray icon appears

---

## Constitution Compliance

- [ ] **All principles respected**
  - [ ] No existing functionality removed (Principle II)
  - [ ] Changes preserve feature parity
  - [ ] Code separation maintained (UI vs. business logic)
  - [ ] Small, focused commits planned
  - [ ] Spec-driven if new feature added

- [ ] **Architecture invariants preserved**
  - [ ] Single-instance enforcement intact
  - [ ] `CREATE_NO_WINDOW` on subprocess calls
  - [ ] `widget.after(0, ...)` for background-thread UI updates
  - [ ] Tray icon reassigned only on state change

---

## Version Control

- [ ] **Repository state clean**
  ```powershell
  git status
  ```
  - [ ] All intended changes staged
  - [ ] No unintended files modified
  - [ ] No debug code left in place
  - [ ] No secrets or credentials in code

- [ ] **Commit created with proper message**
  ```powershell
  git add -A
  git commit -m "<type>: <summary>"
  ```
  - [ ] Message format: `type: summary`
  - [ ] Type is one of: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
  - [ ] Summary is clear and concise (<72 chars)
  - [ ] Body added if context needed

- [ ] **Changes pushed to remote**
  ```powershell
  git push
  ```
  - [ ] Push succeeded
  - [ ] Branch is up to date with remote

---

## Handoff Preparation

- [ ] **Next action clearly documented**
  - [ ] Specific next step stated in `PROJECT_STATUS.md`
  - [ ] Blocking questions identified
  - [ ] Required approvals noted

- [ ] **Outstanding work captured**
  - [ ] Incomplete tasks documented
  - [ ] Known issues logged
  - [ ] Technical debt noted

- [ ] **Context preserved for next session**
  - [ ] All four memory documents current
  - [ ] Feature specifications complete
  - [ ] ADRs created for significant decisions

---

## Automation

Use the end-of-session script to automate parts of this checklist:

```powershell
# Refresh timestamp and report
python scripts/end_session.py

# Also append a session log entry stub
python scripts/end_session.py --append-log

# Check-only mode (no writes)
python scripts/end_session.py --check-only
```

The script will:
- Refresh the `PROJECT_STATUS.md` timestamp
- Optionally append a session entry to `docs/SESSION_LOG.md`
- Verify all memory documents exist
- Warn if documents weren't updated
- Display git status, branch, and latest commit

---

## Notes

- **Every session should update the session log.** Even a session that changed nothing should be recorded with what was investigated and why no changes were made.
- **Constitution violations are never acceptable.** If a principle was intentionally bent, document why in `docs/DECISIONS.md` and get approval.
- **Git history is permanent.** Never commit secrets, credentials, or sensitive data. Review staged files carefully before committing.
- **When in doubt, commit.** Small, frequent commits are better than large, infrequent ones.

---

**Last Updated**: 2026-08-05
