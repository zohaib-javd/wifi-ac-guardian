#!/usr/bin/env python3
"""End-of-session checkpoint for WiFi AC Guardian.

Automates the housekeeping at the end of an engineering session:

* refreshes the ``Last Updated`` stamp in ``PROJECT_STATUS.md``
* optionally appends a blank session entry to ``docs/SESSION_LOG.md``
* verifies the required project-memory documents exist
* warns when the memory documents were not touched this session
* prints branch, latest commit, and uncommitted files
* reminds you to commit and push

Documentation tooling only. This script writes to exactly two files
(``PROJECT_STATUS.md`` and ``docs/SESSION_LOG.md``) and will refuse to write
anywhere else. It never reads, edits, or executes application code.

Usage::

    python scripts/end_session.py                # report + refresh timestamp
    python scripts/end_session.py --append-log   # also append a log entry stub
    python scripts/end_session.py --check-only   # report only, write nothing
"""

from __future__ import annotations

import argparse
import datetime as _datetime
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent

PROJECT_STATUS = "PROJECT_STATUS.md"
SESSION_LOG = "docs/SESSION_LOG.md"

# Documents that must exist for the project memory to be intact.
REQUIRED_DOCS: Sequence[str] = (
    PROJECT_STATUS,
    SESSION_LOG,
    "docs/DECISIONS.md",
    "docs/ROADMAP.md",
    ".specify/memory/constitution.md",
)

# Hard allowlist. This script may not write to anything else.
WRITABLE: Sequence[str] = (PROJECT_STATUS, SESSION_LOG)

LAST_UPDATED_RE = re.compile(r"^(\*\*Last Updated\*\*:\s*)(\S+)", re.MULTILINE)
SESSION_HEADING_RE = re.compile(r"^##\s+\d{4}-\d{2}-\d{2}\s+—\s+Session\s+(\d+)", re.MULTILINE)
LOG_HEADER_END = "---\n"

SESSION_ENTRY_TEMPLATE = """## {date} — Session {number:03d}

**AI Assistant**: <assistant and model>
**Session Goal**: <one sentence>

### Work Completed

- <what was actually done>

### Files Modified

- `<path>` (created | modified | deleted)

### Problems Encountered

- <failures, surprises, contradictions found — be specific>

### Next Recommended Action

1. <concrete next step>

### Outstanding Questions

- <decisions needing human input>

---

"""


# ---------------------------------------------------------------------------
# output helpers
# ---------------------------------------------------------------------------

class Report:
    """Collects warnings so the exit code can reflect them."""

    def __init__(self) -> None:
        self.warnings: List[str] = []

    def warn(self, message: str) -> None:
        self.warnings.append(message)
        print("  [!] {0}".format(message))

    def ok(self, message: str) -> None:
        print("  [ok] {0}".format(message))

    def info(self, message: str) -> None:
        print("  {0}".format(message))


def heading(title: str) -> None:
    print("\n" + title)
    print("-" * len(title))


# ---------------------------------------------------------------------------
# git helpers
# ---------------------------------------------------------------------------

def git(*args: str) -> Optional[str]:
    """Run a git command, returning stripped stdout or None on failure."""
    try:
        result = subprocess.run(
            ("git",) + args,
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, ValueError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.rstrip("\n")


def is_git_repo() -> bool:
    return git("rev-parse", "--is-inside-work-tree") == "true"


def porcelain_paths() -> List[str]:
    """Paths reported by ``git status --porcelain``, normalised to forward slashes.

    ``--untracked-files=all`` matters here: the default collapses a new directory
    to a single ``docs/`` entry, which would hide ``docs/SESSION_LOG.md`` from the
    "was the memory updated" check on a first run.
    """
    raw = git("status", "--porcelain", "--untracked-files=all")
    if not raw:
        return []
    paths: List[str] = []
    for line in raw.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].strip().strip('"')
        # Renames appear as "old -> new"; keep the destination.
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.append(path.replace("\\", "/"))
    return paths


# ---------------------------------------------------------------------------
# safety
# ---------------------------------------------------------------------------

def assert_writable(relative_path: str) -> Path:
    """Resolve a path, refusing anything outside the allowlist."""
    if relative_path not in WRITABLE:
        raise SystemExit(
            "refusing to write to {0}: not in the allowlist {1}".format(
                relative_path, list(WRITABLE)
            )
        )
    target = (REPO_ROOT / relative_path).resolve()
    if REPO_ROOT not in target.parents:
        raise SystemExit("refusing to write outside the repository: {0}".format(target))
    return target


# ---------------------------------------------------------------------------
# steps
# ---------------------------------------------------------------------------

def verify_documents(report: Report) -> None:
    heading("Project memory")
    for relative in REQUIRED_DOCS:
        path = REPO_ROOT / relative
        if path.is_file():
            report.ok(relative)
        else:
            report.warn("missing: {0}".format(relative))


def refresh_timestamp(report: Report, today: str, dry_run: bool) -> None:
    heading("Timestamp")
    path = assert_writable(PROJECT_STATUS)
    if not path.is_file():
        report.warn("{0} not found; skipping timestamp refresh".format(PROJECT_STATUS))
        return

    text = path.read_text(encoding="utf-8")
    match = LAST_UPDATED_RE.search(text)
    if match is None:
        report.warn(
            "no '**Last Updated**:' line in {0}; update it by hand".format(PROJECT_STATUS)
        )
        return

    current = match.group(2)
    if current == today:
        report.ok("{0} already stamped {1}".format(PROJECT_STATUS, today))
        return

    if dry_run:
        report.info("would restamp {0}: {1} -> {2}".format(PROJECT_STATUS, current, today))
        return

    path.write_text(LAST_UPDATED_RE.sub(r"\g<1>" + today, text, count=1), encoding="utf-8")
    report.ok("restamped {0}: {1} -> {2}".format(PROJECT_STATUS, current, today))


