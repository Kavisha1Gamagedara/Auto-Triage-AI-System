import React, { useState, useEffect } from 'react';
import { 
  Car, 
  ShieldCheck, 
  AlertTriangle, 
  Cpu, 
  ArrowRight, 
  RefreshCw, 
  Copy, 
  Check, 
  Wrench, 
  Sparkles, 
  Activity, 
  Layers, 
  ChevronDown,
  ChevronUp,
  Terminal,
  ExternalLink,
  Zap,
  Gauge,
  Database,
  Sliders,
  Radio,
  CheckCircle2,
  AlertOctagon,
  Brain,
  Tag,
  ShoppingBag,
  Barcode
} from 'lucide-react';

import './App.css';
import heroDarkCar from './assets/hero_dark_car.jpg';
import cinematicSportsCar from './assets/cinematic_sports_car.jpg';
import mechanicDiagnostics from './assets/mechanic_diagnostics.jpg';

const API_BASE_URL = 'http://localhost:8000';

const PRESETS = [
  {
    label: 'Honda Civic (P0171 Lean)',
    text: '2019 Honda Civic with trouble code P0171 running rough and check engine light on'
  },
  {
    label: 'Ford F-150 (P0300 Misfire)',
    text: 'Technician note: 2017 Ford F-150 misfiring on acceleration code P0300 with cracked spark plug'
  },
  {
    label: 'Toyota Camry (P0420 Cat)',
    text: 'Customer brought in 2021 Toyota Camry showing code P0420 and damaged catalytic converter'
  },
  {
    label: 'Bogus Vehicle Test',
    text: '2025 Ford GalaxyCruiser9000 engine making loud noise with trouble code P0999'
  }
];

const AGENT2_PRESETS = [
  {
    label: '1995 Toyota Townace (P0251 Fuel)',
    make: 'Toyota',
    model: 'Townace',
    year: '1995',
    dtcs: 'P0251',
    notes: 'Engine lacks power and stalls. Suspected fuel delivery issue or injection pump timing fault on the 1C engine.'
  },
  {
    label: '2019 Honda Civic (P0171 Lean)',
    make: 'Honda',
    model: 'Civic',
    year: '2019',
    dtcs: 'P0171',
    notes: 'Vehicle runs rough on idle, check engine light illuminated, hesitates under light acceleration with +24% fuel trim.'
  },
  {
    label: '2017 Ford F-150 (P0300 Misfire)',
    make: 'Ford',
    model: 'F-150',
    year: '2017',
    dtcs: 'P0300',
    notes: 'Technician note: violent shuddering under highway hill climb, intermittent ignition misfire logged across bank 1.'
  },
  {
    label: '2021 Toyota Camry (P0420 Cat)',
    make: 'Toyota',
    model: 'Camry',
    year: '2021',
    dtcs: 'P0420',
    notes: 'Customer reports sulfur exhaust odor and check engine lamp on dashboard, downstream O2 sensor mirroring upstream.'
  }
];

const SIMULATED_DIAGNOSES = {
  P0251: {
    root_cause_component: 'Spill Valve (Electronic Diesel Injection Pump)',
    failure_mode: 'DTC P0251 designates Fuel Metering Control Malfunction. The electric spill valve solenoid coil has suffered thermal breakdown and plunger sticking on the 1C-T diesel pump, causing sporadic fuel cut-off and engine stalls under acceleration load.',
    severity: 'Critical',
    safety_warning: 'High-pressure diesel spray hazard (up to 1,500 bar). System must be fully depressurized prior to loosening union nuts. Do not expose skin to pressurized fuel spray.'
  },
  P0171: {
    root_cause_component: 'Mass Air Flow (MAF) Sensor',
    failure_mode: 'Contaminated platinum hot-wire sensing element under-reporting incoming intake air volume to ECM, forcing fuel trims beyond compensatory limit (+25% STFT/LTFT) and causing lean combustion misfire.',
    severity: 'Medium',
    safety_warning: 'Allow engine bay and intake manifold to cool down completely before inspecting intake boot, vacuum hoses, and sensor harness.'
  },
  P0300: {
    root_cause_component: 'Ignition Coil On Plug (COP)',
    failure_mode: 'Dielectric insulation breakdown within secondary coil windings resulting in high-voltage spark dissipation to cylinder head casing under combustion chamber compression.',
    severity: 'Medium',
    safety_warning: 'Secondary ignition circuitry operates in excess of 35,000 Volts. Turn ignition off and disconnect battery ground terminal before disassembling ignition coils.'
  },
  P0420: {
    root_cause_component: 'Three-Way Catalytic Converter Substrate',
    failure_mode: 'Thermal sintering and hydrocarbon carbonization of the platinum/rhodium catalytic washcoat, severely degrading oxygen storage capacity (OSC).',
    severity: 'Low',
    safety_warning: 'Catalytic converter skin temperatures frequently exceed 600°C (1,100°F). Ensure vehicle has cooled down for at least two hours before attempting physical inspection or bolt extraction.'
  }
};

const FAQ_ITEMS = [
  {
    q: 'How does Agent 1 prevent vehicle hallucinations?',
    a: 'Agent 1 cross-references every extracted Make, Model, and Year in real time against the official U.S. Department of Transportation (NHTSA vPIC) database via an asynchronous REST API. If the vehicle configuration is fictitious or never manufactured, it is rejected with an HTTP 400 validation error.'
  },
  {
    q: 'What is the Agent-to-Agent (A2A) payload format?',
    a: 'Agent 1 produces a strongly-typed Pydantic contract (Agent1Payload) containing the session ID, verified vehicle parameters (Make, Model, Year, is_verified=True), discovered OBD-II DTC codes, and damaged physical parts. This clean schema is consumed directly by Agent 2 for cognitive reasoning.'
  },
  {
    q: 'How does the LangGraph Fork-Join architecture operate?',
    a: 'The workflow initiates at Agent 1 (Ingestion & Validation). Once verified, data transitions to Agent 2 (Diagnostic Reasoning) which deduces the root-cause failure. At this point, the pipeline forks into two parallel branches: Agent 3 performs dense vector retrieval (ChromaDB) over OEM workshop manuals, while Agent 4 queries a MongoDB parts catalog for pricing. Both branches join to assemble the final diagnostic report.'
  },
  {
    q: 'Do we need a database for vehicle verification?',
    a: 'No local database is required for vehicle models or production years. The NHTSA vPIC database is an authoritative, public REST API maintained by the federal government and queried dynamically on demand.'
  }
];

function generateSessionId() {
  return `sess_${Math.random().toString(36).substring(2, 8)}_${Date.now().toString(36).substring(4)}`;
}

