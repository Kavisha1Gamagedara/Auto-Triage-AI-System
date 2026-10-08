import React, { useRef, useEffect, useState, useCallback } from 'react';
import * as THREE from 'three';
import { 
  Zap, 
  Volume2, 
  VolumeX 
} from 'lucide-react';

import heroHypercarBg from './assets/hero_hypercar_bg.png';

const BEAM_COLORS = [
  { name: 'Xenon Ice (6500K)', hex: '#E0F2FE', threeColor: 0xe0f2fe, flareColor: 'rgba(224, 242, 254, 0.95)' },
  { name: 'Hyper Amber (3000K)', hex: '#FF5E14', threeColor: 0xff5e14, flareColor: 'rgba(255, 94, 20, 0.95)' },
  { name: 'Cyber Cyan (8000K)', hex: '#00F0FF', threeColor: 0x00f0ff, flareColor: 'rgba(0, 240, 255, 0.95)' },
  { name: 'Laser Crimson', hex: '#FF1E56', threeColor: 0xff1e56, flareColor: 'rgba(255, 30, 86, 0.95)' }
];

const FLICKER_MODES = [
  { id: 'ignition', label: 'Xenon Arc Ignition' },
  { id: 'breathing', label: 'DRL Pulse Breathing' },
  { id: 'strobe', label: 'Diagnostic Fault Strobe' },
  { id: 'steady', label: 'Steady High-Beam' }
];