def next_session_number(text: str) -> int:
    numbers = [int(value) for value in SESSION_HEADING_RE.findall(text)]
    return max(numbers) + 1 if numbers else 1


def append_log_entry(report: Report, today: str, dry_run: bool) -> None:
    heading("Session log entry")
    path = assert_writable(SESSION_LOG)
    if not path.is_file():
        report.warn("{0} not found; cannot append".format(SESSION_LOG))
        return

    text = path.read_text(encoding="utf-8")
    number = next_session_number(text)
    entry = SESSION_ENTRY_TEMPLATE.format(date=today, number=number)

    # Newest entries sit directly below the header rule that closes the intro.
    marker = text.find("\n" + LOG_HEADER_END)
    if marker == -1:
        report.warn("no '---' separator found; appending to end of file instead")
        updated = text.rstrip("\n") + "\n\n" + entry
    else:
        cut = marker + len(LOG_HEADER_END) + 1
        updated = text[:cut] + "\n" + entry + text[cut:].lstrip("\n")

    if dry_run:
        report.info("would append Session {0:03d} stub to {1}".format(number, SESSION_LOG))
        return

    path.write_text(updated, encoding="utf-8")
    report.ok("appended Session {0:03d} stub to {1}".format(number, SESSION_LOG))
    report.info("fill it in before committing — do not leave placeholder text")


def check_memory_touched(report: Report, changed: List[str], appended_log: bool) -> None:
    heading("Was the project memory updated?")
    if PROJECT_STATUS in changed:
        report.ok("{0} has uncommitted changes".format(PROJECT_STATUS))
    else:
        report.warn(
            "{0} was not modified this session — is the status still accurate?".format(
                PROJECT_STATUS
            )
        )

    if SESSION_LOG in changed:
        report.ok("{0} has uncommitted changes".format(SESSION_LOG))
    elif appended_log:
        report.ok("{0} entry appended".format(SESSION_LOG))
    else:
        report.warn(
            "{0} was not modified this session — every session should log an entry".format(
                SESSION_LOG
            )
        )


def show_git(report: Report, changed: List[str]) -> None:
    heading("Repository")
    branch = git("rev-parse", "--abbrev-ref", "HEAD") or "<unknown>"
    report.info("branch:  {0}".format(branch))

    commit = git("log", "-1", "--pretty=format:%h %s  (%an, %ar)")
    report.info("commit:  {0}".format(commit or "<no commits yet>"))

    upstream = git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    if upstream:
        counts = git("rev-list", "--left-right", "--count", "{0}...HEAD".format(upstream))
        if counts:
            behind, ahead = counts.split()
            report.info("remote:  {0} (ahead {1}, behind {2})".format(upstream, ahead, behind))
    else:
        report.info("remote:  <no upstream configured>  see docs/GITHUB_SETUP.md")

    print()
    if changed:
        print("  Uncommitted files ({0}):".format(len(changed)))
        for path in changed:
            print("    - {0}".format(path))
    else:
        print("  Working tree clean.")


def show_reminder(report: Report) -> None:
    heading("Before you finish")
    print("  1. Fill in the session log entry — no placeholder text.")
    print("  2. Update docs/DECISIONS.md if any decision was made.")
    print("  3. Update docs/ROADMAP.md if scope or priorities changed.")
    print("  4. Run the checks:")
    print("       python -m compileall -q wifi_ac_guardian_win")
    print("       python -m pytest -q")
    print("  5. Commit and push:")
    print('       git add -A')
    print('       git commit -m "<type>: <summary>"')
    print("       git push")
    print()
    print("  Full list: docs/END_OF_SESSION_CHECKLIST.md")

    if report.warnings:
        print("\n  {0} warning(s) above need attention.".format(len(report.warnings)))


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------

def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="End-of-session checkpoint for WiFi AC Guardian.",
    )
    parser.add_argument(
        "--append-log",
        action="store_true",
        help="append a blank session entry to docs/SESSION_LOG.md",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="report only; write nothing",
    )
    parser.add_argument(
        "--date",
        default=None,
        metavar="YYYY-MM-DD",
        help="override today's date (testing)",
    )
    args = parser.parse_args(argv)

    today = args.date or _datetime.date.today().isoformat()

    print("=" * 68)
    print("  WiFi AC Guardian — end of session checkpoint")
    print("  {0}   repo: {1}".format(today, REPO_ROOT))
    if args.check_only:
        print("  check-only: no files will be written")
    print("=" * 68)

    report = Report()

    verify_documents(report)

    if not is_git_repo():
        report.warn("not a git repository; skipping repository checks")
        changed: List[str] = []
    else:
        changed = porcelain_paths()

    refresh_timestamp(report, today, dry_run=args.check_only)

    if args.append_log:
        append_log_entry(report, today, dry_run=args.check_only)

    # Re-read status after our own writes so the "was it touched" check is honest.
    if not args.check_only and is_git_repo():
        changed = porcelain_paths()

    check_memory_touched(report, changed, appended_log=args.append_log)

    if is_git_repo():
        show_git(report, changed)

    show_reminder(report)

    print()
    return 1 if report.warnings else 0


if __name__ == "__main__":
    sys.exit(main())
