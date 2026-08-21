'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Wifi, Menu, Settings, Info } from 'lucide-react';

interface HeaderProps {
  onOpenSettings?: () => void;
  onOpenAbout?: () => void;
}

export default function Header({ onOpenSettings, onOpenAbout }: HeaderProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="flex items-center justify-between px-6 py-4 border-b border-[#2A2F33] bg-[#0D0F10] relative">
      <div className="flex items-center space-x-3">
        <div className="p-1.5 rounded-lg bg-[#1E2124] border border-[#2A2F33] text-[#22C55E]">
          <Wifi className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-lg font-bold text-[#F2F4F7] tracking-tight">WiFi AC Guardian</h1>
        </div>
      </div>
      <div className="relative" ref={menuRef}>
        <button
          onClick={() => setMenuOpen(!menuOpen)}
          className="p-2 text-[#A1A7AE] hover:text-[#F2F4F7] hover:bg-[#1E2124] rounded-lg transition-colors"
        >
          <Menu className="w-5 h-5" />
        </button>
        {menuOpen && (
          <div className="absolute right-0 mt-2 w-48 bg-[#16181A] border border-[#2A2F33] rounded-xl shadow-xl z-50 overflow-hidden">
            <button
              onClick={() => { setMenuOpen(false); onOpenSettings?.(); }}
              className="w-full flex items-center space-x-3 px-4 py-3 text-sm text-[#F2F4F7] hover:bg-[#1E2124] transition-colors"
            >
              <Settings className="w-4 h-4 text-[#A1A7AE]" />
              <span>Settings</span>
            </button>
            <button
              onClick={() => { setMenuOpen(false); onOpenAbout?.(); }}
              className="w-full flex items-center space-x-3 px-4 py-3 text-sm text-[#F2F4F7] hover:bg-[#1E2124] transition-colors"
            >
              <Info className="w-4 h-4 text-[#A1A7AE]" />
              <span>About</span>
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