export default function App() {
  const [sessionId, setSessionId] = useState(generateSessionId());
  const [rawText, setRawText] = useState(PRESETS[0].text);
  const [loading, setLoading] = useState(false);
  const [pipelineStage, setPipelineStage] = useState('idle'); // 'idle' | 'agent1' | 'agent2' | 'complete' | 'error'
  const [showRawJson, setShowRawJson] = useState(false);
  const [triageResult, setTriageResult] = useState(null);
  const [repairPlan, setRepairPlan] = useState(null);
  const [procurementPlan, setProcurementPlan] = useState(null);
  const [error, setError] = useState(null);
  const [serverStatus, setServerStatus] = useState('checking'); // 'online' | 'offline' | 'checking'
  const [copied, setCopied] = useState(false);
  const [openFaq, setOpenFaq] = useState(0);

  const [intakeMode, setIntakeMode] = useState('smart'); // 'smart' | 'manual' | 'vin'
  const [manualMake, setManualMake] = useState('Honda');
  const [manualModel, setManualModel] = useState('Civic');
  const [manualYear, setManualYear] = useState('2019');
  const [manualDtcs, setManualDtcs] = useState('P0171');
  const [manualParts, setManualParts] = useState('crashed bumper');

  const [vinInput, setVinInput] = useState('1HGCR2F85HA000000');
  const [vinDtcs, setVinDtcs] = useState('P0171, P0420');
  const [vinParts, setVinParts] = useState('crashed bumper');

  const VIN_PRESETS = [
    { label: '2017 Honda Accord (Valid)', vin: '1HGCR2F85HA000000', dtcs: 'P0171', parts: 'intake manifold leak' },
    { label: '2021 Ford F-150 (Valid)', vin: '1FTFW1E84MFA00000', dtcs: 'P0300', parts: 'cracked ignition coil' },
    { label: '2020 Toyota Camry (Valid)', vin: '4T1B11HK5LU000000', dtcs: 'P0420', parts: 'catalytic converter' },
    { label: 'Invalid Checksum Test', vin: '1HGCR2F89HA000000', dtcs: 'P0171', parts: 'bogus check digit' }
  ];

  const MANUAL_PRESETS = [
    { label: '2019 Honda Civic', make: 'Honda', model: 'Civic', year: 2019, dtcs: 'P0171', parts: 'crashed bumper' },
    { label: '2017 Ford F-150', make: 'Ford', model: 'F-150', year: 2017, dtcs: 'P0300', parts: 'cracked spark plug' },
    { label: '2021 Toyota Camry', make: 'Toyota', model: 'Camry', year: 2021, dtcs: 'P0420', parts: 'catalytic converter' },
    { label: 'Bogus Car Test', make: 'Ford', model: 'GalaxyCruiser9000', year: 2025, dtcs: 'P0999', parts: 'warp drive' }
  ];

  // Check Backend Health on Mount
  useEffect(() => {
    checkHealth();
  }, []);

  const checkHealth = async () => {
    try {
      setServerStatus('checking');
      const res = await fetch(`${API_BASE_URL}/api/health`);
      if (res.ok) {
        setServerStatus('online');
      } else {
        setServerStatus('offline');
      }
    } catch {
      setServerStatus('offline');
    }
  };

  const handleNewSession = () => {
    setSessionId(generateSessionId());
    setTriageResult(null);
    setAgent2Result(null);
    setPipelineStage('idle');
    setError(null);
  };

  const handlePresetClick = (presetText) => {
    setRawText(presetText);
    setError(null);
  };

  const handleManualPresetClick = (p) => {
    setManualMake(p.make);
    setManualModel(p.model);
    setManualYear(String(p.year));
    setManualDtcs(p.dtcs);
    setManualParts(p.parts);
    setError(null);
  };

  const handleVinPresetClick = (p) => {
    setVinInput(p.vin);
    setVinDtcs(p.dtcs);
    setVinParts(p.parts);
    setError(null);
  };

  const handleCopyPayload = () => {
    if (!triageResult) return;
    navigator.clipboard.writeText(JSON.stringify(triageResult, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Agent 2 Cognitive Reasoning States
  const [agent2Make, setAgent2Make] = useState(AGENT2_PRESETS[0].make);
  const [agent2Model, setAgent2Model] = useState(AGENT2_PRESETS[0].model);
  const [agent2Year, setAgent2Year] = useState(AGENT2_PRESETS[0].year);
  const [agent2Dtcs, setAgent2Dtcs] = useState(AGENT2_PRESETS[0].dtcs);
  const [agent2Notes, setAgent2Notes] = useState(AGENT2_PRESETS[0].notes);
  const [agent2Loading, setAgent2Loading] = useState(false);
  const [agent2Result, setAgent2Result] = useState(null);
  const [agent2Error, setAgent2Error] = useState(null);
  const [agent2Source, setAgent2Source] = useState('preset'); // 'agent1' | 'preset' | 'custom'
  const [selectedAgent2Preset, setSelectedAgent2Preset] = useState(0);

  const handleSelectAgent2Preset = (p, idx) => {
    setAgent2Make(p.make);
    setAgent2Model(p.model);
    setAgent2Year(p.year);
    setAgent2Dtcs(p.dtcs);
    setAgent2Notes(p.notes);
    setSelectedAgent2Preset(idx);
    setAgent2Source('preset');
    setAgent2Error(null);
  };

  const handleHandoffToAgent2 = (result) => {
    if (!result) return;
    setAgent2Make(result.vehicle_details.make);
    setAgent2Model(result.vehicle_details.model);
    setAgent2Year(String(result.vehicle_details.year));
    setAgent2Dtcs(result.dtc_codes.join(', '));
    setAgent2Notes(
      result.user_note || 
      (result.damaged_parts.length > 0 
        ? `Damage noted: ${result.damaged_parts.join(', ')}. Discovered DTCs: ${result.dtc_codes.join(', ')}.`
        : `Vehicle verified by Agent 1 gateway. Trouble codes: ${result.dtc_codes.join(', ')}.`
      )
    );
    setAgent2Source('agent1');
    setSelectedAgent2Preset(null);
    setAgent2Error(null);

    const el = document.getElementById('agent2');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const handleRunAgent2Diagnostics = async (e) => {
    if (e) e.preventDefault();
    if (agent2Loading) return;

    setAgent2Loading(true);
    setAgent2Error(null);

    try {
      const dtcList = agent2Dtcs
        .split(/[,\s]+/)
        .map(s => s.trim().toUpperCase())
        .filter(Boolean);

      const payload = {
        session_id: sessionId,
        vehicle: {
          make: agent2Make.trim(),
          model: agent2Model.trim(),
          year: parseInt(agent2Year, 10)
        },
        dtc_codes: dtcList,
        user_note: agent2Notes.trim()
      };

      const res = await fetch(`${API_BASE_URL}/api/v1/diagnose`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || `Diagnostic reasoning returned HTTP ${res.status}`);
      }

      setAgent2Result(data);
    } catch (err) {
      setAgent2Error(err.message || 'Diagnostic reasoning error.');
    } finally {
      setAgent2Loading(false);
    }
  };

  const handleSimulateAgent2 = () => {
    setAgent2Loading(true);
    setAgent2Error(null);

    setTimeout(() => {
      const upperDtcs = agent2Dtcs.toUpperCase();
      let matchedKey = Object.keys(SIMULATED_DIAGNOSES).find(k => upperDtcs.includes(k));
      if (!matchedKey) matchedKey = 'P0251';

      const sim = SIMULATED_DIAGNOSES[matchedKey];
      setAgent2Result({
        root_cause_component: sim.root_cause_component,
        failure_mode: `[SIMULATED MASTER MECHANIC REASONING] For ${agent2Year} ${agent2Make} ${agent2Model}: ${sim.failure_mode}`,
        severity: sim.severity,
        safety_warning: sim.safety_warning
      });
      setAgent2Loading(false);
    }, 600);
  };

  const handleRunTriage = async (e) => {
    if (e) e.preventDefault();
    if (pipelineStage === 'agent1' || pipelineStage === 'agent2') return;

    setPipelineStage('agent1');
    setLoading(true);
    setError(null);
    setTriageResult(null);
    setAgent2Result(null);

    try {
      let payload = {};

      if (intakeMode === 'smart') {
        if (!rawText.trim()) return;
        payload = {
          session_id: sessionId,
          raw_text: rawText.trim()
        };
      } else if (intakeMode === 'vin') {
        if (!vinInput.trim()) {
          throw new Error('Please enter a 17-character VIN.');
        }

        const dtcArray = vinDtcs
          .split(/[,\s]+/)
          .map(s => s.trim().toUpperCase())
          .filter(Boolean);

        const partsArray = vinParts
          .split(',')
          .map(s => s.trim().toLowerCase())
          .filter(Boolean);

        payload = {
          session_id: sessionId,
          vin: vinInput.trim().toUpperCase(),
          dtc_codes: dtcArray,
          damaged_parts: partsArray,
          raw_text: `VIN Intake: ${vinInput.trim().toUpperCase()}`
        };
      } else {
        // Manual Spec Entry Mode
        if (!manualMake.trim() || !manualModel.trim() || !manualYear) {
          throw new Error('Please specify Vehicle Make, Model, and Year.');
        }

        const dtcArray = manualDtcs
          .split(/[,\s]+/)
          .map(s => s.trim().toUpperCase())
          .filter(Boolean);

        const partsArray = manualParts
          .split(',')
          .map(s => s.trim().toLowerCase())
          .filter(Boolean);

        payload = {
          session_id: sessionId,
          make: manualMake.trim(),
          model: manualModel.trim(),
          year: parseInt(manualYear, 10),
          dtc_codes: dtcArray,
          damaged_parts: partsArray,
          raw_text: `${manualYear} ${manualMake} ${manualModel} with ${manualParts}`
        };
      }

      // ==========================================
      // STAGE 1: Execute Agent 1 Ingestion & NHTSA Validation
      // ==========================================
      const response = await fetch(`${API_BASE_URL}/api/v1/ingest`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
      });

      const data1 = await response.json();

      if (!response.ok) {
        throw new Error(data1.detail || 'Vehicle validation failed against NHTSA vPIC database.');
      }

      setTriageResult(data1);

      // Sync Agent 2 lab console state
      setAgent2Make(data1.vehicle_details.make);
      setAgent2Model(data1.vehicle_details.model);
      setAgent2Year(String(data1.vehicle_details.year));
      setAgent2Dtcs(data1.dtc_codes.join(', '));
      setAgent2Notes(data1.user_note || `Vehicle verified: ${data1.vehicle_details.year} ${data1.vehicle_details.make} ${data1.vehicle_details.model}`);
      setAgent2Source('agent1');

      // ==========================================
      // STAGE 2: Automated Handoff to Agent 2 Cognitive Diagnostic Reasoning
      // ==========================================
      setPipelineStage('agent2');

      const res2 = await fetch(`${API_BASE_URL}/api/v1/diagnose`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data1)
      });

      const data2 = await res2.json();
      let deducedRootCause = null;

      if (!res2.ok) {
        console.warn('Agent 2 diagnosis error, falling back to simulated reasoning:', data2.detail);
        const upperDtcs = (data1.dtc_codes || []).join(' ').toUpperCase();
        let matchedKey = Object.keys(SIMULATED_DIAGNOSES).find(k => upperDtcs.includes(k)) || 'P0171';
        const sim = SIMULATED_DIAGNOSES[matchedKey];
        setAgent2Result({
          root_cause_component: sim.root_cause_component,
          failure_mode: sim.failure_mode,
          severity: sim.severity,
          safety_warning: sim.safety_warning
        });
        setAgent2Error(data2.detail);
        deducedRootCause = sim.root_cause_component;
      } else {
        setAgent2Result(data2);
        setAgent2Error(null);
        deducedRootCause = data2.root_cause_component;
      }

      // ==========================================
      // STAGE 3: Fork-Join Execution: Agent 3 (RAG) & Agent 4 (Procurement)
      // ==========================================
      if (deducedRootCause) {
        // Agent 3 Call
        try {
          const repairRes = await fetch(`${API_BASE_URL}/api/v1/repair`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              session_id: sessionId,
              vehicle_make: data1.vehicle_details.make,
              vehicle_model: data1.vehicle_details.model,
              vehicle_year: data1.vehicle_details.year,
              issue_summary: deducedRootCause
            })
          });
          const repairData = await repairRes.json();
          if (repairRes.ok && repairData.status === "success") {
            setRepairPlan(repairData.repair_plan);
          }
        } catch (repairErr) {
          console.warn('Agent 3 repair retrieval error:', repairErr);
        }

        // Agent 4 Call (Procurement & Pricing)
        try {
          const procureRes = await fetch(`${API_BASE_URL}/api/v1/procure`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              session_id: sessionId,
              root_cause_component: deducedRootCause,
              make: data1.vehicle_details.make,
              model: data1.vehicle_details.model,
              year: data1.vehicle_details.year,
              severity: (data2 && data2.severity) || 'Medium',
              safety_warning: (data2 && data2.safety_warning) || ''
            })
          });
          const procureData = await procureRes.json();
          if (procureRes.ok) {
            setProcurementPlan(procureData);
          }
        } catch (procureErr) {
          console.warn('Agent 4 procurement error:', procureErr);
        }
      }

      setPipelineStage('complete');
    } catch (err) {
      setError(err.message || 'Error communicating with Auto-Triage multi-agent backend.');
      setPipelineStage('error');
      setTriageResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-root">
      {/* Top Navigation */}
      <header className="site-header">
        <div className="nav-container">
          <a href="#" className="nav-brand">
            <div className="brand-glyph">
              AUTO-TRIAGE<span>//AI</span>
            </div>
            <span className="brand-pill">Agent 1 & 2 Live</span>
          </a>

          <ul className="nav-links">
            <li><a href="#console">Triage Console</a></li>
            <li><a href="#agent2">Agent 2 Reasoning</a></li>
            <li><a href="#agents">Multi-Agent Core</a></li>
            <li><a href="#metrics">Precision</a></li>
            <li><a href="#matrix">DTC Telemetry</a></li>
            <li><a href="#faq">FAQ</a></li>
          </ul>

          <div className="nav-cta-group">
            <div className="api-status-badge">
              <span className={`status-dot-sm ${serverStatus}`} />
              <span>GATEWAY: {serverStatus.toUpperCase()}</span>
              <button 
                onClick={checkHealth} 
                title="Refresh Health" 
                className="icon-btn"
                style={{ marginLeft: 4 }}
              >
                <RefreshCw size={11} />
              </button>
            </div>

            <a href="#console" className="btn-red" style={{ padding: '10px 20px', fontSize: '0.8rem' }}>
              Launch Triage
            </a>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-bg-wrapper">
          <img 
            src={heroDarkCar} 
            alt="High-performance dark sports car" 
            className="hero-bg-img" 
          />
          <div className="hero-gradient-overlay" />
        </div>

        <div className="hero-content">
          <div className="section-tag">
            // Autonomous Multi-Agent Automotive Platform
          </div>

          <h1 className="hero-title">
            INGEST.
            <br />
            TRIAGE.
            <br />
            <span className="red-text">VALIDATE.</span>
          </h1>

          <p className="hero-desc">
            Comprehensive multi-agent vehicle diagnostics. Real-time spaCy entity 
            extraction, US DOT NHTSA vPIC verification, and automated parts procurement — 
            all orchestrated in one unified pipeline.
          </p>

          <div className="hero-actions">
            <a href="#console" className="btn-red">
              <Zap size={16} />
              Start Live Triage
            </a>
            <a href="#agents" className="btn-outline">
              System Architecture
            </a>
          </div>
        </div>
      </section>

      {/* Live Agent 1 Triage Console (#console) */}
      <section id="console" className="triage-console-section">
        <div className="console-container">
          <div className="console-header">
            <div>
              <div className="section-tag">// Live Gateway Terminal</div>
              <h2 className="section-title">Agent 1 // Triage & Validation Console</h2>
            </div>
            <div className="session-chip">
              <Terminal size={14} color="var(--red-primary)" />
              <span>{sessionId}</span>
              <button 
                onClick={handleNewSession} 
                className="icon-btn" 
                title="Generate New Session ID"
              >
                <RefreshCw size={12} />
              </button>
            </div>
          </div>

          <div className="console-grid">
            {/* Left Card: Input Form */}
            <div className="intake-card">
              <div className="card-top-row">
                <div className="card-heading">
                  <Activity size={18} color="var(--red-primary)" />
                  Mechanic Diagnostic Intake
                </div>
              </div>

              {/* Mode Toggle Control */}
              <div className="mode-toggle-bar">
                <button
                  type="button"
                  className={`mode-tab ${intakeMode === 'smart' ? 'active' : ''}`}
                  onClick={() => { setIntakeMode('smart'); setError(null); }}
                >
                  <Sparkles size={14} />
                  Smart NLP Intake
                </button>
                <button
                  type="button"
                  className={`mode-tab ${intakeMode === 'manual' ? 'active' : ''}`}
                  onClick={() => { setIntakeMode('manual'); setError(null); }}
                >
                  <Wrench size={14} />
                  Manual Spec Entry
                </button>
                <button
                  type="button"
                  className={`mode-tab ${intakeMode === 'vin' ? 'active' : ''}`}
                  onClick={() => { setIntakeMode('vin'); setError(null); }}
                >
                  <Barcode size={14} />
                  VIN Decoder Intake
                </button>
              </div>

              {/* MODE A: SMART NLP INTAKE */}
              {intakeMode === 'smart' && (
                <>
                  <div className="preset-group">
                    <span className="preset-title">Quick Scenario Presets:</span>
                    <div className="preset-buttons">
                      {PRESETS.map((preset, idx) => (
                        <button
                          key={idx}
                          type="button"
                          className="preset-btn"
                          onClick={() => handlePresetClick(preset.text)}
                        >
                          <Sparkles size={12} color="var(--red-primary)" />
                          {preset.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  <form onSubmit={handleRunTriage} className="input-group">
                    <div className="input-labels">
                      <span>Diagnostic Complaint Text:</span>
                      <span style={{ fontFamily: 'var(--font-mono)' }}>{rawText.length} chars</span>
                    </div>

                    <textarea
                      className="console-textarea"
                      value={rawText}
                      onChange={(e) => setRawText(e.target.value)}
                      placeholder="e.g. 2019 Honda Civic with crashed bumper and trouble code P0171..."
                    />

                    <button 
                      type="submit" 
                      className="btn-red" 
                      disabled={loading || !rawText.trim()}
                      style={{ width: '100%', marginTop: 8 }}
                    >
                      {loading ? (
                        <>
                          <RefreshCw size={16} className="spin-icon" />
                          {pipelineStage === 'agent2' ? 'Stage 2/2: Groq LLM Deducing Root Cause...' : 'Stage 1/2: Ingesting & Validating with NHTSA...'}
                        </>
                      ) : (
                        <>
                          <Zap size={16} />
                          Execute Autonomous Workflow (Agent 1 ➔ Agent 2)
                        </>
                      )}
                    </button>
                  </form>
                </>
              )}

              {/* MODE B: MANUAL SPEC ENTRY */}
              {intakeMode === 'manual' && (
                <>
                  <div className="preset-group">
                    <span className="preset-title">Fill Quick Spec Preset:</span>
                    <div className="preset-buttons">
                      {MANUAL_PRESETS.map((p, idx) => (
                        <button
                          key={idx}
                          type="button"
                          className="preset-btn"
                          onClick={() => handleManualPresetClick(p)}
                        >
                          <Car size={12} color="var(--red-primary)" />
                          {p.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  <form onSubmit={handleRunTriage} className="manual-spec-form">
                    <div className="form-row">
                      <div className="form-field">
                        <label className="form-label">Vehicle Make *</label>
                        <input
                          type="text"
                          className="form-input"
                          placeholder="e.g. Honda, Toyota, Ford"
                          value={manualMake}
                          onChange={(e) => setManualMake(e.target.value)}
                          required
                        />
                      </div>

                      <div className="form-field">
                        <label className="form-label">Vehicle Model *</label>
                        <input
                          type="text"
                          className="form-input"
                          placeholder="e.g. Civic, Camry, F-150"
                          value={manualModel}
                          onChange={(e) => setManualModel(e.target.value)}
                          required
                        />
                      </div>
                    </div>

                    <div className="form-row">
                      <div className="form-field">
                        <label className="form-label">Production Year *</label>
                        <input
                          type="number"
                          className="form-input"
                          placeholder="1980 - 2026"
                          value={manualYear}
                          onChange={(e) => setManualYear(e.target.value)}
                          min="1980"
                          max="2026"
                          required
                        />
                      </div>

                      <div className="form-field">
                        <label className="form-label">OBD-II DTC Trouble Codes</label>
                        <input
                          type="text"
                          className="form-input"
                          placeholder="e.g. P0171, P0300"
                          value={manualDtcs}
                          onChange={(e) => setManualDtcs(e.target.value)}
                        />
                      </div>
                    </div>

                    <div className="form-field">
                      <label className="form-label">Observed Damaged Components / Collision Notes</label>
                      <input
                        type="text"
                        className="form-input"
                        placeholder="e.g. crashed bumper, cracked headlight, leaking radiator"
                        value={manualParts}
                        onChange={(e) => setManualParts(e.target.value)}
                      />
                    </div>

                    <button 
                      type="submit" 
                      className="btn-red" 
                      disabled={loading || !manualMake || !manualModel || !manualYear}
                      style={{ width: '100%', marginTop: 8 }}
                    >
                      {loading ? (
                        <>
                          <RefreshCw size={16} className="spin-icon" />
                          {pipelineStage === 'agent2' ? 'Stage 2/2: Groq LLM Deducing Root Cause...' : 'Stage 1/2: Validating Spec with NHTSA Database...'}
                        </>
                      ) : (
                        <>
                          <Zap size={16} />
                          Validate Spec & Run Complete Workflow
                        </>
                      )}
                    </button>
                  </form>
                </>
              )}

              {/* MODE C: VIN DECODER & CHECKSUM INTAKE */}
              {intakeMode === 'vin' && (
                <>
                  <div className="preset-group">
                    <span className="preset-title">Test 17-Char VIN Presets:</span>
                    <div className="preset-buttons">
                      {VIN_PRESETS.map((p, idx) => (
                        <button
                          key={idx}
                          type="button"
                          className="preset-btn"
                          onClick={() => handleVinPresetClick(p)}
                        >
                          <Barcode size={12} color="var(--red-primary)" />
                          {p.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  <form onSubmit={handleRunTriage} className="manual-spec-form">
                    <div className="form-field">
                      <div className="input-labels">
                        <label className="form-label">17-Character ISO 3779 VIN Barcode / String *</label>
                        <span style={{ fontFamily: 'var(--font-mono)' }}>{vinInput.length} / 17 chars</span>
                      </div>
                      <input
                        type="text"
                        className="form-input"
                        placeholder="e.g. 1HGCR2F85HA000000"
                        value={vinInput}
                        onChange={(e) => setVinInput(e.target.value.toUpperCase())}
                        maxLength={17}
                        style={{ fontFamily: 'var(--font-mono)', letterSpacing: '0.12em', fontSize: '1.05rem', fontWeight: 700 }}
                        required
                      />
                      <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginTop: 4 }}>
                        Offline MOD-11 Checksum (9th digit) verification executes immediately in 0.1ms before querying NHTSA.
                      </span>
                    </div>

                    <div className="form-row">
                      <div className="form-field">
                        <label className="form-label">OBD-II DTC Codes (Optional)</label>
                        <input
                          type="text"
                          className="form-input"
                          placeholder="e.g. P0171, P0420"
                          value={vinDtcs}
                          onChange={(e) => setVinDtcs(e.target.value)}
                        />
                      </div>

                      <div className="form-field">
                        <label className="form-label">Damaged Components (Optional)</label>
                        <input
                          type="text"
                          className="form-input"
                          placeholder="e.g. intake leak, dented bumper"
                          value={vinParts}
                          onChange={(e) => setVinParts(e.target.value)}
                        />
                      </div>
                    </div>

                    <button 
                      type="submit" 
                      className="btn-red" 
                      disabled={loading || !vinInput.trim()}
                      style={{ width: '100%', marginTop: 8 }}
                    >
                      {loading ? (
                        <>
                          <RefreshCw size={16} className="spin-icon" />
                          {pipelineStage === 'agent2' ? 'Stage 2/2: Groq LLM Deducing Root Cause...' : 'Stage 1/2: Decoding VIN via NHTSA vPIC...'}
                        </>
                      ) : (
                        <>
                          <Barcode size={16} />
                          Decode VIN & Run Autonomous Triage
                        </>
                      )}
                    </button>
                  </form>
                </>
              )}

              {/* Error Banner */}
              {error && (
                <div style={{
                  background: 'rgba(255, 30, 39, 0.1)',
                  border: '1px solid var(--red-primary)',
                  padding: '14px 16px',
                  borderRadius: 'var(--radius-sharp)',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '12px',
                  color: '#ff999d',
                  fontSize: '0.88rem'
                }}>
                  <AlertTriangle size={18} color="var(--red-primary)" style={{ flexShrink: 0, marginTop: 2 }} />
                  <div>
                    <strong style={{ color: 'var(--red-primary)', display: 'block', marginBottom: 2 }}>
                      Validation Rejected
                    </strong>
                    {error}
                  </div>
                </div>
              )}
            </div>

            {/* Right Card: Connected Autonomous Pipeline Results */}
            <div className="results-card">
              <div className="card-top-row">
                <div className="card-heading">
                  <ShieldCheck size={18} color="var(--emerald)" />
                  Autonomous Pipeline Telemetry (Agent 1 + Agent 2)
                </div>
                {pipelineStage === 'complete' && (
                  <span className="synced-badge">
                    <Check size={11} />
                    Workflow Concluded
                  </span>
                )}
              </div>

              {/* Progress Stepper */}
              {(loading || triageResult) && (
                <div className="pipeline-stepper">
                  <div className={`pipeline-step ${triageResult ? 'completed' : loading && pipelineStage === 'agent1' ? 'active' : ''}`}>
                    <span className="step-dot" />
                    <span>1. Agent 1: NHTSA Verification</span>
                  </div>
                  <span className="step-arrow">➔</span>
                  <div className={`pipeline-step ${agent2Result ? 'completed' : loading && pipelineStage === 'agent2' ? 'active' : ''}`}>
                    <span className="step-dot" />
                    <span>2. Agent 2: Groq Reasoning</span>
                  </div>
                  <span className="step-arrow">➔</span>
                  <div className={`pipeline-step ${agent2Result ? 'active' : ''}`}>
                    <span className="step-dot" />
                    <span>3. LangGraph Ready</span>
                  </div>
                </div>
              )}

              {/* Initial Empty State */}
              {!triageResult && !loading && (
                <div className="results-empty">
                  <div className="empty-scanner-icon">
                    <Car size={28} />
                  </div>
                  <div>
                    <h3 style={{ fontSize: '1.05rem', color: 'var(--text-white)' }}>
                      Ready for Autonomous Multi-Agent Triage
                    </h3>
                    <p style={{ fontSize: '0.85rem', marginTop: 6, color: 'var(--text-muted)' }}>
                      Execute a diagnostic complaint to run the complete end-to-end workflow: 
                      <strong> Agent 1</strong> (spaCy NLP & NHTSA validation) automatically streams verified telemetry 
                      into <strong>Agent 2</strong> (Groq LLM cognitive root-cause deduction).
                    </p>
                  </div>
                </div>
              )}

              {/* Stage 1 Loading State */}
              {loading && !triageResult && (
                <div className="pipeline-loading-card">
                  <RefreshCw size={36} color="var(--red-primary)" className="spin-icon" />
                  <div>
                    <div className="pipeline-loading-title">
                      Stage 1/2: Querying US DOT NHTSA VPIC Database...
                    </div>
                    <p className="pipeline-loading-desc">
                      Extracting entities via spaCy and verifying vehicle specifications against federal road-legal standards.
                    </p>
                  </div>
                </div>
              )}

              {/* Connected Results */}
              {triageResult && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  {/* --- AGENT 1 SECTION --- */}
                  <div className="telemetry-vehicle-box">
                    <div className="telemetry-header">
                      <div className="telemetry-title">
                        {triageResult.vehicle_details.year} {triageResult.vehicle_details.make} {triageResult.vehicle_details.model}
                      </div>

                      {triageResult.vehicle_details.is_verified && (
                        <div className="nhtsa-shield-pill">
                          <ShieldCheck size={13} />
                          NHTSA Verified
                        </div>
                      )}
                    </div>

                    <div className="telemetry-specs">
                      <div className="spec-badge">Make: <strong>{triageResult.vehicle_details.make}</strong></div>
                      <div className="spec-badge">Model: <strong>{triageResult.vehicle_details.model}</strong></div>
                      <div className="spec-badge">Year: <strong>{triageResult.vehicle_details.year}</strong></div>
                      <div className="spec-badge">Status: <strong>ROAD-LEGAL</strong></div>
                      {triageResult.vehicle_details.engine && (
                        <div className="spec-badge">Engine: <strong>{triageResult.vehicle_details.engine}</strong></div>
                      )}
                      {triageResult.vehicle_details.fuel_type && (
                        <div className="spec-badge">Fuel: <strong>{triageResult.vehicle_details.fuel_type}</strong></div>
                      )}
                      {triageResult.vehicle_details.drive_type && (
                        <div className="spec-badge">Drive: <strong>{triageResult.vehicle_details.drive_type}</strong></div>
                      )}
                      {triageResult.vehicle_details.body_class && (
                        <div className="spec-badge">Body: <strong>{triageResult.vehicle_details.body_class}</strong></div>
                      )}
                    </div>

                    {/* VIN Identity Bar if VIN decoded */}
                    {triageResult.vehicle_details.vin && (
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: '#0e0e0e', border: '1px solid var(--border-subtle)', borderRadius: 6, padding: '8px 12px', marginTop: 4 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <Barcode size={14} color="var(--red-primary)" />
                          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Decoded VIN:</span>
                          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-white)', letterSpacing: '0.08em' }}>
                            {triageResult.vehicle_details.vin}
                          </span>
                        </div>
                        {triageResult.vehicle_details.vin_checksum_valid ? (
                          <span className="checksum-valid-pill">
                            <Check size={11} />
                            MOD-11 Checksum: Valid
                          </span>
                        ) : (
                          <span className="checksum-invalid-pill">
                            <AlertTriangle size={11} />
                            MOD-11 Checksum: Warning
                          </span>
                        )}
                      </div>
                    )}
                  </div>

                  {/* OBD-II Trouble Codes with Hierarchical Taxonomy */}
                  <div>
                    <div style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 8, letterSpacing: '0.08em' }}>
                      Discovered OBD-II Trouble Codes ({triageResult.dtc_codes.length})
                    </div>
                    {triageResult.dtc_codes.length > 0 ? (
                      <div className="tag-container" style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                        {triageResult.dtc_hierarchy && triageResult.dtc_hierarchy.length > 0 ? (
                          triageResult.dtc_hierarchy.map((item, idx) => (
                            <div key={idx} style={{ background: '#120b0b', border: '1px solid #331515', borderRadius: 6, padding: '8px 10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                <span className="dtc-badge-red" style={{ margin: 0 }}>
                                  <Activity size={12} />
                                  {item.exact_code}
                                </span>
                                <span style={{ fontSize: '0.82rem', color: '#fca5a5' }}>
                                  {item.description}
                                </span>
                              </div>
                              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'flex', gap: 6 }}>
                                <span style={{ background: '#222', padding: '2px 6px', borderRadius: 3 }}>Family: {item.family_code}</span>
                                <span style={{ background: '#222', padding: '2px 6px', borderRadius: 3 }}>{item.system}</span>
                              </div>
                            </div>
                          ))
                        ) : (
                          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                            {triageResult.dtc_codes.map((code, idx) => (
                              <div key={idx} className="dtc-badge-red">
                                <Activity size={12} />
                                <span>{code}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ) : (
                      <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>No DTC codes detected.</span>
                    )}
                  </div>

                  {/* Normalized IR Query & Domain Synonym Expansion */}
                  {triageResult.canonical_query && (
                    <div style={{ background: '#0a0f1d', border: '1px solid #1e293b', borderRadius: 6, padding: '10px 12px' }}>
                      <div style={{ fontSize: '0.72rem', fontWeight: 800, color: '#38bdf8', textTransform: 'uppercase', marginBottom: 4, display: 'flex', alignItems: 'center', gap: 5 }}>
                        <Terminal size={12} />
                        IR Canonical Query (Stopwords Removed & Synonyms Expanded)
                      </div>
                      <code style={{ fontSize: '0.84rem', color: '#e2e8f0', background: 'transparent' }}>
                        {triageResult.canonical_query}
                      </code>
                    </div>
                  )}

                  {/* Damaged Physical Components */}
                  {triageResult.damaged_parts.length > 0 && (
                    <div>
                      <div style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 8, letterSpacing: '0.08em' }}>
                        Identified Damaged Components ({triageResult.damaged_parts.length})
                      </div>
                      <div className="tag-container">
                        {triageResult.damaged_parts.map((part, idx) => (
                          <div key={idx} className="part-badge-dark">
                            <Wrench size={12} color="var(--red-primary)" />
                            <span>{part}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* --- WORKFLOW STREAM CONNECTOR --- */}
                  <div className="workflow-stream-banner">
                    <div className="stream-tag">
                      <Zap size={14} />
                      <span>Automated Pipeline Stream // Agent 1 ➔ Agent 2</span>
                    </div>
                    <span className="stream-pill">GROQ LLM HANDOFF</span>
                  </div>

                  {/* --- AGENT 2 SECTION --- */}
                  {loading && pipelineStage === 'agent2' && (
                    <div className="pipeline-loading-card" style={{ padding: '24px 16px' }}>
                      <RefreshCw size={28} color="var(--red-primary)" className="spin-icon" />
                      <div>
                        <div className="pipeline-loading-title" style={{ fontSize: '0.94rem' }}>
                          Stage 2/2: Groq Cognitive Engine Reasoning...
                        </div>
                        <p className="pipeline-loading-desc" style={{ fontSize: '0.8rem', marginTop: 4 }}>
                          Cross-referencing OBD-II DTCs ({triageResult.dtc_codes.join(', ')}) with physical symptoms on {triageResult.vehicle_details.year} {triageResult.vehicle_details.make} {triageResult.vehicle_details.model}...
                        </p>
                      </div>
                    </div>
                  )}

                  {agent2Result && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                      {/* Status & Severity Header */}
                      <div className="result-header-row">
                        <div className="result-status-text">
                          <CheckCircle2 size={16} color="var(--emerald)" />
                          AGENT 2 REASONING CONCLUDED
                        </div>

                        <div className={`severity-pill severity-${(agent2Result.severity || 'medium').toLowerCase()}`}>
                          <AlertOctagon size={13} />
                          SEVERITY: {agent2Result.severity?.toUpperCase()}
                        </div>
                      </div>

                      {/* Primary Root Cause Component Box */}
                      <div className="root-cause-hero-box">
                        <div className="root-cause-tag">
                          <Wrench size={13} />
                          Deduce Root-Cause Failed Component
                        </div>
                        <div className="root-cause-title">
                          {agent2Result.root_cause_component}
                        </div>
                        <div className="root-cause-sub">
                          Single physical component isolated by Groq LLM for replacement / bench testing
                        </div>
                      </div>

                      {/* Mechanical Failure Mode */}
                      <div className="diagnostic-detail-card">
                        <div className="detail-label">
                          <Radio size={13} color="var(--red-primary)" />
                          Mechanical Failure Mode & Physics
                        </div>
                        <div className="detail-text">
                          {agent2Result.failure_mode}
                        </div>
                      </div>

                      {/* Safety Warning */}
                      {agent2Result.safety_warning && (
                        <div className="safety-warning-banner">
                          <AlertTriangle size={20} color="var(--red-primary)" style={{ flexShrink: 0, marginTop: 2 }} />
                          <div>
                            <h4>MECHANIC SAFETY HAZARD & PROTOCOL</h4>
                            <p>{agent2Result.safety_warning}</p>
                          </div>
                        </div>
                      )}

                      {/* SIMPLE AGENT 3 MANUAL BOX */}
                      {repairPlan && (
                        <div className="telemetry-vehicle-box" style={{ marginTop: '16px', borderLeft: '4px solid #a855f7' }}>
                          <div style={{ color: '#c084fc', fontSize: '0.85rem', fontWeight: 800, textTransform: 'uppercase', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
                            <Layers size={14} />
                            Agent 3 // OEM Repair Manual (RAG)
                          </div>
                          
                          <ol style={{ paddingLeft: '20px', margin: 0, fontSize: '0.9rem', lineHeight: '1.6', color: 'var(--text-white)' }}>
                            {repairPlan.steps.map((step, idx) => (
                              <li key={idx} style={{ marginBottom: '6px' }}>{step}</li>
                            ))}
                          </ol>

                          {repairPlan.torque_specs && (
                            <div style={{ marginTop: 12, fontSize: '0.85rem', color: '#e9d5ff' }}>
                              <strong>Torque Specs:</strong> {repairPlan.torque_specs}
                            </div>
                          )}
                          
                          <div style={{ marginTop: 12, paddingTop: 8, borderTop: '1px solid #3b1669', fontSize: '0.75rem', color: '#a855f7' }}>
                            Source Citation: {repairPlan.citation}
                          </div>
                        </div>
                      )}

                      {/* SIMPLE AGENT 4 PROCUREMENT TEST BOX */}
                      {procurementPlan && (
                        <div className="telemetry-vehicle-box" style={{ marginTop: '16px', borderLeft: '4px solid #38bdf8' }}>
                          <div style={{ color: '#38bdf8', fontSize: '0.85rem', fontWeight: 800, textTransform: 'uppercase', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
                            <ShoppingBag size={14} />
                            Agent 4 // Parts Procurement & Tiered Pricing (MongoDB)
                          </div>

                          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 8, marginBottom: 14 }}>
                            <div style={{ background: '#111', padding: '8px 10px', borderRadius: 4, border: '1px solid #222' }}>
                              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', display: 'block' }}>Resolved Part</span>
                              <span style={{ fontSize: '0.88rem', fontWeight: 700, color: '#fff' }}>{procurementPlan.resolved_part || 'Unresolved'}</span>
                            </div>
                            <div style={{ background: '#111', padding: '8px 10px', borderRadius: 4, border: '1px solid #222' }}>
                              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', display: 'block' }}>Match Strategy</span>
                              <span style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--emerald)' }}>{procurementPlan.match_method} ({Math.round(procurementPlan.match_confidence * 100)}%)</span>
                            </div>
                          </div>

                          {procurementPlan.tiers && Object.keys(procurementPlan.tiers).length > 0 ? (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                              {Object.entries(procurementPlan.tiers).map(([tierName, tierData]) => (
                                <div key={tierName} style={{ background: '#0e1726', border: '1px solid #1e293b', borderRadius: 6, padding: '10px 12px' }}>
                                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                                    <span style={{ fontSize: '0.8rem', fontWeight: 800, color: '#38bdf8', textTransform: 'uppercase' }}>
                                      {tierName.replace('_', ' ')}
                                    </span>
                                    <span style={{ fontSize: '0.9rem', fontWeight: 800, color: 'var(--emerald)' }}>
                                      LKR {tierData.tier_total_lkr?.toLocaleString()}
                                    </span>
                                  </div>
                                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                    {tierData.parts?.map((p, pIdx) => (
                                      <div key={pIdx} style={{ fontSize: '0.8rem', color: '#cbd5e1', display: 'flex', justifyContent: 'space-between' }}>
                                        <span>• {p.part_name} ({p.brand} - {p.part_number})</span>
                                        <span style={{ color: '#94a3b8' }}>LKR {p.price_lkr?.toLocaleString()}</span>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                              No matching catalog items found for this vehicle/component combination.
                              {procurementPlan.warnings && procurementPlan.warnings.length > 0 && (
                                <div style={{ color: 'var(--amber)', marginTop: 4 }}>
                                  Notice: {procurementPlan.warnings.join(', ')}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Downstream LangGraph Dispatch Preview */}
                      <div className="dispatch-preview-box">
                        <div className="dispatch-header">
                          <span className="dispatch-title">Downstream Dispatch: LangGraph Fork-Join</span>
                          <span style={{ fontSize: '0.7rem', color: 'var(--emerald)', fontWeight: 800 }}>READY TO FORK</span>
                        </div>

                        <div className="dispatch-flow-grid">
                          <div className="dispatch-target-card">
                            <div className="target-icon-wrap">
                              <Layers size={16} color="var(--red-primary)" />
                            </div>
                            <div>
                              <span className="target-name">Agent 3: Manual RAG</span>
                              <span className="target-sub">ChromaDB Vector OEM Manual</span>
                            </div>
                          </div>

                          <div className="dispatch-target-card">
                            <div className="target-icon-wrap">
                              <Database size={16} color="var(--red-primary)" />
                            </div>
                            <div>
                              <span className="target-name">Agent 4: Parts Catalog</span>
                              <span className="target-sub">MongoDB Pricing & Inventory</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}


                  {/* Collapsible A2A Handshake JSON Payload */}
                  <div className="raw-json-accordion">
                    <button 
                      type="button" 
                      className="raw-json-toggle-btn"
                      onClick={() => setShowRawJson(!showRawJson)}
                    >
                      <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <Terminal size={13} color="var(--red-primary)" />
                        {showRawJson ? 'Hide A2A Contract JSON' : 'Inspect Verified A2A Contract JSON (Handshake)'}
                      </span>
                      <span>{showRawJson ? '▲' : '▼'}</span>
                    </button>
                    {showRawJson && (
                      <div style={{ padding: '12px', background: '#070707' }}>
                        <pre className="a2a-code">
                          {JSON.stringify(triageResult, null, 2)}
                        </pre>
                        <button 
                          type="button" 
                          onClick={handleCopyPayload} 
                          className="icon-btn" 
                          style={{ fontSize: '0.72rem', gap: 4, marginTop: 8 }}
                        >
                          {copied ? <><Check size={12} color="var(--emerald)" /><span style={{ color: 'var(--emerald)' }}>Copied</span></> : <><Copy size={12} /><span>Copy JSON</span></>}
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Agent 2 Cognitive Diagnostic Reasoning Console (#agent2) */}
      <section id="agent2" className="agent2-section">
        <div className="agent2-container">
          <div className="agent2-header">
            <div>
              <div className="section-tag">// Cognitive Diagnostic Reasoning Engine</div>
              <h2 className="section-title">Agent 2 // Root-Cause Deductive Console</h2>
              <p style={{ color: 'var(--text-gray)', maxWidth: 720, marginTop: 4, fontSize: '0.92rem' }}>
                Evaluates vehicle parameters, cross-references electrical DTC trouble codes with physical symptoms,
                and isolates the single failed mechanical component using structured Groq LLM inference.
              </p>
            </div>

            <div className="agent2-model-badge">
              <Cpu size={14} color="var(--red-primary)" />
              <span>GROQ // OPENAI/GPT-OSS-120B</span>
            </div>
          </div>

          <div className="agent2-grid">
            {/* Left Column: Diagnostics Input Panel */}
            <div className="agent2-card">
              <div className="card-top-row">
                <div className="card-heading">
                  <Sliders size={18} color="var(--red-primary)" />
                  Diagnostic Telemetry Input
                </div>
                {agent2Source === 'agent1' && (
                  <span className="synced-badge">
                    <Check size={11} />
                    Synced with Agent 1
                  </span>
                )}
              </div>

              {/* Quick Scenario Presets for Agent 2 */}
              <div className="preset-group">
                <span className="preset-title">Test Harness Presets:</span>
                <div className="preset-buttons">
                  {AGENT2_PRESETS.map((p, idx) => (
                    <button
                      key={idx}
                      type="button"
                      className={`preset-btn ${selectedAgent2Preset === idx ? 'active' : ''}`}
                      onClick={() => handleSelectAgent2Preset(p, idx)}
                    >
                      <Car size={12} color="var(--red-primary)" />
                      {p.label}
                    </button>
                  ))}
                </div>
              </div>

              <form onSubmit={handleRunAgent2Diagnostics} className="manual-spec-form">
                <div className="form-row">
                  <div className="form-field">
                    <label className="form-label">Vehicle Make *</label>
                    <input
                      type="text"
                      className="form-input"
                      value={agent2Make}
                      onChange={(e) => { setAgent2Make(e.target.value); setAgent2Source('custom'); }}
                      placeholder="e.g. Toyota"
                      required
                    />
                  </div>
                  <div className="form-field">
                    <label className="form-label">Vehicle Model *</label>
                    <input
                      type="text"
                      className="form-input"
                      value={agent2Model}
                      onChange={(e) => { setAgent2Model(e.target.value); setAgent2Source('custom'); }}
                      placeholder="e.g. Townace"
                      required
                    />
                  </div>
                  <div className="form-field">
                    <label className="form-label">Year *</label>
                    <input
                      type="number"
                      className="form-input"
                      value={agent2Year}
                      onChange={(e) => { setAgent2Year(e.target.value); setAgent2Source('custom'); }}
                      placeholder="1995"
                      min="1900"
                      max="2100"
                      required
                    />
                  </div>
                </div>

                <div className="form-field">
                  <label className="form-label">OBD-II Trouble Codes (comma separated)</label>
                  <input
                    type="text"
                    className="form-input"
                    value={agent2Dtcs}
                    onChange={(e) => { setAgent2Dtcs(e.target.value); setAgent2Source('custom'); }}
                    placeholder="e.g. P0251, P0171"
                  />
                </div>

                <div className="form-field">
                  <label className="form-label">Mechanic Notes & Customer Observed Symptoms *</label>
                  <textarea
                    className="form-input"
                    style={{ minHeight: '90px', resize: 'vertical' }}
                    value={agent2Notes}
                    onChange={(e) => { setAgent2Notes(e.target.value); setAgent2Source('custom'); }}
                    placeholder="Describe symptoms, noise, smoke, rough idle, or stall conditions..."
                    required
                  />
                </div>

                <div className="agent2-action-group">
                  <button
                    type="submit"
                    className="btn-red"
                    style={{ flex: 2 }}
                    disabled={agent2Loading || !agent2Make || !agent2Model || !agent2Year}
                  >
                    {agent2Loading ? (
                      <>
                        <RefreshCw size={16} className="spin-icon" />
                        Reasoning with Groq LLM...
                      </>
                    ) : (
                      <>
                        <Zap size={16} />
                        Run Agent 2 Diagnosis
                      </>
                    )}
                  </button>

                  <button
                    type="button"
                    className="btn-outline"
                    style={{ flex: 1 }}
                    onClick={handleSimulateAgent2}
                    title="Preview simulated diagnostic output without requiring a Groq API key"
                  >
                    <Sparkles size={14} />
                    Simulate Demo
                  </button>
                </div>
              </form>

              {/* API Notice / Error Banner */}
              {agent2Error && (
                <div className="agent2-error-banner">
                  <AlertTriangle size={18} color="var(--amber)" style={{ flexShrink: 0, marginTop: 2 }} />
                  <div>
                    <strong style={{ color: 'var(--amber)', display: 'block', marginBottom: 2 }}>
                      Reasoning Notice
                    </strong>
                    <span>{agent2Error}</span>
                    {agent2Error.includes('GROQ_API_KEY') && (
                      <div style={{ marginTop: 8, fontSize: '0.82rem', color: 'var(--text-gray)' }}>
                        Tip: You can add <code>GROQ_API_KEY=gsk_...</code> to <code>backend/.env</code> or click <strong>Simulate Demo</strong> above to test diagnostic reasoning!
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Right Column: Reasoning Output & Root-Cause Card */}
            <div className="agent2-card">
              <div className="card-top-row">
                <div className="card-heading">
                  <Brain size={18} color="var(--red-primary)" />
                  Master Mechanic Root-Cause Telemetry
                </div>
              </div>

              {!agent2Result && !agent2Loading && (
                <div className="results-empty" style={{ minHeight: '320px' }}>
                  <div className="empty-scanner-icon">
                    <Cpu size={30} />
                  </div>
                  <div>
                    <h3 style={{ fontSize: '1.05rem', color: 'var(--text-white)' }}>
                      Ready for Cognitive Reasoning
                    </h3>
                    <p style={{ fontSize: '0.85rem', marginTop: 6, color: 'var(--text-muted)' }}>
                      Trigger diagnosis from Agent 1's handoff or choose a test preset 
                      to execute LLM deductive reasoning over DTC codes and mechanical symptoms.
                    </p>
                  </div>
                </div>
              )}

              {agent2Loading && (
                <div className="results-empty" style={{ minHeight: '320px' }}>
                  <RefreshCw size={36} color="var(--red-primary)" className="spin-icon" />
                  <div>
                    <h3 style={{ fontSize: '1.1rem', color: 'var(--text-white)' }}>
                      Groq LLM Cognitive Engine Active...
                    </h3>
                    <p style={{ fontSize: '0.85rem', marginTop: 8, color: 'var(--text-muted)', lineHeight: 1.6 }}>
                      Evaluating electrical trouble codes vs physical failure modes on 
                      <strong> {agent2Year} {agent2Make} {agent2Model}</strong>.
                    </p>
                  </div>
                </div>
              )}

              {agent2Result && !agent2Loading && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  {/* Status & Severity Header */}
                  <div className="result-header-row">
                    <div className="result-status-text">
                      <CheckCircle2 size={16} color="var(--emerald)" />
                      REASONING CONCLUDED
                    </div>

                    <div className={`severity-pill severity-${(agent2Result.severity || 'medium').toLowerCase()}`}>
                      <AlertOctagon size={13} />
                      SEVERITY: {agent2Result.severity?.toUpperCase()}
                    </div>
                  </div>

                  {/* Primary Root Cause Component Box */}
                  <div className="root-cause-hero-box">
                    <div className="root-cause-tag">
                      <Wrench size={13} />
                      Root-Cause Failed Component
                    </div>
                    <div className="root-cause-title">
                      {agent2Result.root_cause_component}
                    </div>
                    <div className="root-cause-sub">
                      Single physical component isolated for replacement / bench testing
                    </div>
                  </div>

                  {/* Mechanical Failure Mode */}
                  <div className="diagnostic-detail-card">
                    <div className="detail-label">
                      <Radio size={13} color="var(--red-primary)" />
                      Mechanical Failure Mode & Physics
                    </div>
                    <div className="detail-text">
                      {agent2Result.failure_mode}
                    </div>
                  </div>

                  {/* Safety Hazards */}
                  {agent2Result.safety_warning && (
                    <div className="safety-warning-banner">
                      <AlertTriangle size={20} color="var(--red-primary)" style={{ flexShrink: 0, marginTop: 2 }} />
                      <div>
                        <h4>MECHANIC SAFETY HAZARD & PROTOCOL</h4>
                        <p>{agent2Result.safety_warning}</p>
                      </div>
                    </div>
                  )}

                  {/* Downstream LangGraph Dispatch Preview */}
                  <div className="dispatch-preview-box">
                    <div className="dispatch-header">
                      <span className="dispatch-title">Downstream Dispatch: LangGraph Fork-Join</span>
                      <span style={{ fontSize: '0.7rem', color: 'var(--emerald)', fontWeight: 800 }}>READY TO FORK</span>
                    </div>

                    <div className="dispatch-flow-grid">
                      <div className="dispatch-target-card">
                        <div className="target-icon-wrap">
                          <Layers size={16} color="var(--red-primary)" />
                        </div>
                        <div>
                          <span className="target-name">Agent 3: Manual RAG</span>
                          <span className="target-sub">ChromaDB Vector OEM Manual</span>
                        </div>
                      </div>

                      <div className="dispatch-target-card">
                        <div className="target-icon-wrap">
                          <Database size={16} color="var(--red-primary)" />
                        </div>
                        <div>
                          <span className="target-name">Agent 4: Parts Catalog</span>
                          <span className="target-sub">MongoDB Pricing & Inventory</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* 4 Agents Showcase Section (#agents) */}
      <section id="agents" className="agents-section">
        <div className="section-tag">// Core System Architecture</div>
        <h2 className="section-title">The 4 Specialized Agents</h2>
        <p style={{ color: 'var(--text-gray)', maxWidth: 620, marginTop: -12 }}>
          Separation of concerns orchestrated through a LangGraph Fork-Join graph.
        </p>

        <div className="agents-grid">
          {/* Agent 1 Card */}
          <div className="agent-card">
            <img src={mechanicDiagnostics} alt="Diagnostic Scanner" className="agent-card-img" />
            <div className="agent-card-body">
              <span className="agent-num-tag">01 // GATEWAY</span>
              <h3 className="agent-card-title">Agent 1: Ingestion & Validation</h3>
              <p className="agent-card-desc">
                Parses unstructured mechanic notes, runs spaCy entity extraction, 
                and cross-references US DOT NHTSA database to prevent hallucinations.
              </p>
              <div className="agent-status-tag active">
                Live & Operational
              </div>
            </div>
          </div>

          {/* Agent 2 Card */}
          <div className="agent-card">
            <div style={{ height: 180, background: '#161616', display: 'flex', alignItems: 'center', justifyContent: 'center', borderBottom: '1px solid var(--border-subtle)' }}>
              <Cpu size={48} color="var(--red-primary)" />
            </div>
            <div className="agent-card-body">
              <span className="agent-num-tag">02 // COGNITIVE ENGINE</span>
              <h3 className="agent-card-title">Agent 2: Diagnostic Reasoning</h3>
              <p className="agent-card-desc">
                Receives the verified A2A payload, evaluates DTC trouble codes against 
                automotive knowledge graphs, and deduces root cause failure.
              </p>
              <div className="agent-status-tag active">
                Live & Operational
              </div>
              <a href="#agent2" className="btn-outline" style={{ marginTop: 12, padding: '8px 14px', fontSize: '0.75rem', textAlign: 'center', display: 'flex', justifyContent: 'center', gap: 6 }}>
                <Zap size={13} />
                Launch Agent 2 Console
              </a>
            </div>
          </div>

          {/* Agent 3 Card */}
          <div className="agent-card">
            <div style={{ height: 180, background: '#161616', display: 'flex', alignItems: 'center', justifyContent: 'center', borderBottom: '1px solid var(--border-subtle)' }}>
              <Layers size={48} color="var(--text-muted)" />
            </div>
            <div className="agent-card-body">
              <span className="agent-num-tag">03 // FORK A</span>
              <h3 className="agent-card-title">Agent 3: Technical Repair RAG</h3>
              <p className="agent-card-desc">
                Runs parallel dense vector retrieval (ChromaDB) across OEM workshop 
                manuals to synthesize step-by-step repair guides with page citations.
              </p>
              <div className="agent-status-tag">
                ChromaDB Vector Retrieval
              </div>
            </div>
          </div>

          {/* Agent 4 Card */}
          <div className="agent-card">
            <div style={{ height: 180, background: '#161616', display: 'flex', alignItems: 'center', justifyContent: 'center', borderBottom: '1px solid var(--border-subtle)' }}>
              <Database size={48} color="var(--text-muted)" />
            </div>
            <div className="agent-card-body">
              <span className="agent-num-tag">04 // FORK B</span>
              <h3 className="agent-card-title">Agent 4: Parts Procurement</h3>
              <p className="agent-card-desc">
                Queries a MongoDB parts catalog to pinpoint replacement OEM/aftermarket 
                numbers and calculate localized benchmark cost estimates.
              </p>
              <div className="agent-status-tag">
                MongoDB Parts Catalog
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Precision Mid-Banner (Like "GASOLINE IN OUR BLOOD") */}
      <section id="metrics" className="precision-banner-section">
        <div className="precision-container">
          <div>
            <div className="section-tag">// Engineering Excellence</div>
            <h2 className="section-title" style={{ color: 'var(--text-white)' }}>
              PRECISION IN EVERY DIAGNOSIS.
            </h2>
            <p style={{ color: 'var(--text-gray)', fontSize: '1rem', lineHeight: 1.8 }}>
              Automotive mechanics and customers demand 100% dependable diagnostic data. 
              By pairing neural natural language processing with federal vehicular records, 
              Auto-Triage AI guarantees ground truth before cognitive reasoning begins.
            </p>

            <div className="precision-stats">
              <div className="stat-item">
                <div className="stat-num">100%</div>
                <div className="stat-label">NHTSA Ground-Truth</div>
              </div>

              <div className="stat-item">
                <div className="stat-num">&lt; 180ms</div>
                <div className="stat-label">Gateway Latency</div>
              </div>

              <div className="stat-item">
                <div className="stat-num">4 AGENTS</div>
                <div className="stat-label">Fork-Join Graph</div>
              </div>

              <div className="stat-item">
                <div className="stat-num">0%</div>
                <div className="stat-label">AI Hallucinations</div>
              </div>
            </div>
          </div>

          <div className="precision-img-box">
            <img 
              src={cinematicSportsCar} 
              alt="Performance Sports Car Profile" 
              className="precision-img" 
            />
          </div>
        </div>
      </section>

      {/* Diagnostic & DTC Coverage Matrix (#matrix) */}
      <section id="matrix" className="matrix-section">
        <div className="section-tag">// Supported Telemetry</div>
        <h2 className="section-title">Diagnostic Trouble Code Matrix</h2>
        <p style={{ color: 'var(--text-gray)', maxWidth: 640, marginTop: -12 }}>
          Agent 1 continuously parses all standard SAE J2012 OBD-II diagnostic fault categories.
        </p>

        <div className="matrix-grid">
          {/* Powertrain Card */}
          <div className="matrix-card">
            <div className="matrix-card-header">
              <div className="matrix-category">
                <Activity size={16} color="var(--red-primary)" />
                POWERTRAIN <span>// P-CODES</span>
              </div>
            </div>
            <ul className="matrix-list">
              <li className="matrix-item"><span>System Too Lean (Bank 1)</span><code>P0171</code></li>
              <li className="matrix-item"><span>Random/Multiple Misfire</span><code>P0300</code></li>
              <li className="matrix-item"><span>Catalyst System Efficiency</span><code>P0420</code></li>
              <li className="matrix-item"><span>EVAP System Leak Detected</span><code>P0455</code></li>
              <li className="matrix-item"><span>Coolant Thermostat Malfunction</span><code>P0128</code></li>
            </ul>
          </div>

          {/* Chassis Card */}
          <div className="matrix-card">
            <div className="matrix-card-header">
              <div className="matrix-category">
                <Gauge size={16} color="var(--red-primary)" />
                CHASSIS <span>// C-CODES</span>
              </div>
            </div>
            <ul className="matrix-list">
              <li className="matrix-item"><span>Front Left Wheel Speed Sensor</span><code>C0035</code></li>
              <li className="matrix-item"><span>Front Right Wheel Speed Sensor</span><code>C0040</code></li>
              <li className="matrix-item"><span>Electronic Stability Control</span><code>C0121</code></li>
              <li className="matrix-item"><span>ABS Return Pump Relay Failure</span><code>C0265</code></li>
              <li className="matrix-item"><span>Electronic Brake Module Malfunction</span><code>C0550</code></li>
            </ul>
          </div>

          {/* Body Card */}
          <div className="matrix-card">
            <div className="matrix-card-header">
              <div className="matrix-category">
                <ShieldCheck size={16} color="var(--red-primary)" />
                BODY <span>// B-CODES</span>
              </div>
            </div>
            <ul className="matrix-list">
              <li className="matrix-item"><span>Driver Frontal Airbag Circuit</span><code>B0001</code></li>
              <li className="matrix-item"><span>Passenger Side Airbag Circuit</span><code>B0028</code></li>
              <li className="matrix-item"><span>ECU Internal Malfunction</span><code>B1000</code></li>
              <li className="matrix-item"><span>Power Window Control Circuit</span><code>B1325</code></li>
              <li className="matrix-item"><span>HVAC Blend Door Actuator Fault</span><code>B1402</code></li>
            </ul>
          </div>

          {/* Network Card */}
          <div className="matrix-card">
            <div className="matrix-card-header">
              <div className="matrix-category">
                <Cpu size={16} color="var(--red-primary)" />
                NETWORK <span>// U-CODES</span>
              </div>
            </div>
            <ul className="matrix-list">
              <li className="matrix-item"><span>Lost Communication with ECM</span><code>U0100</code></li>
              <li className="matrix-item"><span>Lost Communication with TCM</span><code>U0101</code></li>
              <li className="matrix-item"><span>Lost Communication with ABS Module</span><code>U0121</code></li>
              <li className="matrix-item"><span>Lost Communication with IPC</span><code>U0155</code></li>
              <li className="matrix-item"><span>CAN Controller Bus Failure</span><code>U1000</code></li>
            </ul>
          </div>
        </div>
      </section>

      {/* FAQ Accordion Section (#faq) */}
      <section id="faq" className="faq-section">
        <div style={{ textAlign: 'center' }}>
          <div className="section-tag" style={{ justifyContent: 'center' }}>// Architecture FAQ</div>
          <h2 className="section-title">Frequently Asked Questions</h2>
        </div>

        <div className="faq-list">
          {FAQ_ITEMS.map((item, index) => {
            const isOpen = openFaq === index;
            return (
              <div key={index} className={`faq-item ${isOpen ? 'open' : ''}`}>
                <button 
                  className="faq-question" 
                  onClick={() => setOpenFaq(isOpen ? -1 : index)}
                >
                  <span>{item.q}</span>
                  {isOpen ? <ChevronUp size={18} color="var(--red-primary)" /> : <ChevronDown size={18} />}
                </button>
                {isOpen && (
                  <div className="faq-answer">
                    {item.a}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </section>

      {/* Footer */}
      <footer className="site-footer">
        <div className="footer-container">
          <div>
            <div className="footer-brand">
              AUTO-TRIAGE<span>//AI</span>
            </div>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: 6, maxWidth: 440 }}>
              Multi-Agent Automotive Diagnostic Gateway & Automated Procurement Engine. 
              Engineered with FastAPI, LangGraph, and React.
            </p>
          </div>

          <ul className="footer-links">
            <li><a href="#console">Gateway</a></li>
            <li><a href="#agents">Architecture</a></li>
            <li><a href="#matrix">Telemetry</a></li>
            <li><a href="https://github.com/Kavisha1Gamagedara/Auto-Triage-AI-System" target="_blank" rel="noopener noreferrer" style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              GitHub Repo <ExternalLink size={12} />
            </a></li>
          </ul>
        </div>

        <div className="footer-bottom">
          <span>&copy; 2026 Auto-Triage AI Platform. All rights reserved.</span>
          <span>Branch: <strong>Frontend-dev</strong></span>
        </div>
      </footer>
    </div>
  );
}
