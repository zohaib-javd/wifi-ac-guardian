# WiFi AC Guardian — Windows Project Structure


This folder is the working repository for the **Windows** edition of WiFi AC Guardian. It was reorganized so that every remaining file is either source code, a design asset, project documentation, or a shipped release. All regenerable build output has been removed and is now excluded by `.gitignore`.

The Ubuntu edition lives in a separate folder and is intentionally not tracked here.

## Folder map

| Path | Contents | Keep? |
|---|---|---|
| `wifi_ac_guardian_win/` | Python backend: monitoring engine, Wi-Fi detector, reconnector, IPC server, tray, config, plus all `.ico`, `.png`, and `.bmp` assets under `assets/` | Permanent source |
| `wifi-guardian-ui/` | Electron + Next.js dashboard: `src/` components and pages, `public/` runtime assets, `main.js`, `preload.js`, and build configuration | Permanent source |
| `releases/v2.0.5/` | Shipped Windows binaries: portable `.exe`, NSIS installer, and installer blockmap | Permanent release archive |
| `legacy-v0.1/` | The original Python/Tkinter application, including its own packaging tree and tests | Permanent reference |
| `design-assets/` | Reference renders, the high-resolution `router_on.png` / `router_off.png` sources, and historical notes from earlier build attempts | Permanent reference |
| `docs/` | Design system, decisions, roadmap, session log, checklists, specifications, prompt history, and handoff documents | Permanent documentation |
| `tests/` | Pytest suite for the Windows backend | Permanent source |
| `.claude/`, `.specify/` | Tooling templates and scripts used during spec-driven development | Optional tooling |
| `.git/` | Full version history on branch `master` | Permanent |

## Where the important assets are

Runtime assets that the applications load at execution time remain inside their own projects, because moving them would break the code. The Electron dashboard reads `wifi-guardian-ui/public/`, which holds `icon.ico` (window and taskbar icon), `router.png` and `assets/router.png` (hero and About dialog images), `wifi_icon.png`, and the four tray-state indicators in `public/status/`. The Python backend reads `wifi_ac_guardian_win/assets/`, which holds `app.ico`, `wifi_ac_guardian.ico`, `router.png`, `wifi_router_3d.png`, the Fluent 3D icon set, the four `router_status/` state images, and the seven `tray_menu/` bitmaps.

The two very large router renders, `router_on.png` and `router_off.png`, were roughly 15 MB each and were not referenced by any current source file. They were moved to `design-assets/router-renders/` so they remain available as master artwork without inflating the application bundle. If a future design needs them, export a compressed version into `public/` rather than moving the originals back.

## Rebuilding the Windows application

Because `node_modules` was removed, the first step after cloning or reopening the project is to reinstall dependencies. From the `wifi-guardian-ui` folder, run `npm install` to restore packages, then `npm run dev` for local development or the project's packaging script to produce distributables. Electron Builder will recreate `build_app/` and place fresh installers there. The Python backend can be installed in editable mode from the repository root with `pip install -e .`, and the test suite runs with `pytest`.

Everything deleted during cleanup is reproducible from these steps. Nothing that was removed is required as an input to a build.

## Release policy

Treat `releases/` as an append-only archive. When a new version is produced, create a sibling folder such as `releases/v2.0.6/` and copy the finished portable executable and installer into it, leaving `v2.0.5` untouched. This keeps a clean record of what was actually shipped and prevents the previous release from being overwritten by a rebuild.

For reference, the verified checksums of the current release are recorded below.

| File | Size (bytes) | SHA-256 |
|---|---:|---|
| `WiFi AC Guardian 2.0.5.exe` | 163,214,701 | `99CB42391B03566D4C477D023B04104ADFBA5A335D8B17E879E18317345FCB1A` |
| `WiFi AC Guardian Setup 2.0.5.exe` | 163,447,137 | `4374AAB6E5B7CC9DE066708B94378C495944475C8076D5A0B3C3B6E6C9AE2DF8` |
| `WiFi AC Guardian Setup 2.0.5.exe.blockmap` | 170,068 | `9474D87FAED0D5CF2A226983B306AD429C94D9C36C5D1EAF8BA6E841962865FF` |

## Keeping the folder clean

The `.gitignore` file was extended to exclude `node_modules/`, `.next/`, `out/`, `build_app/`, `tsconfig.tsbuildinfo`, log files, `__pycache__/`, `.pytest_cache/`, `*.egg-info/`, and `*.bak-*` backups. As long as these rules remain in place, routine development will not reintroduce the several gigabytes of intermediate output that were removed. Periodically deleting `build_app/` after archiving a release into `releases/` is the single most effective habit for keeping the workshop small.

## Git status note

The repository currently carries uncommitted work from the v2.0.5 development cycle, and the cleanup added further deletions and moves on top of it. Review the changes with `git status` and commit them in a single descriptive commit when convenient, so the reorganized layout becomes part of the recorded history.
