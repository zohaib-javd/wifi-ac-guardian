'use client';

import React, { useState } from 'react';
import { X, Settings, Shield, Wifi, Bell, Sliders, FileText } from 'lucide-react';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onOpenLogs?: () => void;
}

export default function SettingsModal({ isOpen, onClose, onOpenLogs }: SettingsModalProps) {
  const [activeTab, setActiveTab] = useState<'wifi' | 'protection' | 'notifications' | 'advanced'>('wifi');

  const [targetSsid, setTargetSsid] = useState('lab5g');
  const [checkInterval, setCheckInterval] = useState(10);
  const [reconnectDelay, setReconnectDelay] = useState(15);
  const [maxAttempts, setMaxAttempts] = useState(99);

  const [minBitrateThreshold, setMinBitrateThreshold] = useState(300);
  const [autoSwitchPrimary, setAutoSwitchPrimary] = useState(true);

  const [enableNotifications, setEnableNotifications] = useState(true);
  const [enableSoundAlerts, setEnableSoundAlerts] = useState(false);

  const [autoStart, setAutoStart] = useState(true);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="w-[600px] h-[480px] bg-[#16181A] border border-[#2A2F33] rounded-2xl flex overflow-hidden shadow-2xl">
        {/* Sidebar */}
        <div className="w-48 bg-[#1E2124] border-r border-[#2A2F33] p-4 flex flex-col space-y-1.5">
          <span className="text-[11px] font-bold text-[#6B7280] uppercase tracking-wider mb-2">SETTINGS</span>
          
          <button
            onClick={() => setActiveTab('wifi')}
            className={`flex items-center space-x-2.5 px-3 py-2.5 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'wifi'
                ? 'bg-[#2A2F33] text-[#F2F4F7] border border-[#22C55E]/40 shadow'
                : 'text-[#A1A7AE] hover:bg-[#2A2F33]/40'
            }`}
          >
            <Wifi className={`w-4 h-4 ${activeTab === 'wifi' ? 'text-[#22C55E]' : ''}`} />
            <span>Wi-Fi Network</span>
          </button>

          <button
            onClick={() => setActiveTab('protection')}
            className={`flex items-center space-x-2.5 px-3 py-2.5 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'protection'
                ? 'bg-[#2A2F33] text-[#F2F4F7] border border-[#22C55E]/40 shadow'
                : 'text-[#A1A7AE] hover:bg-[#2A2F33]/40'
            }`}
          >
            <Shield className={`w-4 h-4 ${activeTab === 'protection' ? 'text-[#22C55E]' : ''}`} />
            <span>Protection</span>
          </button>

          <button
            onClick={() => setActiveTab('notifications')}
            className={`flex items-center space-x-2.5 px-3 py-2.5 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'notifications'
                ? 'bg-[#2A2F33] text-[#F2F4F7] border border-[#22C55E]/40 shadow'
                : 'text-[#A1A7AE] hover:bg-[#2A2F33]/40'
            }`}
          >
            <Bell className={`w-4 h-4 ${activeTab === 'notifications' ? 'text-[#22C55E]' : ''}`} />
            <span>Notifications</span>
          </button>

          <button
            onClick={() => setActiveTab('advanced')}
            className={`flex items-center space-x-2.5 px-3 py-2.5 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'advanced'
                ? 'bg-[#2A2F33] text-[#F2F4F7] border border-[#22C55E]/40 shadow'
                : 'text-[#A1A7AE] hover:bg-[#2A2F33]/40'
            }`}
          >
            <Sliders className={`w-4 h-4 ${activeTab === 'advanced' ? 'text-[#22C55E]' : ''}`} />
            <span>Advanced</span>
          </button>
        </div>

        {/* Content Panel */}
        <div className="flex-1 p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-[#2A2F33] pb-3">
              <h3 className="text-sm font-bold text-[#F2F4F7]">
                {activeTab === 'wifi' && 'Primary Network & Timing'}
                {activeTab === 'protection' && 'Protection Engine Settings'}
                {activeTab === 'notifications' && 'Notification Preferences'}
                {activeTab === 'advanced' && 'Advanced Options & Logs'}
              </h3>
              <button onClick={onClose} className="text-[#6B7280] hover:text-[#F2F4F7] transition-colors">
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Tab 1: Wi-Fi Network */}
            {activeTab === 'wifi' && (
              <div className="mt-4 space-y-4 text-xs">
                <div>
                  <label className="block text-[#A1A7AE] font-semibold mb-1">Target SSID</label>
                  <input
                    type="text"
                    value={targetSsid}
                    onChange={(e) => setTargetSsid(e.target.value)}
                    className="w-full px-3 py-2 bg-[#1E2124] border border-[#2A2F33] rounded-lg text-[#F2F4F7] focus:border-[#22C55E] outline-none"
                  />
                </div>

                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="block text-[#A1A7AE] font-semibold mb-1">Check Interval (s)</label>
                    <input
                      type="number"
                      value={checkInterval}
                      onChange={(e) => setCheckInterval(Number(e.target.value))}
                      className="w-full px-3 py-2 bg-[#1E2124] border border-[#2A2F33] rounded-lg text-[#F2F4F7] focus:border-[#22C55E] outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-[#A1A7AE] font-semibold mb-1">Retry Delay (s)</label>
                    <input
                      type="number"
                      value={reconnectDelay}
                      onChange={(e) => setReconnectDelay(Number(e.target.value))}
                      className="w-full px-3 py-2 bg-[#1E2124] border border-[#2A2F33] rounded-lg text-[#F2F4F7] focus:border-[#22C55E] outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-[#A1A7AE] font-semibold mb-1">Max Attempts</label>
                    <input
                      type="number"
                      value={maxAttempts}
                      onChange={(e) => setMaxAttempts(Number(e.target.value))}
                      className="w-full px-3 py-2 bg-[#1E2124] border border-[#2A2F33] rounded-lg text-[#F2F4F7] focus:border-[#22C55E] outline-none"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Tab 2: Protection */}
            {activeTab === 'protection' && (
              <div className="mt-4 space-y-4 text-xs">
                <div>
                  <label className="block text-[#A1A7AE] font-semibold mb-1">Minimum Required Bitrate (Mbps)</label>
                  <input
                    type="number"
                    value={minBitrateThreshold}
                    onChange={(e) => setMinBitrateThreshold(Number(e.target.value))}
                    className="w-full px-3 py-2 bg-[#1E2124] border border-[#2A2F33] rounded-lg text-[#F2F4F7] focus:border-[#22C55E] outline-none"
                  />
                  <p className="text-[11px] text-[#6B7280] mt-1">Triggers hardware reset if link speed falls below threshold.</p>
                </div>

                <div className="flex items-center justify-between p-3 rounded-lg bg-[#1E2124] border border-[#2A2F33]">
                  <div>
                    <span className="block font-semibold text-[#F2F4F7]">Auto-Switch to Primary Network</span>
                    <span className="text-[11px] text-[#6B7280]">Automatically return to {targetSsid} when available</span>
                  </div>
                  <button
                    onClick={() => setAutoSwitchPrimary(!autoSwitchPrimary)}
                    className={`w-9 h-5 flex items-center rounded-full p-0.5 transition-colors ${
                      autoSwitchPrimary ? 'bg-[#22C55E]' : 'bg-[#2A2F33]'
                    }`}
                  >
                    <div
                      className={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform ${
                        autoSwitchPrimary ? 'translate-x-4' : 'translate-x-0'
                      }`}
                    />
                  </button>
                </div>
              </div>
            )}

            {/* Tab 3: Notifications */}
            {activeTab === 'notifications' && (
              <div className="mt-4 space-y-3 text-xs">
                <div className="flex items-center justify-between p-3 rounded-lg bg-[#1E2124] border border-[#2A2F33]">
                  <div>
                    <span className="block font-semibold text-[#F2F4F7]">Windows Toast Notifications</span>
                    <span className="text-[11px] text-[#6B7280]">Show alert when link speed drops or reconnects</span>
                  </div>
                  <button
                    onClick={() => setEnableNotifications(!enableNotifications)}
                    className={`w-9 h-5 flex items-center rounded-full p-0.5 transition-colors ${
                      enableNotifications ? 'bg-[#22C55E]' : 'bg-[#2A2F33]'
                    }`}
                  >
                    <div
                      className={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform ${
                        enableNotifications ? 'translate-x-4' : 'translate-x-0'
                      }`}
                    />
                  </button>
                </div>

                <div className="flex items-center justify-between p-3 rounded-lg bg-[#1E2124] border border-[#2A2F33]">
                  <div>
                    <span className="block font-semibold text-[#F2F4F7]">Sound Alerts</span>
                    <span className="text-[11px] text-[#6B7280]">Play sound chime on reconnection</span>
                  </div>
                  <button
                    onClick={() => setEnableSoundAlerts(!enableSoundAlerts)}
                    className={`w-9 h-5 flex items-center rounded-full p-0.5 transition-colors ${
                      enableSoundAlerts ? 'bg-[#22C55E]' : 'bg-[#2A2F33]'
                    }`}
                  >
                    <div
                      className={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform ${
                        enableSoundAlerts ? 'translate-x-4' : 'translate-x-0'
                      }`}
                    />
                  </button>
                </div>
              </div>
            )}

            {/* Tab 4: Advanced */}
            {activeTab === 'advanced' && (
              <div className="mt-4 space-y-3 text-xs">
                <div className="flex items-center justify-between p-3 rounded-lg bg-[#1E2124] border border-[#2A2F33]">
                  <div>
                    <span className="block font-semibold text-[#F2F4F7]">Run at Windows Startup</span>
                    <span className="text-[11px] text-[#6B7280]">Start WiFi AC Guardian automatically on boot</span>
                  </div>
                  <button
                    onClick={() => setAutoStart(!autoStart)}
                    className={`w-9 h-5 flex items-center rounded-full p-0.5 transition-colors ${
                      autoStart ? 'bg-[#22C55E]' : 'bg-[#2A2F33]'
                    }`}
                  >
                    <div
                      className={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform ${
                        autoStart ? 'translate-x-4' : 'translate-x-0'
                      }`}
                    />
                  </button>
                </div>

                <button
                  onClick={onOpenLogs}
                  className="w-full py-2.5 px-4 rounded-lg bg-[#1E2124] hover:bg-[#252A2F] text-[#F2F4F7] font-semibold border border-[#2A2F33] transition-colors flex items-center justify-center space-x-2"
                >
                  <FileText className="w-4 h-4 text-[#A1A7AE]" />
                  <span>View Application Log File</span>
                </button>
              </div>
            )}
          </div>

          <button
            onClick={onClose}
            className="w-full py-2.5 bg-[#22C55E] hover:bg-[#2BE06B] text-[#051D0D] font-bold rounded-lg text-xs transition-colors mt-4"
          >
            Save Settings
          </button>
        </div>
      </div>
    </div>
  );
}
