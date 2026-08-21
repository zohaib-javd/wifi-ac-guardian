'use client';

/* WiFi AC Guardian design: compact dark utility controls, clear helper text, and emerald state accents. */
import React, { useEffect, useRef, useState } from 'react';
import { FileText, Settings, Shield, Sliders, Wifi, X } from 'lucide-react';

export interface GuardianSettings {
  targetSsid: string;
  checkInterval: number;
  reconnectDelay: number;
  maxAttempts: number;
  autoSwitchPrimary: boolean;
  enableNotifications: boolean;
  enableSoundAlerts: boolean;
  autoStart: boolean;
  startMinimized: boolean;
  minBitrateThreshold: number;
}

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onOpenLogs?: () => void;
  onSave?: (settings: GuardianSettings) => Promise<void> | void;
  initialSettings?: GuardianSettings;
  availableSsids?: string[];
}

const CHECK_INTERVALS = [30, 60, 300, 600] as const;
const RECOVERY_DELAYS = [15, 5, 30, 45, 60] as const;
const MAX_RECOVERY_ATTEMPTS = [50, 25, 15, 10, 5] as const;
const BITRATE_THRESHOLDS = [100, 150, 200, 250, 300, 350, 400, 500] as const;

function supportedValue(value: number | undefined, values: readonly number[], fallback: number) {
  return typeof value === 'number' && values.includes(value) ? value : fallback;
}

