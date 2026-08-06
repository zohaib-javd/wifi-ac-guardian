'use client';

import React, { useState } from 'react';
import { X, Settings, Shield, Wifi, Bell, Sliders } from 'lucide-react';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const [targetSsid, setTargetSsid] = useState('lab5g');
  const [checkInterval, setCheckInterval] = useState(10);
  const [reconnectDelay, setReconnectDelay] = useState(15);
  const [maxAttempts, setMaxAttempts] = useState(99);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="w-[640px] h-[520px] bg-[#16181A] border border-[#2A2F33] rounded-2xl flex overflow-hidden shadow-2xl">
        {/* Sidebar */}
        <div className="w-44 bg-[#1E2124] border-r border-[#2A2F33] p-4 flex flex-col space-y-2">
          <span className="text-[11px] font-bold text-[#6B7280] uppercase tracking-wider mb-2">SETTINGS</span>
          <button className="flex items-center space-x-2 px-3 py-2 rounded-lg bg-[#2A2F33] text-[#F2F4F7] text-xs font-medium">
            <Wifi className="w-4 h-4 text-[#22C55E]" />
            <span>Wi-Fi Network</span>
          </button>
          <button className="flex items-center space-x-2 px-3 py-2 rounded-lg text-[#A1A7AE] hover:bg-[#2A2F33]/50 text-xs font-medium">
            <Shield className="w-4 h-4" />
            <span>Protection</span>
          </button>
          <button className="flex items-center space-x-2 px-3 py-2 rounded-lg text-[#A1A7AE] hover:bg-[#2A2F33]/50 text-xs font-medium">
            <Bell className="w-4 h-4" />
            <span>Notifications</span>
          </button>
          <button className="flex items-center space-x-2 px-3 py-2 rounded-lg text-[#A1A7AE] hover:bg-[#2A2F33]/50 text-xs font-medium">
            <Sliders className="w-4 h-4" />
            <span>Advanced</span>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-[#2A2F33] pb-3">
              <h3 className="text-base font-bold text-[#F2F4F7]">Primary Network & Preferences</h3>
              <button onClick={onClose} className="text-[#6B7280] hover:text-[#F2F4F7]">
                <X className="w-5 h-5" />
              </button>
            </div>

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
          </div>

          <button
            onClick={onClose}
            className="w-full py-2.5 bg-[#22C55E] hover:bg-[#2BE06B] text-[#051D0D] font-bold rounded-lg text-xs transition-colors"
          >
            Save Settings
          </button>
        </div>
      </div>
    </div>
  );
}
