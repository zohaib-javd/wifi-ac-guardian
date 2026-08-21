# Claude Code — Build Instructions

# WiFi AC Guardian Dashboard (Connection Quality Bar Edition)

> Paste everything below this line into Claude Code, along with the reference mockup `wifi_ac_guardian_final.png`. Treat the mockup as the exact visual source of truth.

---

## Task

Build a premium, modern, dark-mode mobile dashboard screen called **"WiFi AC Guardian"** — a utility that monitors a user's Wi-Fi link speed in real time to prevent router bit-rate downgrades. Replicate the attached mockup faithfully, including the **segmented Connection Quality bar with fluid, water-like responsiveness**.

## Critical Constraints

1. The whole screen MUST fit a fixed mobile viewport of **430 × 932 px** with **ZERO scrolling** — root uses `overflow-hidden`; never a scrollbar.
2. Single-column vertical layout — one `flex flex-col` container, sections in natural document flow.
3. **No `absolute`/`fixed` positioning in the layout.** Overlapping cards were the recurring bug — plain flex children only.
4. Fluid fit on ANY window size (360px mobile up to any desktop window): root is `h-dvh w-full`, sections use flex ratios with `min-h-0` so everything shrinks proportionally instead of clipping.

## Tech Stack

React + Tailwind CSS + Framer Motion + Lucide React icons. One drop-in page component.

## Design System

