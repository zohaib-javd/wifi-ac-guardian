'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Wifi, Settings, Router as RouterLucide, Shield, Timer, Power } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

import SettingsModal, { type GuardianSettings } from '@/components/SettingsModal';
import AboutModal from '@/components/AboutModal';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// ----------------------------------------------------------------------------
// TYPES & LOGIC
// ----------------------------------------------------------------------------
interface ConnectionInfo {
  ssid: string;
  signalPercent: number;
  wifiTechnology: string;
  adapter: string;
  rxMbps: number;
  txMbps: number;
}
type EngineState = "protected" | "paused";

function normalizeWifiTechnology(value: unknown) {
  const text = typeof value === "string" ? value.trim() : "";
  const labels: Record<string, string> = {
    "802.11ac (Wi-Fi 5)": "Wi-Fi 5 (802.11ac)",
    "802.11ax (Wi-Fi 6/6E)": "Wi-Fi 6/6E (802.11ax)",
    "802.11be (Wi-Fi 7)": "Wi-Fi 7 (802.11be)",
    "802.11n (Wi-Fi 4)": "Wi-Fi 4 (802.11n)",
  };
  return labels[text] || text || "Wi-Fi 5 (802.11ac)";
}

const SMOOTHING_K = 0.22;
const MAX_SPEED = 1000;
const API_URL = 'http://127.0.0.1:39146';

function useBackendData() {
  const [data, setData] = useState({
    connected: false,
    ssid: "lab5g",
    linkSpeed: 650,
    signalPct: 95,
    txBitrate: "433 Mbps",
    rxBitrate: "650 Mbps",
    phyMode: "Wi-Fi 5 (802.11ac)",
    adapter: "Intel(R) Wi-Fi 6 AX201 160MHz",
    band: "5 GHz (161)",
    status: "paused",
    reconnectAttempts: 0,
    maxAttempts: 99,
    protectionRunning: true,
    lastRecovery: "Never",
    backendOnline: false,
    backendError: "",
    minBitrateThreshold: 300,
    checkInterval: 10,
    reconnectDelay: 15,
    autoSwitchPrimary: true,
    enableNotifications: false,
    enableSoundAlerts: false,
    autoStart: true,
    startMinimized: false,
    targetSsid: "lab5g",
    availableSsids: [] as string[]
  });

  useEffect(() => {
    const fetchTelemetry = async () => {
      try {
        const res = await fetch(API_URL);
        if (res.ok) {
          const telemetry = await res.json();
          setData(prev => ({
            ...prev,
            ...telemetry,
            rxBitrate: telemetry.rxBitrate || `${telemetry.linkSpeed} Mbps`,
            availableSsids: telemetry.available_ssids || [],
            backendOnline: true,
            backendError: ""
          }));
        } else {
          setData(prev => ({
            ...prev,
            backendOnline: false,
            backendError: `Guardian backend returned HTTP ${res.status}.`
          }));
        }
      } catch (err) {
        setData(prev => ({
          ...prev,
          backendOnline: false,
          backendError: "Guardian backend is unavailable."
        }));
      }
    };

    fetchTelemetry();
    const interval = setInterval(fetchTelemetry, 2000);
    return () => clearInterval(interval);
  }, []);

  const applySavedSettings = useCallback((settings: GuardianSettings) => {
    setData(prev => ({
      ...prev,
      targetSsid: settings.targetSsid,
      checkInterval: settings.checkInterval,
      reconnectDelay: settings.reconnectDelay,
      maxAttempts: settings.maxAttempts,
      minBitrateThreshold: settings.minBitrateThreshold,
      autoSwitchPrimary: settings.autoSwitchPrimary,
      enableNotifications: settings.enableNotifications,
      enableSoundAlerts: settings.enableSoundAlerts,
      autoStart: settings.autoStart,
      startMinimized: settings.startMinimized,
    }));
  }, []);

  return { data, applySavedSettings };
}

