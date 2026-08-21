'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Shield, RotateCcw, Activity, Pause } from 'lucide-react';

interface ProtectionEngineCardProps {
  networkSsid?: string;
  onReconnect?: () => void;
  onToggleProtection?: () => void;
}

export default function ProtectionEngineCard({
  networkSsid = 'AC_WIFI_HQ',
  onReconnect,
  onToggleProtection,
}: ProtectionEngineCardProps) {
  const [monitoringOn, setMonitoringOn] = useState(true);
  const [recoveryOn, setRecoveryOn] = useState(true);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, delay: 0.25 }}
      className="rounded-2xl bg-[#16181A] border border-[#2A2F33] p-5 flex flex-col justify-between"
    >
      <div className="flex items-center space-x-2">
        <Shield className="w-4 h-4 text-[#22C55E]" />
        <h3 className="text-sm font-semibold text-[#F2F4F7]">Protection Engine</h3>
      </div>

      <div className="space-y-3 my-3">
        {/* Connection Monitoring Row */}
        <div className="flex items-center justify-between p-3 rounded-lg bg-[#1E2124] border border-[#2A2F33]">
          <div className="flex items-center space-x-2">
            <Activity className="w-4 h-4 text-[#A1A7AE]" />
            <span className="text-xs text-[#F2F4F7]">Connection Monitoring</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-semibold text-[#22C55E]">Active</span>
            <button
              onClick={() => setMonitoringOn(!monitoringOn)}
              className={`w-9 h-5 flex items-center rounded-full p-0.5 transition-colors ${
                monitoringOn ? 'bg-[#22C55E]' : 'bg-[#2A2F33]'
              }`}
            >
              <div
                className={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform ${
                  monitoringOn ? 'translate-x-4' : 'translate-x-0'
                }`}
              />
            </button>
          </div>
        </div>

        {/* Low Speed Recovery Row */}
        <div className="flex items-center justify-between p-3 rounded-lg bg-[#1E2124] border border-[#2A2F33]">
          <div className="flex items-center space-x-2">
            <RotateCcw className="w-4 h-4 text-[#A1A7AE]" />
            <span className="text-xs text-[#F2F4F7]">Low Speed Recovery</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-semibold text-[#22C55E]">Active</span>
            <button
              onClick={() => setRecoveryOn(!recoveryOn)}
              className={`w-9 h-5 flex items-center rounded-full p-0.5 transition-colors ${
                recoveryOn ? 'bg-[#22C55E]' : 'bg-[#2A2F33]'
              }`}
            >
              <div
                className={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform ${
                  recoveryOn ? 'translate-x-4' : 'translate-x-0'
                }`}
              />
            </button>
          </div>
        </div>

      </div>

      {/* Action Buttons */}
      <div className="space-y-2 mt-1">
        <button
          onClick={onReconnect}
          className="w-full py-2.5 px-4 rounded-lg border border-[#22C55E] text-[#22C55E] bg-transparent hover:bg-[#22C55E] hover:text-[#051D0D] text-xs font-bold transition-all flex items-center justify-center space-x-2"
        >
          <RotateCcw className="w-4 h-4" />
          <span>Reconnect now</span>
        </button>

        <button
          onClick={onToggleProtection}
          className="w-full py-2 px-4 rounded-lg border border-[#F59E0B] text-[#F59E0B] bg-transparent hover:bg-[#F59E0B] hover:text-[#121212] text-xs font-bold transition-colors flex items-center justify-center space-x-2"
        >
          <Pause className="w-4 h-4" />
          <span>Stop protection</span>
        </button>
      </div>
    </motion.div>
  );
}
