# WiFi AC Guardian — Router as the ON/OFF Power Button (exact-replication prompt for Antigravity)

**Instructions to Antigravity:** This is a strict, literal replication task. The two attached mockup images are the **only sources of truth**: `wifi_ac_guardian_router_on_no_ring.png` (engine running) and `wifi_ac_guardian_router_off_no_ring.png` (engine stopped). Do NOT add features, colors, layouts, or text not present in these mockups. Do NOT "improve" the design. Every element, string, and behavior below must match exactly. If your judgment conflicts with this document, follow this document.

---

## 0. HARD CONSTRAINTS (do not violate)

1. Single fixed screen: exactly **430 × 932 px**, **zero scrolling, zero overflow**.
2. Layout must fit ANY window size by scaling: render the 430×932 layout inside a wrapper and shrink it with `transform: scale(min(innerWidth/430, innerHeight/932, 1))`, `transform-origin: top center`, so it is proportionally identical from 360×640 to 1280×720. No section may use absolute/fixed positioning (only children inside the Quality bar: tick, zones, marker).
3. Use the exact strings below verbatim. Do not paraphrase.

---

## 1. GLOBAL STYLE

| Property | Exact value |
| --- | --- |
| App background | `#09090B` solid |
| Card background | `rgba(39, 39, 42, 0.8)` + `backdrop-blur-xl` |
| Card border | `1px solid rgba(63, 63, 70, 0.8)` |
| Card radius | `rounded-2xl` |
| Accent (good/active) | Emerald `#10B981` / `#34D399` |
| Warning | Amber `#F59E0B` |
| Danger/stopped | Red `#EF4444` |
| Text | White primary; `#A1A1AA` (zinc-400) labels |
| Glow | Only around the router button (state-colored) and the header Wi-Fi icon |

Section order top → bottom, 8px gaps, page padding 20px/16px: **Header → Hero banner (with router power button) → Connection Quality bar → Connection Details → Protection Engine → one bottom button.**

---

## 2. HEADER

- Left: emerald `Wifi` icon (24px) with small glow; bold white title **"WiFi AC Guardian"** (22px, 700); right: `Settings` gear (24px, zinc-400) opening a dropdown with "Settings" and "About".

---

## 3. HERO BANNER + ROUTER POWER BUTTON (THE MAIN FEATURE)

The hero banner is one full-width card. On its left sits the router — which IS the app's power button.

**Router button (both states):**
- Use the provided router illustration image (`router_on.png` for the lit state, `router_off.png` for the off state) as a static `<img>`, `80×70px`, `object-fit: contain`, at the far left of the banner with ~12px padding.
- Behind/below it: caption **"TAP TO POWER OFF"** (engine running) / **"TAP TO POWER ON"** (engine stopped), 10px, zinc-500.
- The whole router+caption zone is a large tappable hit area (min 110×130px, `cursor-pointer`).
- Clicking it toggles the engine: running → stopped, stopped → running. This is the PRIMARY way to start/stop the app.
- Transition between states: 300ms ease-out on colors only (no bounce, no scale).

**RUNNING state (match `router_button_on.png`):**
- Router image is the green-lit version: glowing green Wi-Fi signal above the router, four lit green LEDs, small lit green port, soft emerald halo behind it. **There is NO circular ring, circle, or outline around the router — it sits freely in the banner with only its soft glow.**
- Banner background has a soft green radial glow on the left half (emerald-500 at 20% opacity).
- Heading: **"Protected — High-Speed Wi-Fi Active"** — emerald-400, 19px, 600 (may wrap, never truncate). Subtext: **"Continuous link quality protection against router bit-rate downgrades."** — zinc-400, 13px.
- Bottom button (single, full width): **"Stop Engine"** — red outline `1px solid #EF4444`, rose-300 text, `Power` icon left, red glow, 48px tall, radius 12px. Clicking it = same as tapping the router (stops the engine).
- Protection Engine → "Next Check" shows live countdown `5 sec` ticking 5→4→3→2→1→5 with emerald `Timer` icon.

