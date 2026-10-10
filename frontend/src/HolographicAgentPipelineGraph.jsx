import React, { useEffect, useRef, useState, useCallback } from 'react';
import { 
  Cpu, 
  Brain, 
  Database, 
  ShoppingBag, 
  Zap, 
  CheckCircle2, 
  Play, 
  RotateCcw, 
  Volume2, 
  VolumeX, 
  Clock, 
  Layers,
  Sparkles,
  Activity,
  ArrowRight
} from 'lucide-react';

/**
 * Cubic Bezier point evaluation for high-performance canvas rendering
 */
function getCubicBezierPoint(p0, p1, p2, p3, t) {
  const cx = 3 * (p1.x - p0.x);
  const bx = 3 * (p2.x - p1.x) - cx;
  const ax = p3.x - p0.x - cx - bx;

  const cy = 3 * (p1.y - p0.y);
  const by = 3 * (p2.y - p1.y) - cy;
  const ay = p3.y - p0.y - cy - by;

  const tSquared = t * t;
  const tCubed = tSquared * t;

  return {
    x: ax * tCubed + bx * tSquared + cx * t + p0.x,
    y: ay * tCubed + by * tSquared + cy * t + p0.y
  };
}

export default function HolographicAgentPipelineGraph({
  activeStage = null, // External stage prop: 'idle' | 'agent1' | 'agent2' | 'agent3' | 'agent4' | 'complete' | 'error'
  liveLatencies = null, // { 1: ms, 2: ms, 3: ms, 4: ms }
  liveData = null, // { triageResult, agent2Result, repairPlan, procurement }
  onRunActualDiagnosis = null,
  onSelectAgent = null,
  embedded = false,
  isLiveDiagnosis = false
}) {
  const canvasRef = useRef(null);
  const animFrameRef = useRef(null);
  const [selectedAgentId, setSelectedAgentId] = useState(1);
  const [soundEnabled, setSoundEnabled] = useState(false);
  
  // simStep: 0: Idle, 1: Agent 1, 2: Agent 2, 3: Agent 3, 4: Agent 4, 5: Complete
  const [simStep, setSimStep] = useState(0);
  const [simulating, setSimulating] = useState(false);
  const [internalLatencies, setInternalLatencies] = useState({ 1: 18, 2: 26, 3: 15, 4: 12 });

  // Web Audio click generator for packet arrival & stage transition
  const playRelayClick = useCallback((pitch = 600) => {
    if (!soundEnabled) return;
    try {
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(pitch, audioCtx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(140, audioCtx.currentTime + 0.035);
      gain.gain.setValueAtTime(0.2, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.035);
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.04);
    } catch {
      // AudioContext unavailable
    }
  }, [soundEnabled]);

  // Synchronize with external activeStage prop when live diagnosis runs
  useEffect(() => {
    if (!activeStage) return;
    
    if (activeStage === 'idle') {
      if (!simulating) setSimStep(0);
    } else if (activeStage === 'agent1' || activeStage === 'ingesting') {
      setSimStep(1);
      setSelectedAgentId(1);
      playRelayClick(520);
    } else if (activeStage === 'agent2' || activeStage === 'reasoning') {
      setSimStep(2);
      setSelectedAgentId(2);
      playRelayClick(650);
    } else if (activeStage === 'agent3' || activeStage === 'rag') {
      setSimStep(3);
      setSelectedAgentId(3);
      playRelayClick(780);
    } else if (activeStage === 'agent4' || activeStage === 'procuring') {
      setSimStep(4);
      setSelectedAgentId(4);
      playRelayClick(920);
    } else if (activeStage === 'complete') {
      setSimStep(5);
      playRelayClick(1080);
    }
  }, [activeStage, simulating, playRelayClick]);

  // Run automated 4-agent simulation cycle
  const handleRunSimulation = useCallback(() => {
    if (simulating || isLiveDiagnosis) return;
    setSimulating(true);
    setSimStep(1);
    setSelectedAgentId(1);
    playRelayClick(520);

    // Randomize dynamic realistic latencies
    setInternalLatencies({
      1: Math.floor(16 + Math.random() * 8),
      2: Math.floor(22 + Math.random() * 10),
      3: Math.floor(14 + Math.random() * 6),
      4: Math.floor(10 + Math.random() * 6)
    });

    const t1 = setTimeout(() => {
      setSimStep(2);
      setSelectedAgentId(2);
      playRelayClick(650);
    }, 1100);

    const t2 = setTimeout(() => {
      setSimStep(3);
      setSelectedAgentId(3);
      playRelayClick(780);
    }, 2200);

    const t3 = setTimeout(() => {
      setSimStep(4);
      setSelectedAgentId(4);
      playRelayClick(920);
    }, 3300);

    const t4 = setTimeout(() => {
      setSimStep(5);
      setSimulating(false);
      playRelayClick(1080);
    }, 4400);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
      clearTimeout(t4);
    };
  }, [simulating, isLiveDiagnosis, playRelayClick]);

  const handleResetSimulation = () => {
    setSimulating(false);
    setSimStep(0);
  };

  // Node Geometry definition within 1000x440 coordinate space
  // Agent 1 -> Fork -> (Agent 2 Top, Agent 3 Bottom) -> Join -> Agent 4
  const NODES = {
    1: { id: 1, x: 130, y: 220, name: 'Agent 1', sub: 'Ingestion & NHTSA', icon: Cpu, stage: 'STAGE 01 // INTAKE', color: '#00F0FF' },
    2: { id: 2, x: 500, y: 110, name: 'Agent 2', sub: 'Diagnostic Reasoning', icon: Brain, stage: 'STAGE 02 // REASON', color: '#3B82F6' },
    3: { id: 3, x: 500, y: 330, name: 'Agent 3', sub: 'Manual Dense RAG', icon: Database, stage: 'STAGE 03 // RAG', color: '#10B981' },
    4: { id: 4, x: 870, y: 220, name: 'Agent 4', sub: 'Parts Procurement', icon: ShoppingBag, stage: 'STAGE 04 // PROCURE', color: '#FF5E14' }
  };

  // Curved Bezier connectors representing the LangGraph Fork-Join DAG
  const EDGES = [
    // Lead-in gateway intake edge to Agent 1
    {
      id: 'e0-1',
      gradientId: 'grad-e0-1',
      from: 0,
      to: 1,
      activeOnStep: 1,
      p0: { x: 20, y: 220 },
      p1: { x: 50, y: 220 },
      p2: { x: 80, y: 220 },
      p3: { x: 95, y: 220 },
      color: '#00F0FF'
    },
    // Agent 1 -> Agent 2 (Reasoning)
    {
      id: 'e1-2',
      gradientId: 'grad-e1-2',
      from: 1,
      to: 2,
      activeOnStep: 2,
      p0: { x: 200, y: 220 },
      p1: { x: 330, y: 220 },
      p2: { x: 360, y: 110 },
      p3: { x: 425, y: 110 },
      color: '#00F0FF'
    },
    // Agent 1 -> Agent 3 (RAG)
    {
      id: 'e1-3',
      gradientId: 'grad-e1-3',
      from: 1,
      to: 3,
      activeOnStep: 3,
      p0: { x: 200, y: 220 },
      p1: { x: 330, y: 220 },
      p2: { x: 360, y: 330 },
      p3: { x: 425, y: 330 },
      color: '#10B981'
    },
    // Agent 2 -> Agent 4 (Procure)
    {
      id: 'e2-4',
      gradientId: 'grad-e2-4',
      from: 2,
      to: 4,
      activeOnStep: 4,
      p0: { x: 575, y: 110 },
      p1: { x: 640, y: 110 },
      p2: { x: 670, y: 220 },
      p3: { x: 800, y: 220 },
      color: '#3B82F6'
    },
    // Agent 3 -> Agent 4 (Procure)
    {
      id: 'e3-4',
      gradientId: 'grad-e3-4',
      from: 3,
      to: 4,
      activeOnStep: 4,
      p0: { x: 575, y: 330 },
      p1: { x: 640, y: 330 },
      p2: { x: 670, y: 220 },
      p3: { x: 800, y: 220 },
      color: '#10B981'
    },
    // Agent 4 -> Complete dossier out
    {
      id: 'e4-out',
      gradientId: 'grad-e4-out',
      from: 4,
      to: 5,
      activeOnStep: 5,
      p0: { x: 935, y: 220 },
      p1: { x: 955, y: 220 },
      p2: { x: 975, y: 220 },
      p3: { x: 990, y: 220 },
      color: '#FF5E14'
    }
  ];

  // Particle System Animation Loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    let particles = [];
    const PARTICLE_COUNT = 44;

    // Initialize flowing photons along the DAG edges
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      const edge = EDGES[i % EDGES.length];
      particles.push({
        edge,
        t: Math.random(),
        speed: 0.0035 + Math.random() * 0.004,
        size: 2.8 + Math.random() * 1.8,
        tail: [],
        tailLength: 8
      });
    }

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const isLight = typeof document !== 'undefined' && document.documentElement.getAttribute('data-theme') === 'light';

      particles.forEach(p => {
        // Boost particle flow speed if corresponding edge is active
        const isEdgeActive = simStep >= p.edge.activeOnStep;
        const isCurrentFocus = simStep === p.edge.activeOnStep;
        const currentSpeed = isCurrentFocus ? p.speed * 3.2 : (isEdgeActive ? p.speed * 2.2 : p.speed * 0.7);

        p.t += currentSpeed;
        if (p.t > 1) {
          p.t = 0;
          p.tail = [];
        }

        const pt = getCubicBezierPoint(p.edge.p0, p.edge.p1, p.edge.p2, p.edge.p3, p.t);

        // Store trail
        p.tail.unshift({ ...pt });
        if (p.tail.length > p.tailLength) p.tail.pop();

        // Draw particle tail / photon trail with radiant jewel glow
        if (p.tail.length > 1) {
          ctx.beginPath();
          ctx.moveTo(p.tail[0].x, p.tail[0].y);
          for (let j = 1; j < p.tail.length; j++) {
            ctx.lineTo(p.tail[j].x, p.tail[j].y);
          }
          ctx.strokeStyle = isEdgeActive ? p.edge.color : (isLight ? p.edge.color + '88' : 'rgba(255, 255, 255, 0.22)');
          ctx.lineWidth = isCurrentFocus ? p.size * 1.25 : (isEdgeActive ? p.size * 0.95 : p.size * 0.65);
          ctx.lineCap = 'round';
          ctx.stroke();
        }

        // Draw glowing particle head in saturated edge jewel-tone
        ctx.save();
        ctx.shadowBlur = isCurrentFocus ? 26 : (isEdgeActive ? 18 : (isLight ? 12 : 8));
        ctx.shadowColor = p.edge.color;
        ctx.fillStyle = p.edge.color;
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, isCurrentFocus ? p.size * 1.9 : (isEdgeActive ? p.size * 1.5 : (isLight ? p.size * 1.25 : p.size * 1.05)), 0, Math.PI * 2);
        ctx.fill();

        // Luminous star core reflection
        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, isCurrentFocus ? p.size * 0.9 : (isEdgeActive ? p.size * 0.7 : p.size * 0.48), 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      });

      animFrameRef.current = requestAnimationFrame(render);
    };

    render();

    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [simStep]);

  // Exact Node Status Determination
  // When Agent 1 runs: 1 is working, others idle
  // When Agent 2 runs: 1 is completed, 2 is working, others idle
  // When Agent 3 runs: 1 & 2 completed, 3 is working, 4 idle
  // When Agent 4 runs: 1, 2, 3 completed, 4 is working
  // When Complete: all 4 completed!
  const getNodeStatus = (nodeId) => {
    if (simStep === 0) return 'idle';
    if (nodeId === 1) {
      if (simStep === 1) return 'working';
      return 'completed';
    }
    if (nodeId === 2) {
      if (simStep < 2) return 'idle';
      if (simStep === 2) return 'working';
      return 'completed';
    }
    if (nodeId === 3) {
      if (simStep < 3) return 'idle';
      if (simStep === 3) return 'working';
      return 'completed';
    }
    if (nodeId === 4) {
      if (simStep < 4) return 'idle';
      if (simStep === 4) return 'working';
      return 'completed';
    }
    return 'idle';
  };

  const handleNodeClick = (nodeId) => {
    setSelectedAgentId(nodeId);
    if (onSelectAgent) onSelectAgent(nodeId);
  };

  // Resolve latencies: prioritize live measured execution times when provided
  const latencies = liveLatencies || internalLatencies;
  const totalExecutionLatency = (latencies[1] || 0) + (latencies[2] || 0) + (latencies[3] || 0) + (latencies[4] || 0);

  // Inspector Drawer Telemetry Details
  const getAgentDetails = (nodeId) => {
    const isLive = Boolean(liveData && (liveData.triageResult || liveData.agent2Result));
    
    const isQuarantined = Boolean(
      liveData?.triageResult?.security_guardrail?.threat_level === 'CRITICAL_ATTACK_BLOCKED' ||
      liveData?.agent2Result?.root_cause_component?.includes('SECURITY') ||
      liveData?.agent2Result?.severity === 'Quarantined'
    );

    if (nodeId === 1) {
      const tr = liveData?.triageResult;
      const count = (tr?.dtc_codes || []).length;
      return {
        title: 'Agent 1: Gateway Ingestion & Federal Truth Check',
        stack: 'spaCy NLP (v3.7) + U.S. DOT NHTSA vPIC REST API + ISO 3779 Checksum',
        role: 'Normalizes mechanic unstructured dialect, extracts standard SAE DTC trouble codes, and validates VIN identity against federal registry records in < 20ms.',
        payload: tr ? (
          isQuarantined
            ? `[PERIMETER DEFENSE ACTIVE] Threat Level: ${tr.security_guardrail?.threat_level || 'CRITICAL_ATTACK_BLOCKED'} // Adversarial prompt neutralized // ${count} DTCs Isolated`
            : `${count} DTCs Isolated (${(tr.dtc_codes || []).join(', ') || 'Clean'}) // Ground Truth: ${tr.vehicle_details?.is_verified ? '100% NHTSA Verified' : 'Validated'} // ${tr.vehicle_details?.year} ${tr.vehicle_details?.make} ${tr.vehicle_details?.model}`
        ) : '3 DTCs Isolated (P0171, P0300, P0420) // VIN Ground Truth: 100% Match',
        outputKey: tr?.vehicle_details ? `Canonical Spec: ${tr.vehicle_details.make} ${tr.vehicle_details.model} (${tr.vehicle_details.engine || 'Standard Powertrain'})` : 'Canonical Diagnostic Graph & Multi-DTC Cascade Matrix',
        isLive
      };
    }
    if (nodeId === 2) {
      const a2 = liveData?.agent2Result;
      return {
        title: 'Agent 2: Cognitive Causal Reasoning Core',
        stack: 'Groq LLM / Llama-3 70B + Pydantic Strict AST + Dual-Pass Hallucination Guard',
        role: 'Applies physics of failure reasoning to deduce the underlying root cause component, calculates Bayesian failure likelihood, and enforces safety warnings.',
        payload: isQuarantined ? (
          'CIRCUIT BREAKER ACTIVATED // 0 Groq LLM Tokens Dispatched (Model Denial-of-Service / Wallet DoS Eliminated) // Reasoning Suspended'
        ) : a2 ? (
          `Root Cause: ${a2.root_cause_component || 'Deducing...'} // Severity: ${a2.severity || 'Medium'} // Mode: ${a2.failure_mode ? a2.failure_mode.slice(0, 85) + '...' : 'Analyzed'}`
        ) : 'Root Cause: Mass Air Flow Sensor Contamination // 96.4% Diagnostic Confidence',
        outputKey: isQuarantined
          ? 'Quarantine Status: PIPELINE_SUSPENDED_SECURITY_QUARANTINE'
          : (a2?.safety_warning ? `Safety: ${a2.safety_warning.slice(0, 80)}...` : 'Failure Mode Physics & Ranked Differential Hypotheses'),
        isLive
      };
    }
    if (nodeId === 3) {
      const rp = liveData?.repairPlan;
      return {
        title: 'Agent 3: OEM Workshop Dense Vector RAG',
        stack: 'ChromaDB Local Vector DB + Recursive Sentence Embeddings + Cosine Index',
        role: 'Performs dense semantic similarity searches across verified OEM factory service manuals to pull strict step-by-step disassembly and torque specifications.',
        payload: isQuarantined ? (
          'OEM MANUAL RAG WITHHELD // Vector query suspended to safeguard OEM technical knowledge base under Security Circuit Breaker'
        ) : rp ? (
          `Service Manual Retrieved // Action: ${rp.recommended_action ? rp.recommended_action.slice(0, 70) + '...' : 'OEM Factory Procedure'}`
        ) : 'ChromaDB Top-3 Chunks Retrieved // Torque Spec: 8.5 N·m (75 in-lbs)',
        outputKey: isQuarantined
          ? 'RAG Status: Suppressed by Circuit Breaker'
          : (rp?.required_tools ? `Required Tools: ${(rp.required_tools || []).slice(0, 3).join(', ')}` : 'Factory Removal Checklist & Strict Zero-Hallucination Guardrails'),
        isLive
      };
    }
    if (nodeId === 4) {
      const proc = liveData?.procurement || liveData?.procurementPlan;
      return {
        title: 'Agent 4: BOM Catalog & Automated Procurement',
        stack: 'Motor/Mitchell Cross-Catalog Index + MongoDB Multi-Tier Pricing Engine',
        role: 'Resolves physical component names into verified distributor SKUs, discovers mandatory gasket/seal dependencies, and generates 3-tier quotes in LKR.',
        payload: isQuarantined ? (
          'PARTS PROCUREMENT & PRICING LOCKED // 0 Components Quoted · 0 LKR Bill Total (Billing Manipulation Exploit Prevented)'
        ) : proc?.primary_part?.pricing?.oem_lkr ? (
          `Quoted: OEM Genuine (${Number(proc.primary_part.pricing.oem_lkr).toLocaleString()} LKR) | Aftermarket (${Number(proc.primary_part.pricing.aftermarket_lkr || 0).toLocaleString()} LKR)`
        ) : (proc?.primary_part?.part_name ? `Resolved Part: ${proc.primary_part.part_name}` : 'Quoted: OEM Genuine (48,500 LKR) | Aftermarket (26,000 LKR) | Economy (14,500 LKR)'),
        outputKey: isQuarantined
          ? 'Procurement Status: 0 LKR Quotes (Withheld)'
          : (proc?.primary_part?.oem_part_number ? `OEM Part Number: ${proc.primary_part.oem_part_number}` : 'Mandatory Gasket Lock & Localized Part Availability Matrix'),
        isLive
      };
    }
    return null;
  };

  const selectedAgentDetails = getAgentDetails(selectedAgentId);
  const isRunningLive = ['agent1', 'agent2', 'agent3', 'agent4'].includes(activeStage);

  return (
    <div className={`holographic-pipeline-root ${embedded ? 'embedded-mode' : ''}`}>
      {/* Top Controls & Status Bar */}
      <div className="pipeline-top-bar">
        <div className="pipeline-title-group">
          <h3 className="pipeline-heading">
            <Sparkles size={16} color="var(--accent-primary)" />
            Holographic 4-Agent Particle Pipeline
          </h3>
        </div>

        <div className="pipeline-actions-group">
          {/* Live Execution Indicator Badge */}
          {(isRunningLive || isLiveDiagnosis) && (
            <div className="pipeline-live-stream-badge">
              <span className="live-pulsing-dot" />
              <span>LIVE TRIAGE FLOWING...</span>
            </div>
          )}

          {/* Trigger Actual Live Diagnosis if prop provided */}
          {onRunActualDiagnosis && !isRunningLive && (
            <button
              type="button"
              onClick={onRunActualDiagnosis}
              className="pipeline-live-run-btn"
              title="Execute full real-time diagnosis on backend"
            >
              <Zap size={13} fill="currentColor" />
              <span>RUN LIVE DIAGNOSIS</span>
            </button>
          )}

          {/* Simulation Toggle Button */}
          <button
            type="button"
            onClick={handleRunSimulation}
            disabled={simulating || isRunningLive || isLiveDiagnosis}
            className={`pipeline-sim-btn ${simulating ? 'simulating' : ''}`}
            title="Trigger animated packet stream simulation"
          >
            <Play size={13} fill="currentColor" />
            <span>{isRunningLive ? 'ORCHESTRATING...' : (simulating ? 'PIPELINE ACTIVE...' : 'SIMULATE FLOW')}</span>
          </button>

          {simStep > 0 && !simulating && !isRunningLive && (
            <button
              type="button"
              onClick={handleResetSimulation}
              className="pipeline-icon-btn"
              title="Reset pipeline graph"
            >
              <RotateCcw size={13} />
            </button>
          )}

          {/* Audio Click Relay Toggle */}
          <button
            type="button"
            onClick={() => setSoundEnabled(prev => !prev)}
            className={`pipeline-icon-btn ${soundEnabled ? 'active' : ''}`}
            title={soundEnabled ? 'Audio clicks enabled' : 'Enable realistic relay sound clicks'}
          >
            {soundEnabled ? <Volume2 size={14} color="var(--accent-primary)" /> : <VolumeX size={14} />}
          </button>

          {/* End-to-End Latency Badge */}
          <div className="pipeline-sla-pill">
            <Clock size={12} color="var(--accent-primary)" />
            <span>TOTAL LATENCY: <strong>{totalExecutionLatency} ms</strong></span>
          </div>
        </div>
      </div>

      {/* Main Holographic Canvas & SVG Graph Container */}
      <div className="holographic-graph-viewport">
        {/* SVG Flow Lines & Gradient Connectors */}
        <svg className="graph-svg-layer" viewBox="0 0 1000 440" preserveAspectRatio="xMidYMid meet">
          <defs>
            {/* Glow Filter */}
            <filter id="neon-glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3.5" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>

            {/* Path Gradients */}
            <linearGradient id="grad-e0-1" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#00F0FF" stopOpacity="0.45" />
              <stop offset="100%" stopColor="#00F0FF" stopOpacity="0.95" />
            </linearGradient>
            <linearGradient id="grad-e1-2" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#00F0FF" stopOpacity="0.95" />
              <stop offset="100%" stopColor="#3B82F6" stopOpacity="0.95" />
            </linearGradient>
            <linearGradient id="grad-e1-3" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#00F0FF" stopOpacity="0.95" />
              <stop offset="100%" stopColor="#10B981" stopOpacity="0.95" />
            </linearGradient>
            <linearGradient id="grad-e2-4" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#3B82F6" stopOpacity="0.95" />
              <stop offset="100%" stopColor="#FF5E14" stopOpacity="0.95" />
            </linearGradient>
            <linearGradient id="grad-e3-4" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#10B981" stopOpacity="0.95" />
              <stop offset="100%" stopColor="#FF5E14" stopOpacity="0.95" />
            </linearGradient>
            <linearGradient id="grad-e4-out" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#FF5E14" stopOpacity="0.95" />
              <stop offset="100%" stopColor="#FF5E14" stopOpacity="0.35" />
            </linearGradient>
          </defs>

          {/* Passive Background Grid Lines */}
          <line className="graph-grid-line" x1="50" y1="220" x2="950" y2="220" stroke="rgba(255, 255, 255, 0.05)" strokeDasharray="4 6" />
          <line className="graph-grid-line" x1="500" y1="50" x2="500" y2="390" stroke="rgba(255, 255, 255, 0.05)" strokeDasharray="4 6" />

          {/* Base Wire Connector Paths */}
          {EDGES.map(edge => {
            const pathData = `M ${edge.p0.x} ${edge.p0.y} C ${edge.p1.x} ${edge.p1.y}, ${edge.p2.x} ${edge.p2.y}, ${edge.p3.x} ${edge.p3.y}`;
            const isActive = simStep >= edge.activeOnStep;
            const isFocus = simStep === edge.activeOnStep;
            const strokeColor = edge.gradientId ? `url(#${edge.gradientId})` : edge.color;

            return (
              <g key={edge.id}>
                {/* Outer Glow Path */}
                <path
                  d={pathData}
                  fill="none"
                  stroke={strokeColor}
                  strokeWidth={isFocus ? 4.5 : (isActive ? 3.2 : 2.2)}
                  strokeOpacity={isFocus ? 1 : (isActive ? 0.85 : 0.42)}
                  filter={isActive ? "url(#neon-glow)" : undefined}
                />
                {/* Core Luminous Pulse Line */}
                <path
                  d={pathData}
                  fill="none"
                  stroke={isFocus ? '#ffffff' : (isActive ? 'rgba(255, 255, 255, 0.85)' : 'rgba(255, 255, 255, 0.35)')}
                  strokeWidth={isFocus ? 2.2 : (isActive ? 1.4 : 0.9)}
                  strokeOpacity={isFocus ? 1 : 0.65}
                />
              </g>
            );
          })}

          {/* Fork & Join Label Micro Tags */}
          <g transform="translate(340, 212)">
            <rect className="graph-flow-pill-bg" x="-38" y="-10" width="76" height="20" rx="10" fill="rgba(11, 14, 22, 0.88)" stroke="rgba(255, 255, 255, 0.18)" />
            <text className="graph-flow-pill-text" x="0" y="3.5" fill="var(--text-muted)" fontSize="9" fontWeight="800" textAnchor="middle" fontFamily="var(--font-mono)">
              FORK // ASYNC
            </text>
          </g>

          <g transform="translate(680, 212)">
            <rect className="graph-flow-pill-bg" x="-42" y="-10" width="84" height="20" rx="10" fill="rgba(11, 14, 22, 0.88)" stroke="rgba(255, 255, 255, 0.18)" />
            <text className="graph-flow-pill-text" x="0" y="3.5" fill="var(--text-muted)" fontSize="9" fontWeight="800" textAnchor="middle" fontFamily="var(--font-mono)">
              JOIN // CONVERGE
            </text>
          </g>
        </svg>

        {/* HTML5 Canvas Photon Particle Rendering Layer */}
        <canvas
          ref={canvasRef}
          width={1000}
          height={440}
          className="graph-particle-canvas"
        />

        {/* Interactive Holographic Agent Node Cards */}
        <div className="graph-nodes-layer">
          {Object.values(NODES).map(node => {
            const status = getNodeStatus(node.id);
            const isSelected = selectedAgentId === node.id;
            const Icon = node.icon;
            const latency = latencies[node.id] || 0;
            const isWorking = status === 'working';
            const isCompleted = status === 'completed';

            return (
              <div
                key={node.id}
                onClick={() => handleNodeClick(node.id)}
                className={`holo-node-container node-${node.id} status-${status} ${isSelected ? 'selected' : ''}`}
                style={{
                  left: `${(node.x / 1000) * 100}%`,
                  top: `${(node.y / 440) * 100}%`,
                  '--agent-glow-color': node.color
                }}
              >
                {/* Outer Status Radar Ring */}
                <div className={`status-radar-ring ${status}`} />

                {/* Main Node Disc */}
                <div className="holo-node-disc">
                  <div className="holo-node-glow-core" />
                  <Icon size={22} className="node-center-icon" />

                  {/* Completion Checkmark Badge */}
                  {isCompleted && (
                    <div className="node-check-pip">
                      <CheckCircle2 size={14} color="#10B981" />
                    </div>
                  )}
                </div>

                {/* Node Metadata & Dynamic Micro-Badges */}
                <div className="holo-node-meta">
                  <span className="node-stage-tag">{node.stage}</span>
                  <strong className="node-agent-name">{node.name}</strong>
                  <span className="node-agent-sub">{node.sub}</span>

                  <div className="node-micro-badges-row">
                    {/* Live Latency Badge */}
                    <span className={`latency-micro-badge ${isWorking ? 'working-latency' : ''}`}>
                      <Zap size={10} color={isWorking ? node.color : 'var(--accent-primary)'} />
                      {isWorking ? 'PROCESSING...' : `${latency} ms`}
                    </span>

                    {/* Status Pill Badge */}
                    <span className={`status-micro-pill ${status}`}>
                      {isWorking ? (
                        <>
                          <span className="mini-pulse-beacon" />
                          ACTIVE
                        </>
                      ) : isCompleted ? (
                        'DONE'
                      ) : (
                        'QUEUED'
                      )}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Selected Node Telemetry Inspector Drawer */}
      {selectedAgentDetails && (
        <div className={`pipeline-inspector-drawer selected-agent-${selectedAgentId}`}>
          <div className="inspector-header-row">
            <div className="inspector-title-box">
              <Layers size={14} color="var(--accent-primary)" />
              <strong>{selectedAgentDetails.title}</strong>
              <span className="inspector-tech-pill">{selectedAgentDetails.stack}</span>
              {selectedAgentDetails.isLive && (
                <span className="inspector-live-tag">LIVE TELEMETRY</span>
              )}
            </div>
            <div className="inspector-latency-chip">
              <Clock size={12} />
              <span>Execution SLA: ~{latencies[selectedAgentId] || 20} ms</span>
            </div>
          </div>

          <div className="inspector-body-grid">
            <div className="inspector-info-card">
              <span className="inspector-label">MICROSERVICE ROLE</span>
              <p className="inspector-text">{selectedAgentDetails.role}</p>
            </div>
            <div className="inspector-info-card">
              <span className="inspector-label">LIVE PAYLOAD TELEMETRY</span>
              <p className="inspector-text accent-highlight">{selectedAgentDetails.payload}</p>
            </div>
            <div className="inspector-info-card">
              <span className="inspector-label">LANGGRAPH CONTRACT OUT</span>
              <p className="inspector-text code-font">{selectedAgentDetails.outputKey}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