export default function HypercarHeadlightCanvas({ 
  onSelectVehicle, 
  onLaunchTriage,
  onSwitchToWorkflow,
  selectedVehicle = 'Universal Multi-Make' 
}) {
  const containerRef = useRef(null);
  const canvasRef = useRef(null);
  const [beamColor, setBeamColor] = useState(BEAM_COLORS[0]);
  const [flickerMode, setFlickerMode] = useState('ignition');
  const [lightIntensity] = useState(1.0);
  const [isIgniting, setIsIgniting] = useState(false);
  const [soundEnabled, setSoundEnabled] = useState(false);
  const [currentFlickerAlpha, setCurrentFlickerAlpha] = useState(1.0);

  // Audio synthesizer for realistic automotive Xenon ballast relay clicks
  const playIgnitionSound = useCallback(() => {
    if (!soundEnabled) return;
    try {
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      
      const osc1 = audioCtx.createOscillator();
      const gain1 = audioCtx.createGain();
      osc1.type = 'triangle';
      osc1.frequency.setValueAtTime(800, audioCtx.currentTime);
      osc1.frequency.exponentialRampToValueAtTime(120, audioCtx.currentTime + 0.04);
      gain1.gain.setValueAtTime(0.4, audioCtx.currentTime);
      gain1.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.04);
      osc1.connect(gain1);
      gain1.connect(audioCtx.destination);
      osc1.start();
      osc1.stop(audioCtx.currentTime + 0.05);

      setTimeout(() => {
        const osc2 = audioCtx.createOscillator();
        const gain2 = audioCtx.createGain();
        osc2.type = 'sawtooth';
        osc2.frequency.setValueAtTime(140, audioCtx.currentTime);
        gain2.gain.setValueAtTime(0.25, audioCtx.currentTime);
        gain2.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.35);
        osc2.connect(gain2);
        gain2.connect(audioCtx.destination);
        osc2.start();
        osc2.stop(audioCtx.currentTime + 0.4);
      }, 120);
    } catch {
      // AudioContext fallback
    }
  }, [soundEnabled]);

  // Three.js Volumetric Light Beams & Particle Dust
  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    let width = container.clientWidth || window.innerWidth;
    let height = container.clientHeight || 720;

    const scene = new THREE.Scene();
    const camera = new THREE.OrthographicCamera(-width / 2, width / 2, height / 2, -height / 2, 0.1, 1000);
    camera.position.z = 10;

    const renderer = new THREE.WebGLRenderer({
      canvas,
      alpha: true,
      antialias: true,
      powerPreference: 'high-performance'
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    const createBeamTexture = () => {
      const texCanvas = document.createElement('canvas');
      texCanvas.width = 128;
      texCanvas.height = 256;
      const ctx = texCanvas.getContext('2d');

      const vGrad = ctx.createLinearGradient(0, 0, 0, 256);
      vGrad.addColorStop(0, 'rgba(255, 255, 255, 0.95)');
      vGrad.addColorStop(0.12, 'rgba(255, 255, 255, 0.7)');
      vGrad.addColorStop(0.4, 'rgba(255, 255, 255, 0.3)');
      vGrad.addColorStop(0.8, 'rgba(255, 255, 255, 0.08)');
      vGrad.addColorStop(1.0, 'rgba(255, 255, 255, 0.0)');
      ctx.fillStyle = vGrad;
      ctx.fillRect(0, 0, 128, 256);

      ctx.globalCompositeOperation = 'destination-in';
      const hGrad = ctx.createLinearGradient(0, 0, 128, 0);
      hGrad.addColorStop(0, 'rgba(0, 0, 0, 0.0)');
      hGrad.addColorStop(0.25, 'rgba(0, 0, 0, 0.85)');
      hGrad.addColorStop(0.5, 'rgba(0, 0, 0, 1.0)');
      hGrad.addColorStop(0.75, 'rgba(0, 0, 0, 0.85)');
      hGrad.addColorStop(1.0, 'rgba(0, 0, 0, 0.0)');
      ctx.fillStyle = hGrad;
      ctx.fillRect(0, 0, 128, 256);

      const texture = new THREE.CanvasTexture(texCanvas);
      texture.wrapS = THREE.ClampToEdgeWrapping;
      texture.wrapT = THREE.ClampToEdgeWrapping;
      return texture;
    };

    const beamTexture = createBeamTexture();

    const beamMaterial = new THREE.MeshBasicMaterial({
      map: beamTexture,
      color: beamColor.threeColor,
      transparent: true,
      opacity: 0.4,
      blending: THREE.AdditiveBlending,
      side: THREE.DoubleSide,
      depthWrite: false
    });

    const createBeamGeometry = (isLeft) => {
      const geo = new THREE.BufferGeometry();
      const topWidth = 16;
      const bottomWidth = 260;
      const length = 340;
      const angleOffset = isLeft ? -75 : 75;

      const vertices = new Float32Array([
        -topWidth / 2, 0, 0,
         topWidth / 2, 0, 0,
        angleOffset - bottomWidth / 2, -length, 0,
        angleOffset + bottomWidth / 2, -length, 0
      ]);

      const uvs = new Float32Array([
        0, 0,
        1, 0,
        0, 1,
        1, 1
      ]);

      const indices = [0, 2, 1, 1, 2, 3];
      geo.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
      geo.setAttribute('uv', new THREE.BufferAttribute(uvs, 2));
      geo.setIndex(indices);
      return geo;
    };

    const leftBeamGeo = createBeamGeometry(true);
    const rightBeamGeo = createBeamGeometry(false);

    const leftBeam = new THREE.Mesh(leftBeamGeo, beamMaterial);
    const rightBeam = new THREE.Mesh(rightBeamGeo, beamMaterial);

    const updateBeamPositions = () => {
      const lx = -width * (0.5 - 0.318);
      const rx = width * (0.689 - 0.5);
      const ly = height * (0.5 - 0.642);
      const ry = height * (0.5 - 0.645);

      leftBeam.position.set(lx, ly, 0);
      rightBeam.position.set(rx, ry, 0);
    };

    updateBeamPositions();
    scene.add(leftBeam);
    scene.add(rightBeam);

    const particleCount = 75;
    const particleGeo = new THREE.BufferGeometry();
    const posArray = new Float32Array(particleCount * 3);

    for (let i = 0; i < particleCount * 3; i += 3) {
      posArray[i] = (Math.random() - 0.5) * (width * 0.7);
      posArray[i + 1] = (Math.random() - 0.5) * (height * 0.6) - 50;
      posArray[i + 2] = (Math.random() - 0.5) * 60;
    }

    particleGeo.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
    const particleMat = new THREE.PointsMaterial({
      size: 2.8,
      color: beamColor.threeColor,
      transparent: true,
      opacity: 0.55,
      blending: THREE.AdditiveBlending
    });

    const particles = new THREE.Points(particleGeo, particleMat);
    scene.add(particles);

    let clock = new THREE.Clock();
    let frameId;

    const animate = () => {
      frameId = requestAnimationFrame(animate);
      const time = clock.getElapsedTime();

      const positions = particleGeo.attributes.position.array;
      for (let i = 0; i < particleCount * 3; i += 3) {
        positions[i + 1] -= 0.25;
        positions[i] += Math.sin(time * 0.8 + i) * 0.12;
        if (positions[i + 1] < -height / 2) {
          positions[i + 1] = height * 0.3;
        }
      }
      particleGeo.attributes.position.needsUpdate = true;

      let currentAlpha = 1.0;

      if (flickerMode === 'ignition') {
        const cycle = (time * 0.8) % 4.5;
        if (cycle < 0.08) {
          currentAlpha = 1.45;
        } else if (cycle < 0.16) {
          currentAlpha = 0.15;
        } else if (cycle < 0.28) {
          currentAlpha = 1.3;
        } else if (cycle < 0.4) {
          currentAlpha = 0.55;
        } else {
          const microJitter = (Math.sin(time * 65) + Math.cos(time * 110)) * 0.04;
          currentAlpha = 1.0 + microJitter;
        }
      } else if (flickerMode === 'breathing') {
        currentAlpha = 0.35 + (Math.sin(time * 2.8) * 0.5 + 0.5) * 0.8;
      } else if (flickerMode === 'strobe') {
        const strobeCycle = (time * 4) % 2;
        currentAlpha = (strobeCycle < 0.15 || (strobeCycle > 0.25 && strobeCycle < 0.4)) ? 1.4 : 0.1;
      } else {
        currentAlpha = 1.0 + Math.sin(time * 40) * 0.02;
      }

      currentAlpha *= lightIntensity;
      setCurrentFlickerAlpha(currentAlpha);

      beamMaterial.opacity = 0.42 * Math.min(1.2, currentAlpha);
      particleMat.opacity = 0.55 * Math.min(1.2, currentAlpha);

      renderer.render(scene, camera);
    };

    animate();

    const handleResize = () => {
      if (!container) return;
      width = container.clientWidth || window.innerWidth;
      height = container.clientHeight || 720;
      camera.left = -width / 2;
      camera.right = width / 2;
      camera.top = height / 2;
      camera.bottom = -height / 2;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
      updateBeamPositions();
    };

    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(frameId);
      window.removeEventListener('resize', handleResize);
      renderer.dispose();
      leftBeamGeo.dispose();
      rightBeamGeo.dispose();
      beamMaterial.dispose();
      beamTexture.dispose();
      particleGeo.dispose();
      particleMat.dispose();
    };
  }, [beamColor, flickerMode, lightIntensity, isIgniting]);

  const handleTriggerIgnition = () => {
    setIsIgniting(true);
    setFlickerMode('ignition');
    playIgnitionSound();
    setTimeout(() => {
      setIsIgniting(false);
    }, 1800);
  };

  return (
    <div className="hypercar-stage-wrapper" ref={containerRef}>
      {/* 1. REALISTIC BACKGROUND IMAGE */}
      <div className="hypercar-backdrop-layer">
        <img 
          src={heroHypercarBg} 
          alt="Realistic Hypercar Diagnostic Showroom" 
          className="hypercar-photo-bg"
        />
        <div className="hypercar-vignette-overlay" />
      </div>

      {/* 2. THREE.JS WEBGL VOLUMETRIC LIGHT & PARTICLE CANVAS */}
      <canvas ref={canvasRef} className="hypercar-webgl-canvas" />

      {/* 3. OPTICAL HEADLIGHT FLICKER & ANAMORPHIC FLARE OVERLAYS */}
      <div 
        className="optical-flare-container"
        style={{
          '--flare-color': beamColor.flareColor,
          '--flicker-opacity': currentFlickerAlpha
        }}
      >
        <div className="headlight-lens left-headlight">
          <div className="xenon-arc-core" />
          <div className="xenon-halo-glow" />
          <div className="anamorphic-streak" />
        </div>

        <div className="headlight-lens right-headlight">
          <div className="xenon-arc-core" />
          <div className="xenon-halo-glow" />
          <div className="anamorphic-streak" />
        </div>

        <div className="floor-specular-reflection" />
      </div>

      {/* 4. CLEAN COCKPIT HUD OVERLAY */}
      <div className="stage-hud-overlay">
        {/* Top Center: Clean Brand Telemetry Header */}
        <div className="stage-center-headline">
          <div className="concept-badge-row">
            <span className="concept-badge">// AUTONOMOUS VEHICLE HEALTH DIAGNOSTICS</span>
            <span className="concept-badge status-live">NHTSA vPIC VERIFIED</span>
          </div>
          <h1 className="stage-primary-title">
            AUTO-TRIAGE
          </h1>
          <p className="stage-secondary-caption">
            MULTI-AGENT FAULT ISOLATION &bull; CASCADE PREVENTION &bull; OEM PROCUREMENT
          </p>
        </div>

        {/* Bottom Interactive Light Controls Dock */}
        <div className="headlight-controls-dock">
          <button 
            type="button" 
            className={`ignite-light-btn ${isIgniting ? 'igniting' : ''}`}
            onClick={handleTriggerIgnition}
          >
            <Zap size={14} />
            <span>IGNITE XENON ARC</span>
          </button>

          <div className="flicker-modes-group">
            {FLICKER_MODES.map(mode => (
              <button
                key={mode.id}
                type="button"
                className={`mode-pill-btn ${flickerMode === mode.id ? 'active' : ''}`}
                onClick={() => setFlickerMode(mode.id)}
              >
                {mode.label}
              </button>
            ))}
          </div>

          <div className="beam-swatches-group">
            {BEAM_COLORS.map(c => (
              <button
                key={c.name}
                type="button"
                className={`beam-color-dot ${beamColor.name === c.name ? 'active' : ''}`}
                style={{ backgroundColor: c.hex }}
                onClick={() => setBeamColor(c)}
                title={c.name}
              />
            ))}
          </div>

          <button 
            type="button" 
            className={`sound-toggle-btn ${soundEnabled ? 'active' : ''}`}
            onClick={() => setSoundEnabled(!soundEnabled)}
            title="Toggle Xenon High-Voltage Relay Audio"
          >
            {soundEnabled ? <Volume2 size={14} /> : <VolumeX size={14} />}
          </button>
        </div>
      </div>
    </div>
  );
}