**STOPPED state (match `router_button_off.png`):**
- Router image switches to the powered-off version: Wi-Fi signal gone, LEDs unlit, port unlit, the halo becomes a **dim grey glow with a faint red outer tint**. **No circle, ring, or outline may ever appear around the router in either state.**
- Banner background left half shifts to a dim **red tint** (red radial glow at 15% opacity).
- Heading: **"Protection Paused"** — amber `#F59E0B`, same size. Subtext unchanged.
- Bottom button becomes: **"Start Engine"** — emerald outline `1px solid #10B981`, emerald-400 text, green glow. Clicking it restarts.
- Protection Engine → "Next Check" shows a static muted **"—"** (zinc-500), timer icon muted. The countdown interval MUST be fully cleared (`clearInterval` in the stop handler AND the useEffect cleanup — no residual ticking).

## 4. CONNECTION QUALITY BAR

Header row: "CONNECTION QUALITY" (12px bold uppercase, letter-spacing 0.08em) left, "300 Mbps protected threshold" (11px zinc-400) right. Scale labels: "0 Mbps" / amber "300 Mbps" (at 30%) / "1000 Mbps". Bar: capsule 22px tall; zones red `#DC2626→#EF4444` (0–30%), amber `#F59E0B` (30–37%), green `#10B981→#34D399` (37–100%); white 2px tick at 30%. Live marker: white dot + line at `(speed/1000)×100%` with bold white "650 Mbps" label beneath that follows it. Fluid motion: exponential smoothing k=0.22 at 60fps + spring (stiffness 45, damping 16, mass 1.2) + decaying 2px wobble; continuous glide only, never jumps. In stopped state the label dims slightly.

## 5. CONNECTION DETAILS CARD

Title: small emerald `Router` icon (16px) + "CONNECTION DETAILS". Six rows (label left zinc-400 13px, value right white 14px 500, 1px zinc-800 divider):

| Label | Value |
| --- | --- |
| Connected to | `lab5g` in emerald pill (emerald-500/10 bg, emerald-400 text, rounded-full) |
| Signal | five ascending green phone-style bars + "95%"; fill 5 bars ≥80%, 4 bars 60–79%, 3 bars 40–59%, 2 bars 20–39%, 1 bar <20%; 300ms fill transition |
| WiFi Technology | `Wi-Fi 5 (802.11ac)` |
| Adapter | `Intel(R) Wi-Fi 6 AX201 160MHz` |
| Network Band (Channel) | `5 GHz (161)` |
| Link Speed (Rx / Tx) | `650 / 433 Mbps` |

## 6. PROTECTION ENGINE CARD

Title: emerald `Shield` icon (16px) + "PROTECTION ENGINE". Rows: "Last Recovery" → `Never` (then timestamp of last recovery), "Next Check" → as specified per engine state in Section 3.

## 7. TYPES & STATE LOGIC

```ts
type EngineState = "running" | "stopped";
// running: green router, green heading, "Stop Engine" button, countdown ticking
// stopped: dark router, red backlight, amber "Protection Paused", "Start Engine" button, Next Check "—"
```

- Only ONE toggle source of truth: `engineState`. Both the router tap and the bottom button flip the same state. The bottom button label is purely DERIVED from the state (never drives it).
- On state change: hero text/backlight, router image (on/off version), caption, bottom button label/style, Next Check — all transition together in one 300ms ease-out color pass.

## 8. ASSET HANDLING

- You are provided with two router illustrations (`router_on.png` — lit green; `router_off.png` — powered off). Upload both to static asset storage and reference by absolute URL. If only one image is available, use the on-state image in both states and toggle its brightness/hue with CSS: running = `filter: none` with the green glow layer; stopped = `filter: brightness(0.45) saturate(0)` with the red glow layer behind.
- Do NOT fall back to a Lucide `Router` icon.

## 9. VERIFICATION CHECKLIST

- [ ] At 430×932, 360×640, 416×713, 1280×720: nothing clipped, no scrollbar, proportions identical to mockups
- [ ] Tapping the router stops the engine: router lights go out, glow goes dim/red, heading → "Protection Paused" amber, red backlight, Next Check → "—", bottom button → green "Start Engine"
- [ ] Tapping again (or "Start Engine"/"Stop Engine") returns everything to running state
- [ ] Countdown stops completely when stopped (no residual interval — verify via console)
- [ ] Quality bar marker glides smoothly, label follows it, never jumps
- [ ] Signal row = phone bars + percent, NOT a progress bar
- [ ] Exact strings used everywhere; no extra cards, toggles, sparklines, logs, or icons
- [ ] Visual match to both mockup images, state for state

**References:** `wifi_ac_guardian_router_on_no_ring.png` (running state) and `wifi_ac_guardian_router_off_no_ring.png` (stopped state) — replicate exactly, including the absence of any ring around the router.