- Background `bg-zinc-950` (#09090B). Cards `bg-zinc-900/80 backdrop-blur-xl border border-zinc-800/80 rounded-2xl`.
- Emerald accents (active/good), amber (caution/threshold), rose (stop), zinc-400 (muted).
- Typography: Inter-like sans. App title 22px bold white; card labels 10–11px uppercase muted; values 16–18px semibold white.

## Layout (top to bottom)

### 1. Header (~56px)
Flex row, items-center, justify-between. Left: emerald Wi-Fi signal icon (3 arcs, subtle glow) + "WiFi AC Guardian" bold white. Right: settings gear (`Settings` icon); click opens a dropdown ("Settings" / "About", AnimatePresence 0.2s slide-down).

### 2. Hero Banner (~95px, glassmorphic, emerald inner tint)
Left: **router icon — COMPACT size, fits inside the card with padding** (a router illustration: two antennas + Wi-Fi arcs + body; keep it ≤ 30% of the card width; do not let it overflow like previous builds). Right: headline "Protected — High-Speed Wi-Fi Active" in emerald-400 semibold (wrap allowed, no truncation), subtext in muted zinc-400: "Continuous link quality protection against router bit-rate downgrades." State `protected` → emerald; `paused` → amber "Protection Paused".

### 3. Connection Quality Bar Card (~160px, THE centerpiece)
Header row: left "CONNECTION QUALITY" (small bold white uppercase), right "300 Mbps protected threshold" (small muted).
The bar itself — **fluid and water-like** (see animation spec):

- A thick rounded rectangle spanning the card width, made of **three static color zones**:
  - RED zone: 0 → 300 Mbps (30% of bar width)
  - AMBER zone: 300 → ~370 Mbps (~7% of width, soft transition at the threshold)
  - EMERALD GREEN zone: 370 → 1000 Mbps (rest of width), with subtle sheen
- Labels above the bar: "0 Mbps" left, orange "300 Mbps" at the red/amber boundary (with thin white tick there), "1000 Mbps" right.
- **Live position marker:** a glowing white vertical pill with a dot, sitting ON the bar at `position = speed / 1000` (86.7% at 867 Mbps), with bold white "867 Mbps" floating directly below it.

### 4. Connection Metrics (~180px)
2×2 grid (`grid-cols-2 gap-2`), four glass cards, Lucide icons in emerald-tinted 36px chips:

| Cell | Value |
| --- | --- |
| STATUS (Activity icon) | `Active · 1 hr 12 m` with emerald dot |
| RECONNECTS (RefreshCw) | `0 · Last 24h` |
| UPLOAD (ArrowUp) | `866.5 Mbps` / `5 GHz / Ch 48` |
| DOWNLOAD (ArrowDown) | `866.5 Mbps` / `TX 866 Mbps` |

### 5. Protection Engine Card (~190px)
"PROTECTION ENGINE" label (Shield icon). **Exactly ONE toggle row** — no "Low Speed Recovery" anywhere: Search icon + "Connection Monitoring" + iOS toggle ON (emerald track, white knob, glow). Turning it OFF flips the screen to the amber paused state. Network row: Wi-Fi icon + "Connected to lab5g (SSID)" (SSID as a brighter pill). Two buttons, `flex gap-2`, `flex-1 min-w-0`, `py-3.5 rounded-xl font-semibold`, never clipped: "Reconnect now" (outlined emerald, RefreshCw; loading = spin, then success flash) and "Stop protection" (outlined rose, Power).

## Animation Spec — "Responsive like Water" (most important)

The marker must feel liquid and alive, like a buoy sliding on water:

1. **Smoothed live value:** do NOT jump the marker to raw readings. Pipe readings through an exponential smoothing filter: `displaySpeed = displaySpeed + (rawSpeed − displaySpeed) * k`, with `k ≈ 0.18–0.25` updated every frame (~16ms via `requestAnimationFrame` while `rawSpeed` changes). This gives the drag/flow feel of water instead of ticking.
2. **Spring follow-through:** Framer Motion `animate` on the marker's `left` position with `transition={{ type: "spring", stiffness: 45, damping: 16, mass: 1.2 }}` — soft overshoot allowed, settle ~0.7s. If using the rAF smoothing approach, the spring acts as the outer layer.
3. **Wobble on arrival:** when the marker nears its target (<2% away), add a tiny decaying sine wobble to the dot (amplitude ~2px, decays over ~0.5s) — like a buoy settling on water. Implement as `opacity`/`translateY` on the dot element.
4. **Live jitter feed:** every 1–2s re-read speed with ±0–5 Mbps noise; the smoothing filter absorbs it into a continuous glide. When a hard drop occurs (simulated downgrade or real event), let the marker glide down quickly (~0.5s) — fast enough to feel urgent, smooth enough to feel fluid.
5. **Number readout:** the "867 Mbps" label counts up/down alongside the marker via the same smoothed value (format with `toFixed(0)`); update at 20–30fps during motion for buttery motion.
6. **Color logic:** marker stays white/glowing while above 300; when smoothed speed drops below 300, the marker turns amber/red and the header flips to the paused state.
7. Buttons: `whileHover scale 1.02`, `whileTap scale 0.97`; toggle knob spring; banner fades/scales on status change.

## State Model

```ts
interface GuardianState {
  status: "protected" | "paused";
  rawLinkSpeed: number;   // simulated: drift around 860–890, ±5 jitter; expose a hook to bind a real source later
  maxSpeed: 1000;
  threshold: 300;
  uptimeMinutes: 72;
  reconnects24h: 0;
  uploadMbps: 866.5; downloadMbps: 866.5; txRateMbps: 866;
  band: "5 GHz / Ch 48";
  ssid: "lab5g";
  monitoringOn: boolean;  // sole toggle
}
```

## Verbatim Text

"WiFi AC Guardian" · "Protected — High-Speed Wi-Fi Active" · "Continuous link quality protection against router bit-rate downgrades." · "CONNECTION QUALITY" · "300 Mbps protected threshold" · "0 Mbps" · "300 Mbps" · "1000 Mbps" · "867 Mbps" · "STATUS" · "RECONNECTS" · "UPLOAD" · "DOWNLOAD" · "Active · 1 hr 12 m" · "0 · Last 24h" · "866.5 Mbps" · "5 GHz / Ch 48" · "TX 866 Mbps" · "PROTECTION ENGINE" · "Connection Monitoring" · "Connected to lab5g (SSID)" · "Reconnect now" · "Stop protection"

## Acceptance Checklist (verify before done)

1. Renders 430×932 with zero scroll; test also at 360×640 and a small desktop window — nothing clips, nothing overlaps.
2. Router icon is compact and fully inside the banner card.
3. Three-zone bar: red 30%, amber ~7% after 300, green rest; "300 Mbps" orange label with tick at the boundary; marker at 86.7% with "867 Mbps" beneath.
4. Marker motion is continuous and fluid (smoothed drift, spring, wobble) — visibly NOT jumping tick-by-tick.
5. Only one toggle exists ("Connection Monitoring"); OFF flips the paused state.
6. Gear dropdown works; both buttons fully visible with hover/tap feedback.
