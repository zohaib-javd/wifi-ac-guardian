# Manus Handoff: WiFi AC Guardian (Frontend UI)

Welcome, Manus! 

This directory contains the complete, self-contained **Next.js + Electron** frontend for the WiFi AC Guardian desktop application. 

**Target Location:**
`C:\Users\Zohaib\Documents\WiFi_AC_Guardian_Windows\wifi-guardian-ui`

## 1. Project Context
- **Role**: This is purely a visual dashboard. It polls real-time telemetry from a local Python daemon running on `http://127.0.0.1:39146`.
- **Framework**: Next.js 15 (Static Export) wrapped in Electron 33.
- **Styling**: Tailwind CSS, Framer Motion for fluid animations (see the specific spring/smoothing math in `page.tsx`).
- **Responsive Layout**: The app uses a strict `transform: scale()` wrapper in `page.tsx` to ensure the exact 430x932 mockup proportions are never clipped, shrinking fluidly to fit any physical desktop window. 

## 2. Important Files
- `src/app/page.tsx`: The primary dashboard UI and state logic. This is where the backend polling hook (`useBackendData`) and UI components live.
- `src/app/layout.tsx`: Contains the root HTML structure and window title metadata.
- `main.js`: The Electron main process. This spawns the desktop window, points to the static Next.js export (`out` folder), and strictly limits resizing/maximization.
- `package.json`: Contains the Electron-builder configuration (note that `directories.output` is set to `build_app` instead of `dist` to avoid Windows EBUSY file-lock errors).

## 3. How to Build & Package
If you need to recompile and package the `.exe` for Windows, you MUST run this specific command inside this directory:

```bash
npm run dist
```

**What this command does:**
1. Runs `next build` to generate the static HTML export into the `out/` folder.
2. Triggers `electron-builder` to package the app.
3. Spits the final portable executable (`WiFi AC Guardian 2.0.5.exe`) into the local `build_app/` folder.

**Post-Build Deployment:**
After running `npm run dist`, you must copy the newly generated `WiFi AC Guardian 2.0.5.exe` from `build_app/` and overwrite the final delivery folder located at:
`C:\Users\Zohaib\Desktop\Upwork\Portfolio Projects\WiFi AC Guardian App\Final Apps\Windows`
