'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { MoreHorizontal, Wifi } from 'lucide-react';

interface ConnectionCardProps {
  currentSpeed?: number;
  threshold?: number;
  maxSpeed?: number;
}

export default function ConnectionCard({
  currentSpeed = 866.5,
  threshold = 300,
  maxSpeed = 1000,
}: ConnectionCardProps) {
  // Calculate arc parameters for SVG gauge
  const radius = 120;
  const strokeWidth = 22;
  const center = 150;
  const arcLength = Math.PI * radius; // 180 degrees
  const speedRatio = Math.max(0, Math.min(1, currentSpeed / maxSpeed));
  const activeDash = speedRatio * arcLength;

  // Threshold arrow angle (300 Mbps)
  const threshRatio = threshold / maxSpeed;
  const threshAngleDeg = 180 * (1 - threshRatio);
  const threshRad = (threshAngleDeg * Math.PI) / 180;
  const threshX = center + (radius + 20) * Math.cos(threshRad);
  const threshY = center - (radius + 20) * Math.sin(threshRad);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, delay: 0.2 }}
      className="rounded-2xl bg-[#16181A] border border-[#2A2F33] p-5 flex flex-col justify-between"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Wifi className="w-4 h-4 text-[#22C55E]" />
          <h3 className="text-sm font-semibold text-[#F2F4F7]">Connection Card</h3>
        </div>
        <button className="text-[#6B7280] hover:text-[#F2F4F7] transition-colors">
          <MoreHorizontal className="w-5 h-5" />
        </button>
      </div>

      {/* Curved Arc Gauge Bitrate Quality Meter */}
      <div className="relative flex flex-col items-center justify-center my-4">
        <svg width="300" height="170" viewBox="0 0 300 170" className="overflow-visible">
          {/* Background Track Arc */}
          <path
            d="M 30 150 A 120 120 0 0 1 270 150"
            fill="none"
            stroke="#2A2F33"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />

          {/* 3 Color Segment Fills */}
          {/* Red Zone 0-200 */}
          <path
            d="M 30 150 A 120 120 0 0 1 270 150"
            fill="none"
            stroke="#EF4444"
            strokeWidth={strokeWidth}
            strokeDasharray={`${(200 / maxSpeed) * arcLength} ${arcLength}`}
            strokeLinecap="round"
          />
          {/* Amber Zone 200-300 */}
          <path
            d="M 30 150 A 120 120 0 0 1 270 150"
            fill="none"
            stroke="#F59E0B"
            strokeWidth={strokeWidth}
            strokeDasharray={`${(100 / maxSpeed) * arcLength} ${arcLength}`}
            strokeDashoffset={`-${(200 / maxSpeed) * arcLength}`}
          />
          {/* Green Zone 300-1000 */}
          <path
            d="M 30 150 A 120 120 0 0 1 270 150"
            fill="none"
            stroke="#22C55E"
            strokeWidth={strokeWidth}
            strokeDasharray={`${activeDash} ${arcLength}`}
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
        <div className="absolute top-16 flex flex-col items-center">
          <span className="text-xs text-[#A1A7AE]">Live Link Speed:</span>
          <span className="text-3xl font-bold text-[#F2F4F7] tracking-tight">{currentSpeed.toFixed(0)} Mbps</span>
          <span className="text-xs text-[#A1A7AE] mt-1">Minimum Required: {threshold} Mbps</span>
        </div>

        {/* Bottom Scale Labels */}
        <div className="w-full flex justify-between px-6 text-xs text-[#6B7280] -mt-2">
          <span>0</span>
          <span>0-1000 Mbps</span>
        </div>
      </div>
    </motion.div>
  );
}
