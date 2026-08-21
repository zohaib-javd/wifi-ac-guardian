'use client';

import React, { useEffect, useState } from 'react';
import { motion, useMotionValue, animate } from 'framer-motion';

interface SpeedGaugeProps {
  speed: number;
  maxSpeed: number;
  minRequired: number;
}

export default function SpeedGauge({ speed, maxSpeed, minRequired }: SpeedGaugeProps) {
  const [displaySpeed, setDisplaySpeed] = useState(0);
  const count = useMotionValue(0);

  const fillFraction = Math.min(speed / maxSpeed, 1);
  const fillPercent = fillFraction * 100;
  
  const minFraction = minRequired / maxSpeed;
  const minPercent = minFraction * 100;
  
  const isWarning = speed < minRequired;

  useEffect(() => {
    const animation = animate(count, speed, {
      duration: 0.7,
      type: "spring",
      stiffness: 100,
      damping: 15,
      onUpdate: (latest) => {
        setDisplaySpeed(Math.round(latest));
      }
    });
    return animation.stop;
  }, [speed, count]);

  return (
    <div className="w-full h-full flex flex-col justify-center min-h-0 relative">
      
      {/* Top Readout */}
      <div className="flex items-baseline space-x-2 mb-6 sm:mb-8">
        <div className="text-[40px] leading-none font-extrabold text-white tracking-tight" style={{ fontFamily: 'system-ui, -apple-system, sans-serif' }}>
          {displaySpeed}
        </div>
        <div className="text-[18px] font-semibold text-zinc-400">
          Mbps
        </div>
      </div>

      {/* Bar Area */}
      <div className="relative w-full pt-6 pb-6">
        
        {/* Min Marker Label (ABOVE the bar) */}
        <div 
          className="absolute top-0 -translate-x-1/2 flex flex-col items-center pointer-events-none"
          style={{ left: `${minPercent}%` }}
        >
          <span className="text-[10px] sm:text-[11px] uppercase font-bold text-amber-500 mb-1 leading-none tracking-wide">
            Min 300
          </span>
          <div className="w-0.5 h-3 bg-amber-500 rounded-full" />
        </div>

        {/* The Track */}
        <div className="w-full h-2.5 sm:h-3 bg-zinc-800 rounded-full relative overflow-visible z-10">
          
          {/* Ticks (underneath the bar fill visually or on top? We will put them on the track background) */}
          <div className="absolute inset-0 w-full h-full pointer-events-none z-20 flex justify-between px-1">
            {Array.from({ length: 11 }).map((_, i) => (
              <div key={i} className="h-full w-px bg-zinc-700/50" />
            ))}
          </div>

          {/* Fill Bar */}
          <motion.div
            className={`absolute left-0 top-0 bottom-0 rounded-full z-30 ${isWarning ? 'bg-amber-500' : 'bg-gradient-to-r from-emerald-400 to-cyan-400'}`}
            style={{ width: `${fillPercent}%` }}
            initial={{ width: 0 }}
            animate={{ width: `${fillPercent}%` }}
            transition={{ duration: 0.7, type: "spring", stiffness: 100, damping: 15 }}
          />

          {/* Glow for fill bar */}
          <motion.div
            className={`absolute left-0 top-0 bottom-0 rounded-full z-0 blur-md opacity-60 ${isWarning ? 'bg-amber-500' : 'bg-emerald-400'}`}
            style={{ width: `${fillPercent}%` }}
            initial={{ width: 0 }}
            animate={{ width: `${fillPercent}%` }}
            transition={{ duration: 0.7, type: "spring", stiffness: 100, damping: 15 }}
          />

          {/* The Needle */}
          <motion.div
            className="absolute top-1/2 z-40"
            style={{ left: `${fillPercent}%` }}
            initial={{ left: 0 }}
            animate={{ left: `${fillPercent}%` }}
            transition={{ duration: 0.7, type: "spring", stiffness: 100, damping: 15 }}
          >
            <div className="relative -translate-x-1/2 -translate-y-1/2 flex flex-col items-center justify-center">
              {/* Needle Body (Polygon pointing down) */}
              <svg width="12" height="24" viewBox="0 0 12 24" className="absolute bottom-[2px] filter drop-shadow-md">
                <polygon points="6,24 0,0 12,0" fill="white" />
              </svg>
              {/* Pivot Dot */}
              <div className="w-4 h-4 bg-white rounded-full shadow-lg absolute -top-4 border-2 border-zinc-900" />
            </div>
          </motion.div>
        </div>

        {/* Labels below the bar */}
        <div className="flex items-center justify-between mt-2.5">
          <span className="text-[11px] font-semibold text-zinc-400 tracking-wide">0</span>
          <span className="text-[11px] font-semibold text-zinc-400 tracking-wide">1000</span>
        </div>
      </div>

      {/* Caption Bottom Right */}
      <div className="absolute bottom-0 right-0">
        <span className="text-[10px] uppercase font-bold tracking-widest text-zinc-500">
          OUT OF 1000 MBPS
        </span>
      </div>

    </div>
  );
}
