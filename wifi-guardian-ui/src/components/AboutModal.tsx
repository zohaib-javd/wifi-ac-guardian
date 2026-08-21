'use client';

import React from 'react';
import Image from 'next/image';
import { X, ShieldCheck } from 'lucide-react';

interface AboutModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function AboutModal({ isOpen, onClose }: AboutModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-[390px] bg-[#16181A] border border-[#2A2F33] rounded-2xl p-5 shadow-2xl space-y-4">
        <div className="flex items-center justify-between border-b border-[#2A2F33] pb-3">
          <div className="flex items-center space-x-3">
            <Image src="/router.png" alt="Router Icon" width={36} height={36} className="object-contain" />
            <div>
              <h3 className="text-base font-bold text-[#F2F4F7]">WiFi AC Guardian</h3>
              <p className="text-xs text-[#22C55E]">v1.1.0 Commercial Edition</p>
            </div>
          </div>
          <button onClick={onClose} className="text-[#6B7280] hover:text-[#F2F4F7]">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-4 rounded-xl bg-[#1E2124] border border-[#2A2F33] text-xs text-[#A1A7AE] space-y-2">
          <p className="font-bold text-[#F2F4F7]">Engineered by Zohaib Javed aka Zeejay</p>
          <p>
            Router firmware and band-steering quietly downgrade your Wi-Fi to 802.11n, even on hardware that supports Wi-Fi 5+.
          </p>
          <p>
            WiFi AC Guardian watches your link in the background and forces a clean radio reset the moment it drops below 300 Mbps, restoring full-speed AC/AX/BE performance without you touching a setting.
          </p>
          <p>Windows 11 and Ubuntu 26.04 LTS.</p>
          <p>
            More at:{' '}
            <a
              href="https://zeejaylab.store"
              target="_blank"
              rel="noreferrer"
              className="font-semibold text-[#34d399] underline underline-offset-2 hover:text-[#6ee7b7]"
            >
              zeejaylab.store
            </a>
          </p>
          <p>
            Email:{' '}
            <a
              href="mailto:zeejay.lab@gmail.com"
              className="font-semibold text-[#34d399] underline underline-offset-2 hover:text-[#6ee7b7]"
            >
              zeejay.lab@gmail.com
            </a>
          </p>
        </div>

        <button
          onClick={onClose}
          className="w-full py-2 bg-[#1E2124] hover:bg-[#252A2F] text-[#F2F4F7] font-bold rounded-lg text-xs border border-[#2A2F33] transition-colors"
        >
          Close
        </button>
      </div>
    </div>
  );
}