function SettingToggle({ enabled, onToggle }: { enabled: boolean; onToggle: () => void }) {
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-pressed={enabled}
      className={`w-10 h-6 shrink-0 flex items-center rounded-full p-1 transition-colors ${enabled ? 'bg-[#22C55E]' : 'bg-[#2A2F33]'}`}
    >
      <span className={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform ${enabled ? 'translate-x-4' : 'translate-x-0'}`} />
    </button>
  );
}

function SettingsSection({ title, helper, children }: { title: string; helper?: string; children: React.ReactNode }) {
  return (
    <section className="space-y-1.5">
      <h3 className="text-[12px] font-semibold text-[#F2F4F7]">{title}</h3>
      {helper && <p className="text-[10px] leading-snug text-[#6B7280]">{helper}</p>}
      {children}
    </section>
  );
}

export default function SettingsModal({ isOpen, onClose, onOpenLogs, onSave, initialSettings, availableSsids = [] }: SettingsModalProps) {
  const [activeTab, setActiveTab] = useState<'general' | 'wifi' | 'protection' | 'advanced'>('general');
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState('');
  const wasOpenRef = useRef(false);

  const [targetSsid, setTargetSsid] = useState('lab5g');
  const [checkInterval, setCheckInterval] = useState(30);
  const [reconnectDelay, setReconnectDelay] = useState(15);
  const [maxAttempts, setMaxAttempts] = useState(50);
  const [minBitrateThreshold, setMinBitrateThreshold] = useState(300);
  const [autoSwitchPrimary, setAutoSwitchPrimary] = useState(true);
  const [autoStart, setAutoStart] = useState(true);
  const [startMinimized, setStartMinimized] = useState(false);
  const [enableNotifications, setEnableNotifications] = useState(false);
  const [enableSoundAlerts, setEnableSoundAlerts] = useState(false);

  useEffect(() => {
    if (isOpen && !wasOpenRef.current && initialSettings) {
      setTargetSsid(initialSettings.targetSsid || 'lab5g');
      setCheckInterval(supportedValue(initialSettings.checkInterval, CHECK_INTERVALS, 30));
      setReconnectDelay(supportedValue(initialSettings.reconnectDelay, RECOVERY_DELAYS, 15));
      setMaxAttempts(supportedValue(initialSettings.maxAttempts, MAX_RECOVERY_ATTEMPTS, 50));
      setMinBitrateThreshold(supportedValue(initialSettings.minBitrateThreshold, BITRATE_THRESHOLDS, 300));
      setAutoSwitchPrimary(initialSettings.autoSwitchPrimary ?? true);
      setAutoStart(initialSettings.autoStart ?? true);
      setStartMinimized(initialSettings.startMinimized ?? false);
      // Alerts no longer have a user-facing tab; preserve any saved values when another setting is changed.
      setEnableNotifications(initialSettings.enableNotifications ?? false);
      setEnableSoundAlerts(initialSettings.enableSoundAlerts ?? false);
    }
    wasOpenRef.current = isOpen;
  }, [isOpen, initialSettings]);

  if (!isOpen) return null;

  const handleSave = async () => {
    if (isSaving) return;
    setSaveError('');
    setIsSaving(true);
    try {
      await onSave?.({
        targetSsid,
        checkInterval,
        reconnectDelay,
        maxAttempts,
        autoSwitchPrimary,
        enableNotifications,
        enableSoundAlerts,
        autoStart,
        startMinimized,
        minBitrateThreshold,
      });
      onClose();
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : 'Unable to save settings.');
    } finally {
      setIsSaving(false);
    }
  };

  const tabs = [
    { id: 'general', icon: Settings, label: 'General' },
    { id: 'wifi', icon: Wifi, label: 'Wi-Fi' },
    { id: 'protection', icon: Shield, label: 'Protection' },
    { id: 'advanced', icon: Sliders, label: 'Advanced' },
  ] as const;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="w-full max-w-[390px] max-h-[90vh] bg-[#16181A] border border-[#2A2F33] rounded-2xl flex flex-col overflow-hidden shadow-2xl">
        <div className="bg-[#1E2124] border-b border-[#2A2F33] flex flex-col pt-3 px-2 shrink-0">
          <div className="flex justify-between items-center px-2 mb-3">
            <span className="text-[12px] font-bold text-[#F2F4F7] uppercase tracking-wider">Settings</span>
            <button onClick={onClose} aria-label="Close settings" className="text-[#6B7280] hover:text-[#F2F4F7] transition-colors p-1">
              <X className="w-5 h-5" />
            </button>
          </div>
          <div className="grid grid-cols-4 gap-1 pb-2">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex min-w-0 items-center justify-center gap-1 px-1 py-2 rounded-lg text-[10px] font-semibold transition-all whitespace-nowrap ${activeTab === tab.id ? 'bg-[#2A2F33] text-[#F2F4F7] border border-[#22C55E]/40 shadow' : 'text-[#A1A7AE] hover:bg-[#2A2F33]/40'}`}
              >
                <tab.icon className={`w-3.5 h-3.5 shrink-0 ${activeTab === tab.id ? 'text-[#22C55E]' : ''}`} />
                <span className="truncate">{tab.label}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 min-h-0 no-scrollbar">
          {activeTab === 'general' && (
            <div className="space-y-3 text-xs">
              <div className="flex items-center justify-between gap-3 p-3 rounded-lg bg-[#1E2124] border border-[#2A2F33]">
                <div className="pr-2">
                  <span className="block font-semibold text-[#F2F4F7] mb-0.5">Run at Startup</span>
                  <span className="text-[10px] text-[#6B7280]">Start automatically on boot</span>
                </div>
                <SettingToggle enabled={autoStart} onToggle={() => setAutoStart(value => !value)} />
              </div>
              <div className="flex items-center justify-between gap-3 p-3 rounded-lg bg-[#1E2124] border border-[#2A2F33]">
                <div className="pr-2">
                  <span className="block font-semibold text-[#F2F4F7] mb-0.5">Start Minimized</span>
                  <span className="text-[10px] text-[#6B7280]">Launch in the system tray</span>
                </div>
                <SettingToggle enabled={startMinimized} onToggle={() => setStartMinimized(value => !value)} />
              </div>
            </div>
          )}

          {activeTab === 'wifi' && (
            <div className="space-y-4 text-xs">
              <SettingsSection title="Target WiFi Connection" helper="Select the WiFi Connection for Protection">
                <select value={targetSsid} onChange={(event) => setTargetSsid(event.target.value)} className="w-full px-3 py-2.5 bg-[#1E2124] border border-[#2A2F33] rounded-lg text-[#F2F4F7] focus:border-[#22C55E] outline-none">
                  {availableSsids.length > 0
                    ? availableSsids.map(ssid => <option key={ssid} value={ssid}>{ssid}</option>)
                    : <option value={targetSsid}>No paired networks currently in range</option>}
                </select>
              </SettingsSection>
              <div className="flex items-center justify-between gap-3 p-3 rounded-lg bg-[#1E2124] border border-[#2A2F33]">
                <div className="pr-2">
                  <span className="block font-semibold text-[#F2F4F7] mb-0.5">Auto-Switch to Primary</span>
                  <span className="text-[10px] leading-tight text-[#6B7280]">Return to Target WiFi Connection when available.</span>
                </div>
                <SettingToggle enabled={autoSwitchPrimary} onToggle={() => setAutoSwitchPrimary(value => !value)} />
              </div>
            </div>
          )}

          {activeTab === 'protection' && (
            <div className="space-y-5 text-xs">
              <SettingsSection title="Monitoring" helper="How often should Guardian check your connection?">
                <select value={checkInterval} onChange={(event) => setCheckInterval(Number(event.target.value))} className="w-full px-3 py-2.5 bg-[#1E2124] border border-[#2A2F33] rounded-lg text-[#F2F4F7] focus:border-[#22C55E] outline-none">
                  <option value={30}>Every 30 seconds (Default)</option>
                  <option value={60}>Every 1 minute</option>
                  <option value={300}>Every 5 minutes</option>
                  <option value={600}>Every 10 minutes</option>
                </select>
              </SettingsSection>
              <SettingsSection title="Recovery" helper="How quickly should Guardian retry after a connection problem?">
                <select value={reconnectDelay} onChange={(event) => setReconnectDelay(Number(event.target.value))} className="w-full px-3 py-2.5 bg-[#1E2124] border border-[#2A2F33] rounded-lg text-[#F2F4F7] focus:border-[#22C55E] outline-none">
                  <option value={15}>After 15 seconds (Default)</option>
                  <option value={5}>After 5 seconds</option>
                  <option value={30}>After 30 seconds</option>
                  <option value={45}>After 45 seconds</option>
                  <option value={60}>After 60 seconds</option>
                </select>
              </SettingsSection>
              <SettingsSection title="Maximum recovery attempts">
                <select value={maxAttempts} onChange={(event) => setMaxAttempts(Number(event.target.value))} className="w-full px-3 py-2.5 bg-[#1E2124] border border-[#2A2F33] rounded-lg text-[#F2F4F7] focus:border-[#22C55E] outline-none">
                  <option value={50}>50 attempts (Max)</option>
                  <option value={25}>25 attempts</option>
                  <option value={15}>15 attempts</option>
                  <option value={10}>10 attempts</option>
                  <option value={5}>5 attempts</option>
                </select>
              </SettingsSection>
            </div>
          )}

          {activeTab === 'advanced' && (
            <div className="space-y-4 text-xs">
              <SettingsSection title="Min Bitrate Threshold (Mbps)" helper="Triggers Hardware reset if link speed falls below threshold.">
                <select value={minBitrateThreshold} onChange={(event) => setMinBitrateThreshold(Number(event.target.value))} className="w-full px-3 py-2.5 bg-[#1E2124] border border-[#2A2F33] rounded-lg text-[#F2F4F7] focus:border-[#22C55E] outline-none">
                  <option value={100}>100</option>
                  <option value={150}>150</option>
                  <option value={200}>200</option>
                  <option value={250}>250</option>
                  <option value={300}>300 (Default)</option>
                  <option value={350}>350</option>
                  <option value={400}>400</option>
                  <option value={500}>500</option>
                </select>
              </SettingsSection>
              <button onClick={onOpenLogs} className="w-full py-3 px-4 rounded-lg bg-[#1E2124] hover:bg-[#252A2F] text-[#F2F4F7] font-semibold border border-[#2A2F33] transition-colors flex items-center justify-center gap-2">
                <FileText className="w-4 h-4 text-[#A1A7AE]" />
                <span>View Log File</span>
              </button>
            </div>
          )}
        </div>

        <div className="p-4 border-t border-[#2A2F33] shrink-0">
          {saveError && <p role="alert" className="mb-2 text-[11px] text-red-300">{saveError}</p>}
          <button onClick={handleSave} disabled={isSaving} className="w-full py-3 bg-[#22C55E] hover:bg-[#2BE06B] disabled:cursor-wait disabled:opacity-70 text-[#051D0D] font-bold rounded-lg text-xs transition-colors">
            {isSaving ? 'Saving…' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  );
}
