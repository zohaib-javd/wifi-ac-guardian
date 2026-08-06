'use client';

import React, { useState, useEffect } from 'react';
import Header from '@/components/Header';
import HeroCard from '@/components/HeroCard';
import MetricCards from '@/components/MetricCards';
import ConnectionCard from '@/components/ConnectionCard';
import ProtectionEngineCard from '@/components/ProtectionEngineCard';
import BottomToolbar from '@/components/BottomToolbar';
import SettingsModal from '@/components/SettingsModal';
import AboutModal from '@/components/AboutModal';

export default function Home() {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isAboutOpen, setIsAboutOpen] = useState(false);

  const [telemetry, setTelemetry] = useState({
    status: 'Active',
    ssid: 'lab5g',
    linkSpeed: 866.5,
    reconnectAttempts: 0,
    uploadSpeed: 866.5,
    downloadSpeed: 866.5,
  });

  // Polling IPC simulation / local backend bridge fetch
  useEffect(() => {
    const interval = setInterval(() => {
      // Small real-time jitter simulation for telemetry feedback
      setTelemetry((prev) => ({
        ...prev,
        linkSpeed: Math.min(1000, Math.max(780, prev.linkSpeed + (Math.random() * 4 - 2))),
      }));
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleReconnect = () => {
    alert("Triggering hardware radio reset on primary Wi-Fi interface...");
  };

  const handleToggleProtection = () => {
    setTelemetry((prev) => ({
      ...prev,
      status: prev.status === 'Active' ? 'Paused' : 'Active',
    }));
  };

  return (
    <div className="flex flex-col min-h-screen bg-[#0D0F10]">
      {/* Header */}
      <Header />

      {/* Main Content Area */}
      <main className="flex-1 max-w-[1200px] w-full mx-auto p-6 space-y-4">
        {/* 1. Hero Section */}
        <HeroCard
          statusText={telemetry.status === 'Active' ? 'Protected — High-Speed Wi-Fi Active' : 'Protection Paused'}
          ssid={telemetry.ssid}
          linkSpeed={Number(telemetry.linkSpeed.toFixed(1))}
        />

        {/* 2. Metric Cards Row */}
        <MetricCards
          status={telemetry.status}
          reconnectAttempts={telemetry.reconnectAttempts}
          uploadSpeed={Number(telemetry.uploadSpeed.toFixed(1))}
          downloadSpeed={Number(telemetry.downloadSpeed.toFixed(1))}
        />

        {/* 3. Middle Section: Connection Card & Protection Engine */}
        <div className="grid grid-cols-2 gap-4">
          <ConnectionCard currentSpeed={telemetry.linkSpeed} threshold={300} maxSpeed={1000} />
          <ProtectionEngineCard
            networkSsid={telemetry.ssid}
            onReconnect={handleReconnect}
            onToggleProtection={handleToggleProtection}
          />
        </div>
      </main>

      {/* Bottom Pinned Toolbar */}
      <BottomToolbar
        onOpenSettings={() => setIsSettingsOpen(true)}
        onOpenLogs={() => alert("Opening application log file...")}
        onOpenAbout={() => setIsAboutOpen(true)}
      />

      {/* Modals */}
      <SettingsModal isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />
      <AboutModal isOpen={isAboutOpen} onClose={() => setIsAboutOpen(false)} />
    </div>
  );
}
