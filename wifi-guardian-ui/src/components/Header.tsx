'use client';

import React from 'react';
import { Wifi } from 'lucide-react';

export default function Header() {
  return (
    <header className="flex items-center justify-between px-6 py-4 border-b border-[#2A2F33] bg-[#0D0F10]">
      <div className="flex items-center space-x-3">
        <div className="p-1.5 rounded-lg bg-[#1E2124] border border-[#2A2F33] text-[#22C55E]">
          <Wifi className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-lg font-bold text-[#F2F4F7] tracking-tight">WiFi AC Guardian</h1>
          <p className="text-xs text-[#A1A7AE]">High-Speed Wi-Fi 5+ Protection Service</p>
        </div>
      </div>
      <div className="flex items-center space-x-2">
        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-[#22C55E]/10 text-[#22C55E] border border-[#22C55E]/20">
          ● v1.1.0 Commercial Edition
        </span>
      </div>
    </header>
  );
}
