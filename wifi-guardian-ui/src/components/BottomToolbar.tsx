'use client';

import React from 'react';
import { Settings, FileText, Info } from 'lucide-react';

interface BottomToolbarProps {
  onOpenSettings?: () => void;
  onOpenLogs?: () => void;
  onOpenAbout?: () => void;
}

export default function BottomToolbar({
  onOpenSettings,
  onOpenLogs,
  onOpenAbout,
}: BottomToolbarProps) {
  return (
    <div className="w-full flex justify-center py-4 border-t border-[#2A2F33] bg-[#0D0F10]">
      <div className="flex items-center space-x-3 p-1.5 rounded-full bg-[#16181A] border border-[#2A2F33] shadow-lg">
        <button
          onClick={onOpenSettings}
          className="flex items-center space-x-2 px-5 py-2 rounded-full bg-[#1E2124] hover:bg-[#252A2F] text-[#F2F4F7] text-xs font-semibold border border-[#2A2F33] transition-all hover:border-[#22C55E]/50"
        >
          <Settings className="w-4 h-4 text-[#22C55E]" />
          <span>Settings</span>
        </button>

        <button
          onClick={onOpenLogs}
          className="flex items-center space-x-2 px-5 py-2 rounded-full bg-[#1E2124] hover:bg-[#252A2F] text-[#F2F4F7] text-xs font-semibold border border-[#2A2F33] transition-all hover:border-[#22C55E]/50"
        >
          <FileText className="w-4 h-4 text-[#A1A7AE]" />
          <span>View Logs</span>
        </button>

        <button
          onClick={onOpenAbout}
          className="flex items-center space-x-2 px-5 py-2 rounded-full bg-[#1E2124] hover:bg-[#252A2F] text-[#F2F4F7] text-xs font-semibold border border-[#2A2F33] transition-all hover:border-[#22C55E]/50"
        >
          <Info className="w-4 h-4 text-[#3B82F6]" />
          <span>About</span>
        </button>
      </div>
    </div>
  );
}
