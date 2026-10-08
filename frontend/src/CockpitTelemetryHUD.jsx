import React, { useState, useEffect } from 'react';
import { Activity, Gauge, Zap, BatteryCharging, Radio, Cpu, AlertTriangle, ShieldCheck } from 'lucide-react';

export default function CockpitTelemetryHUD() {
  const [speed, setSpeed] = useState(68);
  const [rpm, setRpm] = useState(3400);
  const [voltage, setVoltage] = useState(384.2);
  const [temp, setTemp] = useState(89);
  const [packetsPerSec, setPacketsPerSec] = useState(1420);

  // Subtle real-time telemetry fluctuation animation
  useEffect(() => {
    const interval = setInterval(() => {
      setSpeed(prev => Math.min(145, Math.max(55, Math.round(prev + (Math.random() * 4 - 2)))));
      setRpm(prev => Math.min(6500, Math.max(2200, Math.round(prev + (Math.random() * 120 - 60)))));
      setVoltage(prev => Number((384.0 + Math.random() * 0.8).toFixed(1)));
      setTemp(prev => Math.min(98, Math.max(86, Math.round(prev + (Math.random() * 0.6 - 0.3)))));
      setPacketsPerSec(prev => Math.round(1400 + Math.random() * 80));
    }, 800);
    return () => clearInterval(interval);
  }, []);

  const speedAngle = (speed / 160) * 180;
  const rpmAngle = (rpm / 8000) * 180;

  return (
    <div className="cockpit-telemetry-hud-root">
      <div className="telemetry-hud-glass-panel">
        {/* Top Status Bar */}
        <div className="hud-panel-top">
          <div className="hud-sys-status">
            <span className="live-radar-dot" />
            <span className="hud-sys-label">CAN-BUS TELEMETRY LIVE</span>
            <span className="hud-sys-val">// ISO 11898-2 HIGH SPEED</span>
          </div>
          <div className="hud-node-pill">
            <Cpu size={12} color="var(--accent-primary)" />
            <span>OBD-II STREAM: {packetsPerSec} PKT/S</span>
          </div>
        </div>

        {/* Central Twin Gauge Cluster */}
        <div className="twin-gauges-cluster">
          {/* Speedometer Gauge */}
          <div className="circular-gauge-card">
            <svg className="gauge-svg" viewBox="0 0 200 120">
              <path 
                d="M 20 100 A 80 80 0 0 1 180 100" 
                fill="none" 
                stroke="rgba(255, 255, 255, 0.08)" 
                strokeWidth="12" 
                strokeLinecap="round" 
              />
              <path 
                d="M 20 100 A 80 80 0 0 1 180 100" 
                fill="none" 
                stroke="var(--accent-primary)" 
                strokeWidth="12" 
                strokeLinecap="round" 
                strokeDasharray="251.2"
                strokeDashoffset={251.2 - (speed / 160) * 251.2}
                style={{ transition: 'stroke-dashoffset 0.5s ease-out' }}
              />
            </svg>
            <div className="gauge-value-overlay">
              <span className="huge-speed-number">{speed}</span>
              <span className="gauge-unit">MPH</span>
            </div>
            <div className="gauge-footer-label">
              <Gauge size={13} color="var(--accent-primary)" />
              <span>VEHICLE GROUND SPEED</span>
            </div>
          </div>

          {/* Tachometer RPM Gauge */}
          <div className="circular-gauge-card">
            <svg className="gauge-svg" viewBox="0 0 200 120">
              <path 
                d="M 20 100 A 80 80 0 0 1 180 100" 
                fill="none" 
                stroke="rgba(255, 255, 255, 0.08)" 
                strokeWidth="12" 
                strokeLinecap="round" 
              />
              <path 
                d="M 20 100 A 80 80 0 0 1 180 100" 
                fill="none" 
                stroke={rpm > 5500 ? '#ef4444' : '#00f0ff'} 
                strokeWidth="12" 
                strokeLinecap="round" 
                strokeDasharray="251.2"
                strokeDashoffset={251.2 - (rpm / 8000) * 251.2}
                style={{ transition: 'stroke-dashoffset 0.5s ease-out' }}
              />
            </svg>
            <div className="gauge-value-overlay">
              <span className="huge-speed-number" style={{ color: rpm > 5500 ? '#ef4444' : '#00f0ff' }}>
                {(rpm / 1000).toFixed(1)}k
              </span>
              <span className="gauge-unit">RPM</span>
            </div>
            <div className="gauge-footer-label">
              <Activity size={13} color="#00f0ff" />
              <span>MOTOR / ENGINE SPEED</span>
            </div>
          </div>
        </div>

        {/* Live Subsystems Telemetry Grid */}
        <div className="hud-subsystems-grid">
          <div className="subsystem-telemetry-tile">
            <div className="subsystem-header">
              <Zap size={14} color="var(--accent-primary)" />
              <span>HV BUS VOLTAGE</span>
            </div>
            <div className="subsystem-val">{voltage} V</div>
            <div className="subsystem-bar">
              <div className="bar-fill" style={{ width: '92%', backgroundColor: 'var(--accent-primary)' }} />
            </div>
          </div>

          <div className="subsystem-telemetry-tile">
            <div className="subsystem-header">
              <BatteryCharging size={14} color="#10b981" />
              <span>BATTERY SOC</span>
            </div>
            <div className="subsystem-val">94.8%</div>
            <div className="subsystem-bar">
              <div className="bar-fill" style={{ width: '94.8%', backgroundColor: '#10b981' }} />
            </div>
          </div>

          <div className="subsystem-telemetry-tile">
            <div className="subsystem-header">
              <Radio size={14} color="#38bdf8" />
              <span>COOLANT TEMP</span>
            </div>
            <div className="subsystem-val">{temp}°C</div>
            <div className="subsystem-bar">
              <div className="bar-fill" style={{ width: '65%', backgroundColor: '#38bdf8' }} />
            </div>
          </div>

          <div className="subsystem-telemetry-tile">
            <div className="subsystem-header">
              <ShieldCheck size={14} color="#a855f7" />
              <span>HEALTH INDEX</span>
            </div>
            <div className="subsystem-val">99.2%</div>
            <div className="subsystem-bar">
              <div className="bar-fill" style={{ width: '99.2%', backgroundColor: '#a855f7' }} />
            </div>
          </div>
        </div>

        {/* Animated Oscilloscope Signal Stream */}
        <div className="hud-oscilloscope-container">
          <div className="oscilloscope-header">
            <span>O2 SENSOR & FUEL TRIM OSCILLOSCOPE WAVEFORM</span>
            <span className="osc-badge">SAMPLING: 10kHz</span>
          </div>
          <div className="waveform-box">
            <svg className="waveform-svg" viewBox="0 0 600 50" preserveAspectRatio="none">
              <path 
                className="wave-line"
                d="M 0 25 Q 30 5, 60 25 T 120 25 T 180 45 T 240 25 T 300 10 T 360 25 T 420 40 T 480 25 T 540 15 T 600 25" 
                fill="none" 
                stroke="var(--accent-primary)" 
                strokeWidth="2.5" 
              />
            </svg>
            <div className="oscilloscope-scanline" />
          </div>
        </div>
      </div>
    </div>
  );
}
