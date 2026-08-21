'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { MoreHorizontal, Wifi, ShieldCheck, RotateCcw, ArrowUpRight, ArrowDownRight } from 'lucide-react';

interface ConnectionCardProps {
  currentSpeed?: number;
  threshold?: number;
  maxSpeed?: number;
  status?: string;
  uptime?: string;
  reconnectAttempts?: number;
  uploadSpeed?: number;
  downloadSpeed?: number;
  networkSsid?: string;
  channel?: number;
  band?: string;
}

export default function ConnectionCard({
  currentSpeed = 866.5,
  threshold = 300,
  maxSpeed = 1000,
  status = 'Active',
  uptime = '24h 12m',
  reconnectAttempts = 0,
  uploadSpeed = 866.5,
  downloadSpeed = 866.5,
  networkSsid = 'AC_WIFI_HQ',
  channel = 48,
  band = '5.0 GHz',
}: ConnectionCardProps) {
  // Calculate arc parameters for SVG gauge
  const radius = 110;
  const strokeWidth = 22;
  const center = 140;
  const arcLength = Math.PI * radius; // 180 degrees
  const speedRatio = Math.max(0, Math.min(1, currentSpeed / maxSpeed));
  const activeDash = speedRatio * arcLength;

  // Threshold arrow angle (300 Mbps)
  const threshRatio = threshold / maxSpeed;
  const threshAngleDeg = 180 * (1 - threshRatio);
  const threshRad = (threshAngleDeg * Math.PI) / 180;
  const threshX = center + (radius + 20) * Math.cos(threshRad);
  const threshY = center - (radius + 20) * Math.sin(threshRad);

  const isGoodQuality = currentSpeed >= threshold;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, delay: 0.2 }}
      className="rounded-2xl bg-[#16181A] border border-[#2A2F33] p-5 flex flex-col justify-between"
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Wifi className="w-4 h-4 text-[#22C55E]" />
          <h3 className="text-sm font-semibold text-[#F2F4F7]">Connection</h3>
        </div>
        <button className="text-[#6B7280] hover:text-[#F2F4F7] transition-colors">
          <MoreHorizontal className="w-5 h-5" />
        </button>
      </div>

      <div className="grid grid-cols-2 gap-2 mb-3">
        <div className="rounded-lg bg-[#1E2124] border border-[#2A2F33] p-2.5">
          <div className="flex items-center space-x-2 mb-1.5">
            <div className="p-1 rounded bg-[#2A2F33]">
              <ShieldCheck className="w-3.5 h-3.5 text-[#22C55E]" />
            </div>
            <span className="text-[10px] uppercase font-bold text-[#A1A7AE]">Status</span>
          </div>
          <div className="font-bold text-[#F2F4F7] text-sm">{status}</div>
          <div className="text-[10px] text-[#6B7280]">Uptime: {uptime}</div>
        </div>
        
        <div className="rounded-lg bg-[#1E2124] border border-[#2A2F33] p-2.5">
          <div className="flex items-center space-x-2 mb-1.5">
            <div className="p-1 rounded bg-[#2A2F33]">
              <RotateCcw className="w-3.5 h-3.5 text-[#F59E0B]" />
            </div>
            <span className="text-[10px] uppercase font-bold text-[#A1A7AE]">Reconnects</span>
          </div>
          <div className="font-bold text-[#F2F4F7] text-sm">{reconnectAttempts}</div>
          <div className="text-[10px] text-[#6B7280]">Last 24 hours</div>
        </div>

        <div className="rounded-lg bg-[#1E2124] border border-[#2A2F33] p-2.5">
          <div className="flex items-center space-x-2 mb-1.5">
            <div className="p-1 rounded bg-[#2A2F33]">
              <ArrowUpRight className="w-3.5 h-3.5 text-[#38BDF8]" />
            </div>
            <span className="text-[10px] uppercase font-bold text-[#A1A7AE]">Upload Link</span>
          </div>
          <div className="font-bold text-[#F2F4F7] text-sm">{uploadSpeed.toFixed(0)} Mbps</div>
          <div className="text-[10px] text-[#6B7280]">{band} / Ch {channel}</div>
        </div>

        <div className="rounded-lg bg-[#1E2124] border border-[#2A2F33] p-2.5">
          <div className="flex items-center space-x-2 mb-1.5">
            <div className="p-1 rounded bg-[#2A2F33]">
              <ArrowDownRight className="w-3.5 h-3.5 text-[#A78BFA]" />
            </div>
            <span className="text-[10px] uppercase font-bold text-[#A1A7AE]">Download Link</span>
          </div>
          <div className="font-bold text-[#F2F4F7] text-sm">{downloadSpeed.toFixed(0)} Mbps</div>
          <div className="text-[10px] text-[#6B7280]">TX Rate: {Math.round(uploadSpeed)} Mbps</div>
        </div>
      </div>

      <div className="border-t border-[#2A2F33] my-3" />

      {/* Curved Arc Gauge Bitrate Quality Meter */}
      <div className="relative flex flex-col items-center justify-center my-2">
        <svg width="280" height="160" viewBox="0 0 280 160" className="overflow-visible">
          {/* Background Track Arc */}
          <path
            d={`M 30 140 A ${radius} ${radius} 0 0 1 250 140`}
            fill="none"
            stroke="#2A2F33"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />

          {/* 3 Color Segment Fills */}
          {/* Red Zone 0-200 */}
          <path
            d={`M 30 140 A ${radius} ${radius} 0 0 1 250 140`}
            fill="none"
            stroke="#EF4444"
            strokeWidth={strokeWidth}
            strokeDasharray={`${(200 / maxSpeed) * arcLength} ${arcLength}`}
            strokeLinecap="round"
          />
          {/* Amber Zone 200-300 */}
          <path
            d={`M 30 140 A ${radius} ${radius} 0 0 1 250 140`}
            fill="none"
            stroke="#F59E0B"
            strokeWidth={strokeWidth}
            strokeDasharray={`${(100 / maxSpeed) * arcLength} ${arcLength}`}
            strokeDashoffset={`-${(200 / maxSpeed) * arcLength}`}
          />
          {/* Green Zone 300-1000 */}
          <motion.path
            d={`M 30 140 A ${radius} ${radius} 0 0 1 250 140`}
            fill="none"
            stroke="#22C55E"
            strokeWidth={strokeWidth}
            animate={{ strokeDasharray: `${activeDash} ${arcLength}` }}
            transition={{ duration: 0.8, ease: 'easeInOut' }}
            strokeDashoffset={`-${(300 / maxSpeed) * arcLength}`}
            strokeLinecap="round"
          />

          {/* Threshold Arrow Indicator */}
          <line
            x1={center + (radius - 12) * Math.cos(threshRad)}
            y1={center - (radius - 12) * Math.sin(threshRad)}
            x2={threshX}
            y2={threshY}
            stroke="#F2F4F7"
            strokeWidth="2"
          />
        </svg>

        {/* Center Text Block */}
        <div className="absolute top-14 flex flex-col items-center">
          <span className="text-xs text-[#A1A7AE]">Live Link Speed:</span>
          <span className="text-3xl font-bold text-[#F2F4F7] tracking-tight">{currentSpeed.toFixed(0)} Mbps</span>
          <span className="text-[10px] text-[#A1A7AE] mt-1">Minimum Required: {threshold} Mbps</span>
        </div>

        {/* Bottom Scale Labels */}
        <div className="w-full flex justify-between px-4 text-[10px] text-[#6B7280] -mt-4">
          <span>0</span>
          <span>0-1000 Mbps</span>
        </div>
      </div>

      <div className="mt-4 space-y-1.5">
        <div className="text-xs text-[#A1A7AE]">
          📶 Current Network: <span className="font-bold text-[#F2F4F7]">{networkSsid}</span>
        </div>
        <div className="text-xs text-[#A1A7AE]">
          {isGoodQuality ? '🟢' : '🔴'} Connection Quality: <span className="font-bold text-[#F2F4F7]">{isGoodQuality ? 'Excellent' : 'Poor'}</span>
        </div>
      </div>
    </motion.div>
  );
}
