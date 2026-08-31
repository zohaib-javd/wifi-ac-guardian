import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Wifi, Settings, Activity, RefreshCw, ArrowUp, ArrowDown, Shield, Search, Power } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export default function App() {
  const [monitoringOn, setMonitoringOn] = useState(true);
  const [rawLinkSpeed, setRawLinkSpeed] = useState(867);
  const [displaySpeed, setDisplaySpeed] = useState(867);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isReconnecting, setIsReconnecting] = useState(false);

  const requestRef = useRef<number | null>(null);
  
  const status = monitoringOn ? "protected" : "paused";
  
  // Simulated jitter
  useEffect(() => {
    if (!monitoringOn) return;
    const interval = setInterval(() => {
      // randomly jump down simulating drop, or jitter
      if (Math.random() > 0.8) {
        setRawLinkSpeed(prev => Math.max(100, prev - Math.random() * 500)); // Simulating a drop
      } else {
        setRawLinkSpeed(prev => {
          const target = 867;
          return Math.min(1000, Math.max(0, prev + (target - prev) * 0.1 + (Math.random() * 10 - 5)));
        });
      }
    }, 1500);
    return () => clearInterval(interval);
  }, [monitoringOn]);

  // Exponential smoothing via rAF
  useEffect(() => {
    const animate = () => {
      // k ≈ 0.18–0.25
      setDisplaySpeed(prev => {
        const k = 0.2;
        const diff = rawLinkSpeed - prev;
        return prev + diff * k;
      });
      requestRef.current = requestAnimationFrame(animate);
    };
    requestRef.current = requestAnimationFrame(animate);
    return () => {
      if (requestRef.current !== null) cancelAnimationFrame(requestRef.current);
    };
  }, [rawLinkSpeed]);

  const percentage = Math.min(100, Math.max(0, (displaySpeed / 1000) * 100));
  const isProtectedThreshold = displaySpeed >= 300;

  // Calculate wobble if very close to target
  const distanceToTarget = Math.abs(rawLinkSpeed - displaySpeed);
  const isSettling = distanceToTarget > 0.1 && distanceToTarget < 20;

  return (
    <div className="flex justify-center items-center h-screen w-full bg-black sm:bg-zinc-950 overflow-hidden">
      {/* Phone container */}
      <div className="relative flex flex-col w-full h-[100dvh] max-w-[430px] max-h-[932px] sm:h-[932px] sm:w-[430px] sm:border sm:border-zinc-800 sm:rounded-[3rem] bg-zinc-950 overflow-hidden text-white font-sans shadow-2xl">
        
        <div className="flex-1 flex flex-col min-h-0 p-4 gap-4 overflow-hidden">
          {/* Header */}
          <header className="flex flex-row items-center justify-between h-[56px] shrink-0">
             <div className="flex items-center gap-2">
                <Wifi className="w-6 h-6 text-emerald-400" />
                <h1 className="text-[22px] font-bold text-white tracking-tight">WiFi AC Guardian</h1>
             </div>
             <div className="relative">
               <button onClick={() => setIsSettingsOpen(!isSettingsOpen)} className="p-2 hover:bg-zinc-800 rounded-full transition-colors cursor-pointer">
                 <Settings className="w-6 h-6 text-zinc-400" />
               </button>
               <AnimatePresence>
                 {isSettingsOpen && (
                   <motion.div 
                     initial={{ opacity: 0, y: -10 }}
                     animate={{ opacity: 1, y: 0 }}
                     exit={{ opacity: 0, y: -10 }}
                     transition={{ duration: 0.2 }}
                     className="absolute right-0 top-full mt-2 w-48 bg-zinc-900 border border-zinc-800 rounded-xl shadow-xl overflow-hidden z-50"
                   >
                     <button className="w-full text-left px-4 py-3 hover:bg-zinc-800 text-sm font-medium border-b border-zinc-800 cursor-pointer">Settings</button>
                     <button className="w-full text-left px-4 py-3 hover:bg-zinc-800 text-sm font-medium cursor-pointer">About</button>
                   </motion.div>
                 )}
               </AnimatePresence>
             </div>
          </header>

          {/* Hero Banner */}
          <div className={cn("flex flex-row items-center p-4 h-[95px] shrink-0 rounded-2xl backdrop-blur-xl border border-zinc-800/80 transition-colors duration-500", status === 'protected' ? "bg-zinc-900/80" : "bg-zinc-900/80")}>
            <div className="w-[30%] h-full flex items-center justify-center shrink-0 pr-4">
               {/* Router Icon (simplified vector) */}
               <div className="relative w-16 h-12 flex flex-col items-center justify-end">
                  <div className="absolute top-0 w-8 h-8 rounded-full border-t-2 border-emerald-400 opacity-60"></div>
                  <div className="absolute top-2 w-12 h-12 rounded-full border-t-2 border-emerald-500 opacity-30"></div>
                  <div className="w-1 h-6 bg-zinc-500 absolute left-2 bottom-4"></div>
                  <div className="w-1 h-6 bg-zinc-500 absolute right-2 bottom-4"></div>
                  <div className="w-full h-4 bg-zinc-800 border border-zinc-600 rounded-sm relative z-10 flex items-center px-1 gap-0.5">
                     <div className="w-1 h-1 rounded-full bg-emerald-400"></div>
                     <div className="w-1 h-1 rounded-full bg-emerald-400"></div>
                     <div className="w-1 h-1 rounded-full bg-emerald-400"></div>
                     <div className="w-1 h-1 rounded-full bg-emerald-400"></div>
                  </div>
               </div>
            </div>
            <div className="flex-1 min-w-0 flex flex-col justify-center">
               <h2 className={cn("text-[17px] font-semibold leading-tight", status === 'protected' ? "text-emerald-400" : "text-amber-400")}>
                 {status === 'protected' ? "Protected — High-Speed Wi-Fi Active" : "Protection Paused"}
               </h2>
               <p className="text-xs text-zinc-400 mt-1 leading-snug pr-2">Continuous link quality protection against router bit-rate downgrades.</p>
            </div>
          </div>

          {/* Connection Quality Bar Card */}
          <div className="flex flex-col p-5 h-[160px] shrink-0 rounded-2xl bg-zinc-900/80 backdrop-blur-xl border border-zinc-800/80 mt-2">
            <div className="flex justify-between items-center mb-6">
              <span className="text-[10px] font-bold text-white tracking-wider">CONNECTION QUALITY</span>
              <span className="text-[11px] text-zinc-400 tracking-wide">300 Mbps protected threshold</span>
            </div>
            
            <div className="relative w-full h-8 mt-4">
              {/* Bar track */}
              <div className="absolute inset-0 rounded-full flex overflow-hidden">
                <div className="h-full bg-rose-500 w-[30%]" />
                <div className="h-full bg-amber-500 w-[7%]" />
                <div className="h-full bg-emerald-500 flex-1 relative overflow-hidden">
                   <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent w-[200%] animate-shine" />
                </div>
              </div>
              
              {/* 300 Mbps marker line */}
              <div className="absolute top-0 bottom-0 left-[30%] w-0.5 bg-white/70 z-10" />
              
              {/* Labels */}
              <div className="absolute -top-6 left-0 text-[11px] font-medium text-zinc-400">0 Mbps</div>
              <div className="absolute -top-6 left-[30%] -translate-x-1/2 text-[11px] font-bold text-amber-500">300 Mbps</div>
              <div className="absolute -top-6 right-0 text-[11px] font-medium text-zinc-400">1000 Mbps</div>

              {/* Liquid Marker */}
              <motion.div 
                className="absolute top-[-4px] bottom-[-4px] w-[2px] z-20 flex flex-col items-center"
                animate={{ left: `${percentage}%` }}
                transition={{ type: "spring", stiffness: 45, damping: 16, mass: 1.2 }}
              >
                 {/* The vertical pill and dot */}
                 <div className="w-[3px] h-full bg-white rounded-full shadow-[0_0_10px_rgba(255,255,255,0.8)] relative">
                    <motion.div 
                      className={cn("absolute top-1/2 -translate-y-1/2 -left-1 w-2.5 h-2.5 rounded-full shadow-[0_0_8px_rgba(255,255,255,0.9)] border-2 border-zinc-900", isProtectedThreshold ? "bg-white" : "bg-amber-400")}
                      animate={isSettling ? { y: ["-50%", "-80%", "-40%", "-50%"] } : { y: "-50%" }}
                      transition={{ duration: 0.5, ease: "easeOut" }}
                    />
                 </div>
                 {/* Follower value label */}
                 <div className="absolute top-full mt-2 text-[14px] font-bold text-white whitespace-nowrap shadow-black drop-shadow-md">
                   {displaySpeed.toFixed(0)} Mbps
                 </div>
              </motion.div>
            </div>
          </div>

          {/* Connection Metrics */}
          <div className="grid grid-cols-2 gap-2 h-[180px] shrink-0 mt-2">
             <MetricCard icon={<Activity className="w-5 h-5 text-emerald-400" />} label="STATUS" value={<span className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />Active · 1 hr 12 m</span>} />
             <MetricCard icon={<RefreshCw className="w-5 h-5 text-emerald-400" />} label="RECONNECTS" value="0 · Last 24h" />
             <MetricCard icon={<ArrowUp className="w-5 h-5 text-emerald-400" />} label="UPLOAD" value="866.5 Mbps" sub="5 GHz / Ch 48" />
             <MetricCard icon={<ArrowDown className="w-5 h-5 text-emerald-400" />} label="DOWNLOAD" value="866.5 Mbps" sub="TX 866 Mbps" />
          </div>

          {/* Protection Engine Card */}
          <div className="flex flex-col p-4 h-[190px] shrink-0 rounded-2xl bg-zinc-900/80 backdrop-blur-xl border border-zinc-800/80 mt-2">
             <div className="flex items-center gap-2 mb-4">
                <Shield className="w-4 h-4 text-zinc-400" />
                <span className="text-[10px] font-bold text-zinc-400 tracking-wider">PROTECTION ENGINE</span>
             </div>

             <div className="flex items-center justify-between pb-3 border-b border-zinc-800/80">
                <div className="flex items-center gap-3">
                   <div className="w-8 h-8 rounded-full bg-zinc-800/50 flex items-center justify-center">
                     <Search className="w-4 h-4 text-zinc-300" />
                   </div>
                   <span className="text-[15px] font-medium text-white">Connection Monitoring</span>
                </div>
                {/* iOS Toggle */}
                <button 
                  onClick={() => setMonitoringOn(!monitoringOn)}
                  className={cn("w-14 h-8 rounded-full relative transition-colors duration-300 cursor-pointer", monitoringOn ? "bg-emerald-500" : "bg-zinc-700")}
                >
                   <motion.div 
                     className="w-7 h-7 bg-white rounded-full absolute top-0.5 shadow-sm"
                     animate={{ left: monitoringOn ? 26 : 2 }}
                     transition={{ type: "spring", stiffness: 500, damping: 30 }}
                   />
                </button>
             </div>

             <div className="flex items-center gap-3 mt-3 mb-4">
                <Wifi className="w-5 h-5 text-zinc-400" />
                <span className="text-sm text-zinc-400">Connected to <span className="text-zinc-200 font-medium px-2 py-0.5 rounded bg-zinc-800/80">lab5g</span> (SSID)</span>
             </div>

             <div className="flex gap-2">
                <motion.button 
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.97 }}
                  onClick={() => {
                     setIsReconnecting(true);
                     setTimeout(() => setIsReconnecting(false), 1500);
                  }}
                  className="flex-1 min-w-0 flex items-center justify-center gap-2 py-3 rounded-xl font-semibold border border-emerald-500/30 bg-emerald-500/10 text-emerald-400 cursor-pointer"
                >
                   <RefreshCw className={cn("w-4 h-4", isReconnecting && "animate-spin")} />
                   Reconnect now
                </motion.button>
                <motion.button 
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.97 }}
                  onClick={() => setMonitoringOn(false)}
                  className="flex-1 min-w-0 flex items-center justify-center gap-2 py-3 rounded-xl font-semibold border border-rose-500/30 bg-rose-500/10 text-rose-400 cursor-pointer"
                >
                   <Power className="w-4 h-4" />
                   Stop protection
                </motion.button>
             </div>

          </div>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ icon, label, value, sub }: { icon: React.ReactNode, label: string, value: React.ReactNode, sub?: string }) {
  return (
    <div className="flex flex-col p-4 rounded-2xl bg-zinc-900/80 backdrop-blur-xl border border-zinc-800/80 min-w-0">
      <div className="flex items-center gap-3 mb-3">
         <div className="w-9 h-9 rounded-full bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
           {icon}
         </div>
         <span className="text-[10px] font-bold text-zinc-400 tracking-wider uppercase">{label}</span>
      </div>
      <div className="text-[15px] font-semibold text-white whitespace-nowrap overflow-hidden text-ellipsis">{value}</div>
      {sub && <div className="text-[11px] text-zinc-500 mt-1 whitespace-nowrap overflow-hidden text-ellipsis">{sub}</div>}
    </div>
  );
}
