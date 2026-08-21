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
    linkSpeed: 872.2,
    reconnectAttempts: 0,
    uploadSpeed: 866.5,
    downloadSpeed: 866.5,
  });

  // Telemetry update loop
  useEffect(() => {
    const interval = setInterval(() => {
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

  const handleOpenLogs = () => {
    alert("Opening application log file...");
  };

  return (
    <div className="flex flex-col min-h-screen bg-[#0D0F10]">
      {/* Header */}
      <Header />

      {/* Main Compact Content Area */}
      <main className="flex-1 max-w-[920px] w-full mx-auto p-5 space-y-4">
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
        onOpenLogs={handleOpenLogs}
        onOpenAbout={() => setIsAboutOpen(true)}
      />

      {/* Modals */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        onOpenLogs={handleOpenLogs}
      />
      <AboutModal isOpen={isAboutOpen} onClose={() => setIsAboutOpen(false)} />
    </div>
  );
}
