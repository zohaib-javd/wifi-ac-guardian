'use client';

import React from 'react';
import Image from 'next/image';
import { motion } from 'framer-motion';
import { CheckCircle2, Wifi } from 'lucide-react';

interface HeroCardProps {
  statusText?: string;
  ssid?: string;
  linkSpeed?: number;
}

export default function HeroCard({
  statusText = 'Protected — High-Speed Wi-Fi Active',
  ssid = 'lab5g',
  linkSpeed = 872.2,
}: HeroCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className="relative overflow-hidden rounded-2xl bg-[#16181A] border border-[#2A2F33] p-5 shadow-xl"
    >
      {/* Background Radial Glow */}
      <div className="absolute top-1/2 left-16 -translate-y-1/2 w-44 h-44 bg-[#22C55E]/15 rounded-full blur-3xl pointer-events-none" />

      <div className="relative z-10 flex items-center justify-between">
        {/* Left 3D Cyan Router Artwork */}
        <div className="relative w-28 h-28 flex-shrink-0 flex items-center justify-center">
          <Image
            src="/router.png"
            alt="Wi-Fi Router Artwork"
            width={112}
            height={112}
            className="object-contain drop-shadow-[0_10px_20px_rgba(34,197,94,0.25)]"
            priority
          />
        </div>

        {/* Right Text Content */}
        <div className="flex-1 ml-6 min-w-0">
          <div className="flex items-center space-x-2.5">
            <h2 className="text-xl font-bold text-[#F2F4F7] tracking-tight truncate">{statusText}</h2>
            <CheckCircle2 className="w-6 h-6 text-[#22C55E] flex-shrink-0" />
          </div>

          <div className="mt-1.5 flex items-center space-x-2 text-xs text-[#A1A7AE] flex-wrap">
            <span className="w-2 h-2 rounded-full bg-[#22C55E] animate-pulse flex-shrink-0" />
            <span className="font-semibold text-[#F2F4F7]">Active Protection</span>
            <span className="text-[#6B7280]">|</span>
            <span>Connected to <strong className="text-[#F2F4F7]">{ssid}</strong></span>
            <span className="text-[#6B7280]">|</span>
            <span>Link Speed: <strong className="text-[#22C55E]">{linkSpeed} Mbps</strong></span>
          </div>

          <p className="mt-1.5 text-[11px] text-[#6B7280]">
            Continuous link quality protection against router bit-rate downgrades.
          </p>
          <div className="mt-3 border-t border-[#2A2F33]" />
          <div className="mt-2.5 flex items-center space-x-2">
            <Wifi className="w-3.5 h-3.5 text-[#22C55E]/60" />
            <span className="text-[11px] text-[#22C55E]/60 font-medium">High-Speed Wi-Fi 5+ Protection Service</span>
          </div>
        </div>
      </div>

      {/* Bottom Ambient Glow Line */}
      <div className="absolute bottom-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-[#22C55E]/30 to-transparent" />
    </motion.div>
  );
}