function useSmoothedValue(target: number, k: number = SMOOTHING_K) {
  const [display, setDisplay] = useState(target);
  const displayRef = useRef(target);
  const targetRef = useRef(target);

  useEffect(() => {
    targetRef.current = target;
    let raf: number;
    let last = performance.now();

    const step = (now: number) => {
      const dt = Math.min((now - last) / 16.67, 3);
      last = now;
      displayRef.current += (targetRef.current - displayRef.current) * Math.min(k * dt, 1);
      setDisplay(displayRef.current);
      raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [target, k]);

  return display;
}

function formatRecovery(value: unknown) {
  if (!value) return "Never";
  const date = new Date(String(value));
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

// ----------------------------------------------------------------------------
// COMPONENTS
// ----------------------------------------------------------------------------
function SignalBars({ percent }: { percent: number }) {
  let activeBars = 1;
  if (percent >= 80) activeBars = 5;
  else if (percent >= 60) activeBars = 4;
  else if (percent >= 40) activeBars = 3;
  else if (percent >= 20) activeBars = 2;

  const heights = [20, 40, 60, 80, 100];

  return (
    <div className="flex items-end gap-[3px] h-[14px]">
      {heights.map((h, i) => (
        <motion.div
          key={i}
          layout
          initial={false}
          animate={{
            backgroundColor: i < activeBars ? "#10B981" : "rgba(63, 63, 70, 0.5)",
          }}
          transition={{ duration: 0.3 }}
          style={{ height: `${h}%`, width: '4px', borderRadius: '2px' }}
        />
      ))}
    </div>
  );
}

/**
 * Router power button in the hero banner.
 * ON: teal router with glowing green Wi-Fi signal + green halo.
 * OFF: dimmed "lights out" + faint red tint. NO ring around it — sits freely.
 */
function RouterPowerButton({
  running,
  onTap,
  disabled = false,
}: {
  running: boolean;
  onTap: () => void;
  disabled?: boolean;
}) {
  return (
    <button
      onClick={onTap}
      disabled={disabled}
      aria-label={running ? "Tap to power off" : "Tap to power on"}
      aria-busy={disabled}
      className={cn(
        "relative w-[104px] h-[96px] shrink-0 flex flex-col items-center justify-center group",
        disabled ? "cursor-wait opacity-80" : "cursor-pointer"
      )}
    >
      {/* Glow layer (no ring — just a soft radial halo) */}
      <motion.div
        className="absolute inset-[-10px] rounded-full pointer-events-none"
        animate={{
          background: running
            ? "radial-gradient(circle, rgba(16,185,129,0.35) 0%, rgba(16,185,129,0.08) 45%, transparent 70%)"
            : "radial-gradient(circle, rgba(156,163,175,0.25) 0%, rgba(239,68,68,0.12) 55%, transparent 75%)",
          scale: running ? [1, 1.06, 1] : 1,
        }}
        transition={{
          background: { duration: 0.3, ease: "easeOut" },
          scale: running ? { duration: 1.8, repeat: Infinity, ease: "easeInOut" } : undefined,
        }}
      />

      <motion.img
        src="/assets/router.png"
        alt="Router power button"
        width={78}
        height={78}
        draggable={false}
        className="object-contain relative z-10"
        animate={{
          filter: running ? "none" : "brightness(0.45) saturate(0)",
        }}
        transition={{ duration: 0.3, ease: "easeOut" }}
      />

      <span className="relative z-10 text-[9px] tracking-[0.08em] text-[#a1a1aa] mt-0.5 whitespace-nowrap">
        {running ? "TAP TO POWER OFF" : "TAP TO POWER ON"}
      </span>
    </button>
  );
}

export default function Home() {
  const { data: telemetry, applySavedSettings } = useBackendData();
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isAboutOpen, setIsAboutOpen] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  // Local toggles for UI interaction since backend might not be attached
  const [engineState, setEngineState] = useState<EngineState>(telemetry.protectionRunning ? "protected" : "paused");
  const [engineActionPending, setEngineActionPending] = useState(false);
  const [actionError, setActionError] = useState("");
  const pendingEngineStateRef = useRef<EngineState | null>(null);

  // Sync engineState with telemetry if it changes
  useEffect(() => {
    if (pendingEngineStateRef.current === null && telemetry.backendOnline) {
      setEngineState(telemetry.protectionRunning ? "protected" : "paused");
    }
  }, [telemetry.backendOnline, telemetry.protectionRunning]);

  const [countdown, setCountdown] = useState(5);
  const countdownRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    // Fully clear any previous interval whenever state changes
    if (countdownRef.current) {
      clearInterval(countdownRef.current);
      countdownRef.current = null;
    }

    if (engineState !== "protected") {
      setCountdown(5);
      return;
    }

    countdownRef.current = setInterval(() => {
      setCountdown(c => (c <= 1 ? 5 : c - 1));
    }, 1000);

    return () => {
      if (countdownRef.current) {
        clearInterval(countdownRef.current);
        countdownRef.current = null;
      }
    };
  }, [engineState]);

  const smoothedSpeed = useSmoothedValue(telemetry.linkSpeed);
  const percentage = Math.min(100, Math.max(0, (smoothedSpeed / MAX_SPEED) * 100));

  const distanceToTarget = Math.abs(telemetry.linkSpeed - smoothedSpeed);
  const isSettling = distanceToTarget > 0.1 && distanceToTarget < 15;

  const handleToggleEngine = useCallback(async () => {
    if (engineActionPending) return;
    const newState: EngineState = engineState === "protected" ? "paused" : "protected";
    const previousState = engineState;
    pendingEngineStateRef.current = newState;
    setActionError("");
    setEngineActionPending(true);
    setEngineState(newState);
    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'toggle_protection' })
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok || typeof payload.protectionRunning !== "boolean") {
        throw new Error(payload.message || `Guardian backend returned HTTP ${res.status}.`);
      }
      const confirmedState: EngineState = payload.protectionRunning ? "protected" : "paused";
      setEngineState(confirmedState);
      pendingEngineStateRef.current = null;
    } catch (e) {
      pendingEngineStateRef.current = null;
      setEngineState(previousState);
      setActionError(e instanceof Error ? e.message : "Unable to change protection state.");
    } finally {
      setEngineActionPending(false);
    }
  }, [engineActionPending, engineState]);

  const handleSaveSettings = useCallback(async (settings: GuardianSettings) => {
    setActionError("");
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "save_settings", settings })
    });
    const payload = await res.json().catch(() => ({}));
    if (!res.ok || payload.status !== "ok") {
      const message = payload.message || payload.error || `Guardian backend returned HTTP ${res.status}.`;
      setActionError(message);
      throw new Error(message);
    }
    const electronAPI = typeof window !== "undefined"
      ? (window as Window & {
        electronAPI?: {
          setLoginStartup?: (options: { autoStart: boolean; startMinimized: boolean }) => Promise<{ ok: boolean; error?: string | null }>;
        }
      }).electronAPI
      : undefined;
    if (electronAPI?.setLoginStartup) {
      const startupResult = await electronAPI.setLoginStartup({
        autoStart: settings.autoStart,
        startMinimized: settings.startMinimized,
      });
      if (!startupResult.ok) {
        const message = startupResult.error || "Unable to update Windows startup settings.";
        setActionError(message);
        throw new Error(message);
      }
    }
    applySavedSettings((payload.settings || settings) as GuardianSettings);
  }, [applySavedSettings]);

  const handleReconnect = useCallback(async () => {
    if (engineState === "protected") return; // Button is disabled visually anyway
    try {
      await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'reconnect_now' })
      });
      // Optionally start engine when reconnecting
      setEngineState("protected");
    } catch (e) {}
  }, [engineState]);

  const isProtected = engineState === "protected";
  const protectedThreshold = Math.max(1, Number(telemetry.minBitrateThreshold) || 300);
  const thresholdPercentage = Math.min(100, Math.max(0, (protectedThreshold / MAX_SPEED) * 100));
  const cautionEndPercentage = Math.min(100, thresholdPercentage + 7);

  // ConnectionInfo Object logic
  const connInfo: ConnectionInfo = {
    ssid: telemetry.ssid || "lab5g",
    signalPercent: telemetry.signalPct || 95,
    wifiTechnology: normalizeWifiTechnology(telemetry.phyMode),
    adapter: typeof telemetry.adapter === "string" && telemetry.adapter.trim()
      ? telemetry.adapter.trim()
      : "Intel(R) Wi-Fi 6 AX201 160MHz",
    rxMbps: parseInt(telemetry.rxBitrate) || telemetry.linkSpeed || 650,
    txMbps: parseInt(telemetry.txBitrate) || 433,
  };

  // Fill the actual Electron width and compact vertical rhythm for short windows.
  // Do not scale a fixed 430x932 canvas by viewport height: that makes the UI
  // artificially narrow and lets the quality readout escape its card.
  const [viewport, setViewport] = useState({ width: 430, height: 932 });

  useEffect(() => {
    const compute = () => setViewport({ width: window.innerWidth, height: window.innerHeight });
    compute();
    window.addEventListener("resize", compute);
    return () => window.removeEventListener("resize", compute);
  }, []);

  const shellWidth = Math.min(430, Math.max(320, viewport.width));
  const compact = viewport.height < 800;
  const density = compact ? 0.55 : Math.max(0.72, Math.min(1, viewport.height / 932));
  const layoutGap = compact ? 12 : Math.max(12, 16 * density);
  const shellPaddingX = layoutGap;
  const shellPaddingY = layoutGap;
  const shellPaddingBottom = layoutGap;
  const sectionGap = layoutGap;
  const cardPadding = compact ? 9 : Math.max(10, 16 * density);
  const rowPadding = compact ? 3 : Math.max(4, 10 * density);
  const markerPercentage = Math.min(96, Math.max(4, percentage));

  return (
    <div aria-busy={engineActionPending} className="relative h-dvh w-full overflow-hidden bg-zinc-950 flex items-start justify-center select-none text-white font-sans">
      <AnimatePresence>
        {(telemetry.backendError || actionError) && (
          <motion.div
            role="status"
            aria-live="polite"
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            className="fixed left-1/2 top-2 z-[100] w-[min(390px,calc(100vw-24px))] -translate-x-1/2 rounded-lg border border-[#7f1d1d] bg-[#2a1214]/95 px-3 py-2 text-center text-[11px] text-[#fecaca] shadow-xl backdrop-blur"
          >
            {actionError || telemetry.backendError}
          </motion.div>
        )}
      </AnimatePresence>
      <div
        style={{
          width: `${shellWidth}px`,
          height: "100%",
          padding: `${shellPaddingY}px ${shellPaddingX}px ${shellPaddingBottom}px`,
          gap: `${sectionGap}px`,
          justifyContent: "space-between",
          flexShrink: 0,
        }}
        className="flex flex-col overflow-hidden"
      >

        {/* 3. HEADER */}
        <header style={{ height: `${Math.max(compact ? 32 : 32, 40 * density)}px` }} className="flex flex-row items-center justify-between shrink-0 z-50">
           <div className="flex items-center gap-[10px]">
              <Wifi className="w-6 h-6 text-[#10B981] drop-shadow-[0_0_6px_rgba(16,185,129,0.5)]" />
              <h1 className="text-[18px] font-bold tracking-tight">WiFi AC Guardian</h1>
           </div>
           <div className="relative">
             <button onClick={() => setIsDropdownOpen(!isDropdownOpen)} className="p-1.5 -mr-1.5 hover:bg-zinc-800/50 rounded-full transition-colors cursor-pointer text-[#a1a1aa] hover:text-white">
               <Settings className="w-6 h-6" />
             </button>
             <AnimatePresence>
               {isDropdownOpen && (
                 <motion.div
                   initial={{ opacity: 0, y: -5 }}
                   animate={{ opacity: 1, y: 0 }}
                   exit={{ opacity: 0, y: -5 }}
                   transition={{ duration: 0.15 }}
                   className="absolute right-0 top-full mt-1 w-32 bg-[#18181b] border border-[#3f3f46]/80 rounded-lg shadow-xl overflow-hidden z-50"
                 >
                   <button onClick={() => { setIsDropdownOpen(false); setIsSettingsOpen(true); }} className="w-full text-left px-3 py-2.5 hover:bg-[#27272a] text-[13px] font-medium border-b border-[#3f3f46]/50 cursor-pointer">Settings</button>
                   <button onClick={() => { setIsDropdownOpen(false); setIsAboutOpen(true); }} className="w-full text-left px-3 py-2.5 hover:bg-[#27272a] text-[13px] font-medium cursor-pointer">About</button>
                 </motion.div>
               )}
             </AnimatePresence>
           </div>
        </header>

        {/* 4. HERO STATUS BANNER (router is the ON/OFF power button) */}
        <div
          style={{
            padding: `${cardPadding}px`,
            minHeight: `${Math.max(compact ? 108 : 112, 128 * density)}px`,
            flexGrow: 1,
            background: isProtected
              ? "linear-gradient(108deg, rgba(4,120,87,0.52) 0%, rgba(5,150,105,0.38) 18%, rgba(13,76,62,0.27) 44%, rgba(39,39,42,0.92) 100%)"
              : "linear-gradient(108deg, rgba(127,29,29,0.56) 0%, rgba(185,28,28,0.38) 18%, rgba(97,28,28,0.26) 44%, rgba(39,39,42,0.92) 100%)",
            boxShadow: isProtected
              ? "0 0 24px rgba(16,185,129,0.18)"
              : "0 0 24px rgba(239,68,68,0.16)",
          }}
          className="flex flex-row items-center shrink-0 rounded-2xl bg-[#27272a]/80 backdrop-blur-xl border border-[#3f3f46]/80 relative overflow-hidden"
        >
          {/* Background Glow */}
          <motion.div
            className="absolute left-0 top-0 bottom-0 w-1/2 pointer-events-none"
            animate={{
              background: isProtected
                ? "radial-gradient(circle at 28% 50%, rgba(16,185,129,0.32) 0%, rgba(16,185,129,0.16) 44%, rgba(16,185,129,0.04) 67%, transparent 100%)"
                : "radial-gradient(circle at 28% 50%, rgba(239,68,68,0.28) 0%, rgba(239,68,68,0.14) 44%, rgba(239,68,68,0.04) 67%, transparent 100%)"
            }}
            transition={{ duration: 0.3, ease: "easeOut" }}
          />

          <div style={{ width: `${compact ? 112 : 132}px` }} className="shrink-0 mr-2 relative z-10 flex justify-center -translate-x-1">
            <RouterPowerButton running={isProtected} onTap={handleToggleEngine} disabled={engineActionPending} />
          </div>

          <div className="flex-1 min-w-0 flex flex-col justify-center relative z-10 pl-1">
             <motion.h2
               className="text-[17px] font-semibold leading-tight mb-1 whitespace-pre-wrap"
               animate={{ color: isProtected ? "#34d399" : "#f59e0b" }}
               transition={{ duration: 0.3, ease: "easeOut" }}
             >
               {isProtected ? "Protection Active" : "Protection Paused"}
             </motion.h2>
             <p className="text-[11px] text-[#a1a1aa] leading-snug">
               Continuous link quality protection against router bit-rate downgrades.
             </p>
          </div>
        </div>

        {/* 5. CONNECTION QUALITY BAR CARD */}
        <div style={{ padding: `${cardPadding}px`, paddingBottom: `${cardPadding + Math.max(compact ? 22 : 26, 34 * density)}px`, minHeight: `${Math.max(compact ? 128 : 150, 176 * density)}px`, flexGrow: 1 }} className="flex flex-col min-h-0 rounded-2xl bg-[#27272a]/80 backdrop-blur-xl border border-[#3f3f46]/80 justify-center overflow-hidden">
          <div className="flex justify-between items-center mb-4 shrink-0">
            <span className="text-[11px] font-bold tracking-[0.08em] text-[#ffffff]">CONNECTION QUALITY</span>
            <span className="text-[10px] text-[#a1a1aa]">{protectedThreshold} Mbps protected threshold</span>
          </div>

          <div className="relative w-full shrink-0">
            {/* Labels above bar */}
            <div className="relative h-4 mb-[6px] flex text-[10px]">
              <span className="absolute left-0 text-[#a1a1aa]">0 Mbps</span>
              <span className="absolute font-medium text-[#f59e0b]"
                style={{ left: `${thresholdPercentage}%`, transform: "translateX(-50%)" }}>
                {protectedThreshold} Mbps
              </span>
              <span className="absolute right-0 text-[#a1a1aa]">1000 Mbps</span>
            </div>

            {/* Bar track container */}
            <div className="relative h-[22px] w-full rounded-full overflow-hidden bg-zinc-800">
              {/* Red Zone */}
              <div
                className="absolute inset-y-0 left-0 bg-gradient-to-r from-[#dc2626] to-[#ef4444]"
                style={{ width: `${thresholdPercentage}%` }}
              />
              {/* Amber Zone */}
              <div
                className="absolute inset-y-0 bg-[#f59e0b]"
                style={{ left: `${thresholdPercentage}%`, width: `${Math.max(0, cautionEndPercentage - thresholdPercentage)}%` }}
              />
              {/* Green Zone */}
              <div
                className="absolute inset-y-0 bg-gradient-to-r from-[#10b981] to-[#34d399]"
                style={{ left: `${cautionEndPercentage}%`, right: 0 }}
              />

              {/* Tick at threshold */}
              <div
                className="absolute top-0 bottom-0 w-[2px] bg-white z-10"
                style={{ left: `${thresholdPercentage}%` }}
              />
            </div>

            {/* Liquid Marker container */}
            <div className="absolute top-[20px] left-0 right-0 h-10 pointer-events-none">
              <motion.div
                className="absolute top-[-6px] bottom-[-6px] w-[2px] z-20 flex flex-col items-center -translate-x-1/2"
                animate={{ left: `${markerPercentage}%` }}
                transition={{ type: "spring", stiffness: 45, damping: 16, mass: 1.2 }}
              >
                 <div className="w-[2px] h-[34px] bg-white relative shadow-sm">
                    {/* Glowing Dot on top */}
                    <div className="absolute top-0 -left-[3px] w-[8px] h-[8px] rounded-full bg-white shadow-[0_0_6px_rgba(255,255,255,1)]" />
                 </div>
                 {/* Floating Label Below */}
                 <motion.div
                   className="absolute top-[36px] text-[14px] font-semibold tracking-[-0.01em] text-white whitespace-nowrap"
                   animate={isSettling ? { y: [0, -2, 2, -1, 1, 0] } : { y: 0 }}
                   transition={{ duration: 0.4, ease: "easeOut" }}
                 >
                   {smoothedSpeed.toFixed(0)} Mbps
                 </motion.div>
              </motion.div>
            </div>
          </div>
        </div>

        {/* 6. CONNECTION DETAILS CARD */}
        <div style={{ padding: `${cardPadding}px`, flexGrow: 1 }} className="flex flex-col shrink-0 rounded-2xl bg-[#27272a]/80 backdrop-blur-xl border border-[#3f3f46]/80">
           <div style={{ marginBottom: `${Math.max(6, 12 * density)}px` }} className="flex items-center gap-2">
              <RouterLucide className="w-4 h-4 text-[#10B981]" strokeWidth={2} />
              <span className="text-[11px] font-semibold tracking-[0.055em] text-[#ffffff]">CONNECTION DETAILS</span>
           </div>

           <div className="flex flex-col">
              {/* Row 1 */}
              <div style={{ paddingTop: rowPadding, paddingBottom: rowPadding }} className="flex justify-between items-center border-b border-[#3f3f46]/80">
                 <span className="text-[11px] leading-none text-[#b4b4bb]">Connected to</span>
                 <div className="px-2.5 py-0.5 rounded-full bg-[#10b981]/10 text-[#34d399] text-[11px] leading-none font-semibold border border-[#10b981]/20">
                    {connInfo.ssid}
                 </div>
              </div>
              {/* Row 2 */}
              <div style={{ paddingTop: rowPadding, paddingBottom: rowPadding }} className="flex justify-between items-center border-b border-[#3f3f46]/80">
                 <span className="text-[11px] leading-none text-[#b4b4bb]">Signal</span>
                 <div className="flex items-center gap-2">
                    <SignalBars percent={connInfo.signalPercent} />
                    <span className="text-[11px] font-semibold text-white">{connInfo.signalPercent}%</span>
                 </div>
              </div>
              {/* Row 3 */}
              <div style={{ paddingTop: rowPadding, paddingBottom: rowPadding }} className="flex justify-between items-center border-b border-[#3f3f46]/80">
                 <span className="text-[11px] leading-none text-[#b4b4bb]">WiFi Technology</span>
                 <span className="text-[11px] font-semibold tracking-[-0.01em] text-white">{connInfo.wifiTechnology}</span>
              </div>
              {/* Row 4 */}
              <div style={{ paddingTop: rowPadding, paddingBottom: rowPadding }} className="flex justify-between items-center border-b border-[#3f3f46]/80">
                 <span className="text-[11px] leading-none text-[#b4b4bb]">Adapter</span>
                 <span className="text-[11px] font-semibold tracking-[-0.015em] text-white truncate max-w-[200px] text-right">{connInfo.adapter}</span>
              </div>
              {/* Row 5 */}
              <div style={{ paddingTop: rowPadding }} className="flex justify-between items-center">
                 <span className="text-[11px] leading-none text-[#b4b4bb]">Link Speed (Rx / Tx)</span>
                 <span className="text-[11px] font-semibold text-white">{connInfo.rxMbps} / {connInfo.txMbps} Mbps</span>
              </div>
           </div>
        </div>

        {/* 7. PROTECTION ENGINE CARD + ACTION stay together at the bottom. */}
        <div style={{ gap: `${sectionGap}px` }} className="flex flex-col shrink-0">
        <div style={{ padding: `${cardPadding}px` }} className="flex flex-col shrink-0 rounded-2xl bg-[#27272a]/80 backdrop-blur-xl border border-[#3f3f46]/80">
           <div style={{ marginBottom: `${Math.max(6, 12 * density)}px` }} className="flex items-center gap-2">
              <Shield className="w-4 h-4 text-[#10B981]" strokeWidth={2} />
              <span className="text-[11px] font-bold tracking-wider text-[#ffffff]">PROTECTION ENGINE</span>
           </div>

           <div className="flex flex-col">
              <div style={{ paddingTop: rowPadding, paddingBottom: rowPadding }} className="flex justify-between items-center border-b border-[#3f3f46]/80">
                 <span className="text-[11px] text-[#a1a1aa]">Last Recovery</span>
                 <span className="text-[12px] font-medium text-white">{formatRecovery(telemetry.lastRecovery)}</span>
              </div>

              <div style={{ paddingTop: rowPadding, paddingBottom: rowPadding }} className="flex justify-between items-center border-b border-[#3f3f46]/80">
                 <span className="text-[11px] text-[#a1a1aa]">Recovery Attempts</span>
                 <span className="text-[12px] font-medium text-white">{telemetry.reconnectAttempts} / {telemetry.maxAttempts}</span>
              </div>

              <div style={{ paddingTop: rowPadding }} className="flex justify-between items-center">
                 <span className="text-[11px] text-[#a1a1aa]">Next Check</span>
                 <div className="flex items-center gap-1.5">
                    <Timer className="w-4 h-4" style={{ color: isProtected ? "#10B981" : "#52525b" }} />
                    <span className="text-[12px] font-medium" style={{ color: isProtected ? "#ffffff" : "#52525b" }}>
                      {isProtected ? `${countdown} sec` : "—"}
                    </span>
                 </div>
              </div>
           </div>
        </div>

        {/* 8. REFERENCE ACTION (single full-width state button) */}
        <div style={{ height: `${Math.max(compact ? 46 : 52, 58 * density)}px` }} className="flex flex-row shrink-0">
           <motion.button
             whileTap={{ scale: 0.98 }}
             transition={{ duration: 0.16, ease: "easeOut" }}
             onClick={handleToggleEngine}
             disabled={engineActionPending}
             aria-busy={engineActionPending}
             className={cn(
               "w-full flex items-center justify-center gap-3 rounded-xl border transition-all h-full",
               isProtected
                 ? "border-[#ef4444] text-[#f87171] bg-transparent shadow-[0_0_14px_rgba(239,68,68,0.28)] cursor-pointer disabled:cursor-wait disabled:opacity-70"
                 : "border-[#10B981] text-[#10B981] bg-transparent shadow-[0_0_14px_rgba(16,185,129,0.24)] cursor-pointer disabled:cursor-wait disabled:opacity-70"
             )}
           >
              <Power className="w-[18px] h-[18px]" strokeWidth={2.5} />
              <span className="text-[14px] font-semibold">{isProtected ? "Stop Engine" : "Start Engine"}</span>
           </motion.button>
        </div>
        </div>

      </div>

      {/* Modals */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        initialSettings={{
          targetSsid: telemetry.targetSsid,
          checkInterval: telemetry.checkInterval,
          reconnectDelay: telemetry.reconnectDelay,
          maxAttempts: telemetry.maxAttempts,
          autoSwitchPrimary: telemetry.autoSwitchPrimary,
          enableNotifications: telemetry.enableNotifications,
          enableSoundAlerts: telemetry.enableSoundAlerts,
          autoStart: telemetry.autoStart,
          startMinimized: telemetry.startMinimized,
          minBitrateThreshold: protectedThreshold,
        }}
        availableSsids={telemetry.availableSsids}
        onSave={handleSaveSettings}
        onOpenLogs={() => {
          const electronAPI = typeof window !== "undefined"
            ? (window as Window & { electronAPI?: { openLogFile?: () => Promise<{ ok: boolean; error?: string | null }> } }).electronAPI
            : undefined;
          if (electronAPI?.openLogFile) {
            void electronAPI.openLogFile().then(result => {
              if (!result.ok) setActionError(result.error || "Unable to open the Guardian log file.");
            });
          } else {
            setActionError("View Log File is available in the Windows desktop app.");
          }
        }}
      />
      <AboutModal isOpen={isAboutOpen} onClose={() => setIsAboutOpen(false)} />
    </div>
  );
}
