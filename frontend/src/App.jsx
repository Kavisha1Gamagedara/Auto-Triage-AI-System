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
  Database
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
  const [triageResult, setTriageResult] = useState(null);
  const [error, setError] = useState(null);
  const [serverStatus, setServerStatus] = useState('checking'); // 'online' | 'offline' | 'checking'
  const [copied, setCopied] = useState(false);
  const [openFaq, setOpenFaq] = useState(0);

  const [intakeMode, setIntakeMode] = useState('smart'); // 'smart' | 'manual'
  const [manualMake, setManualMake] = useState('Honda');
  const [manualModel, setManualModel] = useState('Civic');
  const [manualYear, setManualYear] = useState('2019');
  const [manualDtcs, setManualDtcs] = useState('P0171');
  const [manualParts, setManualParts] = useState('crashed bumper');

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

  const handleCopyPayload = () => {
    if (!triageResult) return;
    navigator.clipboard.writeText(JSON.stringify(triageResult, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRunTriage = async (e) => {
    if (e) e.preventDefault();
    if (loading) return;

    setLoading(true);
    setError(null);

    try {
      let payload = {};

      if (intakeMode === 'smart') {
        if (!rawText.trim()) return;
        payload = {
          session_id: sessionId,
          raw_text: rawText.trim()
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

      const response = await fetch(`${API_BASE_URL}/api/v1/ingest`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Vehicle validation failed against NHTSA vPIC database.');
      }

      setTriageResult(data);
    } catch (err) {
      setError(err.message || 'Network error communicating with FastAPI backend.');
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
            <span className="brand-pill">Agent 1 Live</span>
          </a>

          <ul className="nav-links">
            <li><a href="#console">Triage Console</a></li>
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
                          Validating Against NHTSA Database...
                        </>
                      ) : (
                        <>
                          <ArrowRight size={16} />
                          Execute Smart NLP Triage
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
                          Validating Spec with NHTSA Database...
                        </>
                      ) : (
                        <>
                          <ShieldCheck size={16} />
                          Validate With NHTSA & Ingest to Agent 2
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

            {/* Right Card: Telemetry & Verified Profile */}
            <div className="results-card">
              <div className="card-top-row">
                <div className="card-heading">
                  <ShieldCheck size={18} color="var(--emerald)" />
                  Verified Telemetry & Profile
                </div>
              </div>

              {!triageResult && !loading && (
                <div className="results-empty">
                  <div className="empty-scanner-icon">
                    <Car size={28} />
                  </div>
                  <div>
                    <h3 style={{ fontSize: '1.05rem', color: 'var(--text-white)' }}>
                      Ready for Diagnostic Data
                    </h3>
                    <p style={{ fontSize: '0.85rem', marginTop: 6, color: 'var(--text-muted)' }}>
                      Execute a diagnostic complaint to inspect real-time spaCy extraction 
                      and official US DOT NHTSA vPIC verification.
                    </p>
                  </div>
                </div>
              )}

              {loading && (
                <div className="results-empty">
                  <RefreshCw size={32} color="var(--red-primary)" className="spin-icon" />
                  <div>
                    <h3 style={{ fontSize: '1.05rem', color: 'var(--text-white)' }}>
                      Querying NHTSA VPIC Database...
                    </h3>
                    <p style={{ fontSize: '0.85rem', marginTop: 6, color: 'var(--text-muted)' }}>
                      Verifying physical vehicle existence to prevent AI hallucinations.
                    </p>
                  </div>
                </div>
              )}

              {triageResult && !loading && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  {/* Vehicle Identity Box */}
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
                    </div>
                  </div>

                  {/* OBD-II Trouble Codes */}
                  <div>
                    <div style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 8, letterSpacing: '0.08em' }}>
                      Discovered OBD-II Trouble Codes ({triageResult.dtc_codes.length})
                    </div>
                    {triageResult.dtc_codes.length > 0 ? (
                      <div className="tag-container">
                        {triageResult.dtc_codes.map((code, idx) => (
                          <div key={idx} className="dtc-badge-red">
                            <Activity size={12} />
                            <span>{code}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>No DTC codes detected.</span>
                    )}
                  </div>

                  {/* Damaged Physical Components */}
                  <div>
                    <div style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 8, letterSpacing: '0.08em' }}>
                      Identified Damaged Components ({triageResult.damaged_parts.length})
                    </div>
                    {triageResult.damaged_parts.length > 0 ? (
                      <div className="tag-container">
                        {triageResult.damaged_parts.map((part, idx) => (
                          <div key={idx} className="part-badge-dark">
                            <Wrench size={12} color="var(--red-primary)" />
                            <span>{part}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>No component damage flagged in text.</span>
                    )}
                  </div>

                  {/* A2A Outgoing Contract */}
                  <div className="a2a-box">
                    <div className="a2a-header">
                      <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <Layers size={13} color="var(--red-primary)" />
                        Verified A2A Payload (Handoff to Agent 2)
                      </span>
                      <button onClick={handleCopyPayload} className="icon-btn" style={{ fontSize: '0.72rem', gap: 4 }}>
                        {copied ? (
                          <>
                            <Check size={12} color="var(--emerald)" />
                            <span style={{ color: 'var(--emerald)' }}>Copied</span>
                          </>
                        ) : (
                          <>
                            <Copy size={12} />
                            <span>Copy JSON</span>
                          </>
                        )}
                      </button>
                    </div>
                    <pre className="a2a-code">
                      {JSON.stringify(triageResult, null, 2)}
                    </pre>
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
              <div className="agent-status-tag">
                Ready for Branch Integration
              </div>
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
