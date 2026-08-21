'use client';

import React from 'react';
import { motion } from 'framer-motion';

interface ToggleProps {
  isOn: boolean;
  onToggle: () => void;
}

export default function Toggle({ isOn, onToggle }: ToggleProps) {
  return (
    <div
      className={`flex h-6 w-11 cursor-pointer items-center rounded-full p-1 transition-colors duration-300 ${
        isOn ? 'bg-emerald-500 shadow-[0_0_12px_rgba(16,185,129,0.4)]' : 'bg-zinc-700'
      }`}
      onClick={onToggle}
    >
      <motion.div
        className="h-4 w-4 rounded-full bg-white shadow-sm"
        layout
        initial={false}
        animate={{
          x: isOn ? 20 : 0,
        }}
        transition={{
          type: 'spring',
          stiffness: 700,
          damping: 30,
        }}
      />
    </div>
  );
}
