'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { ShieldCheck, RotateCcw, ArrowUpRight, ArrowDownRight } from 'lucide-react';

interface MetricCardsProps {
  status?: string;
  uptime?: string;
  reconnectAttempts?: number;
  uploadSpeed?: number;
  downloadSpeed?: number;
}

export default function MetricCards({
  status = 'Active',
  uptime = '1 hr 12 m uptime',
  reconnectAttempts = 0,
  uploadSpeed = 866.5,
  downloadSpeed = 866.5,
}: MetricCardsProps) {
  const cards = [
    {
      title: 'Status',
      value: status,
      subtext: uptime,
      icon: ShieldCheck,
      color: 'text-[#22C55E]',
    },
    {
      title: 'Reconnect Attempts',
      value: `${reconnectAttempts}`,
      subtext: 'Last 24 hours',
      icon: RotateCcw,
      color: 'text-[#F2F4F7]',
    },
    {
      title: 'Upload Link Speed',
      value: `${uploadSpeed} Mbps`,
      subtext: '5.0 GHz / Ch 48',
      icon: ArrowUpRight,
      color: 'text-[#F2F4F7]',
    },
    {
      title: 'Download Link Speed',
      value: `${downloadSpeed} Mbps`,
      subtext: 'TX Rate: 866 Mbps',
      icon: ArrowDownRight,
      color: 'text-[#F2F4F7]',
    },
  ];

  return (
    <div className="grid grid-cols-4 gap-3 my-3">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <motion.div
            key={card.title}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2, delay: idx * 0.05 }}
            className="rounded-xl bg-[#16181A] border border-[#2A2F33] p-3.5 flex flex-col justify-between min-h-[92px] hover:border-[#22C55E]/40 transition-colors overflow-hidden"
          >
            <div className="flex items-center space-x-2 min-w-0">
              <div className="p-1 rounded-md bg-[#1E2124] text-[#22C55E] flex-shrink-0">
                <Icon className="w-3.5 h-3.5" />
              </div>
              <span className="text-[11px] font-bold text-[#A1A7AE] uppercase tracking-wider truncate">
                {card.title}
              </span>
            </div>
            <div className="flex items-baseline justify-between mt-2 min-w-0">
              <span className={`text-sm font-extrabold ${card.color} truncate mr-1`}>{card.value}</span>
              <span className="text-[10px] text-[#6B7280] flex-shrink-0">{card.subtext}</span>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}
