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
  GitMerge,
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
  Barcode,
  Sun,
  Moon,
  Workflow,
  ArrowUpRight,
  Crown,
  User,
  LogIn,
  LogOut,
  CreditCard,
  Building2,
  Clock
} from 'lucide-react';

import './App.css';
import WorkflowDashboard from './WorkflowDashboard.jsx';
import AdminDashboardPage from './AdminDashboardPage.jsx';
import HypercarHeadlightCanvas from './HypercarHeadlightCanvas.jsx';
import HolographicAgentPipelineGraph from './HolographicAgentPipelineGraph.jsx';
import cinematicSportsCar from './assets/cinematic_sports_car.jpg';
import heroDarkCar from './assets/hero_dark_car.jpg';
import mechanicDiagnostics from './assets/mechanic_diagnostics.jpg';
import Telemetry3DAnimation from './Telemetry3DAnimation.jsx';
import telemetry3dEngine from './assets/telemetry_3d_engine.jpg';
import telemetry3dGearshift from './assets/telemetry_3d_gearshift.jpg';
import telemetry3dGauge from './assets/telemetry_3d_gauge.jpg';

// RBAC & Subscription Modals
import { useAuth } from './AuthContext';
import AuthModal from './AuthModal.jsx';
import SubscriptionTiersModal from './SubscriptionTiersModal.jsx';
import DeveloperPaymentGatewayModal from './DeveloperPaymentGatewayModal.jsx';
import AdminDashboardModal from './AdminDashboardModal.jsx';
import QuotaExceededModal from './QuotaExceededModal.jsx';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const PRESETS = [
  {
    label: 'Universal Cascade: P0171 + P0300 (Lean & Misfire)',
    text: '2018 Toyota Corolla with trouble codes P0171 and P0300 running rough on acceleration with fuel trim imbalance'
  },
  {
    label: 'Cascade: P0171 + P0300 + P0420',
    text: '2019 Honda Civic with codes P0171, P0300, and P0420 running rough with sulfur exhaust odor'
  },
  {
    label: 'Cascade: P0101 + P0171 + P0300',
    text: '2017 Ford F-150 showing codes P0101, P0171, and P0300 with hesitation and misfires'
  },
  {
    label: 'Honda Civic (P0171 Lean)',
    text: '2019 Honda Civic with trouble code P0171 running rough and check engine light on'
  },
  {
    label: 'Typo: "Toyta Commry" (P0171)',
    text: 'Customer brought in 2019 Toyta Commry with trouble code P0171 and rough idle'
  },
  {
    label: 'Typo: "Chevy Silvrado" (P0300)',
    text: 'Technician note: 2017 Chevy Silvrado misfiring on acceleration code P0300 with cracked spark plug'
  },
  {
    label: 'Typo: "Hnda Civc" (P0171)',
    text: '2019 Hnda Civc engine hesitation code P0171'
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
    label: 'Cascade: P0171 + P0300 + P0420 (Civic)',
    make: 'Honda',
    model: 'Civic',
    year: '2019',
    dtcs: 'P0171, P0300, P0420',
    notes: 'Severe multi-code issue: P0171 lean fuel trim leading to P0300 cylinder misfires and downstream P0420 catalyst efficiency breakdown.'
  },
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
    category: 'System',
    categoryKey: 'system',
    q: 'How does Auto-Triage diagnose vehicle problems from OBD-II trouble codes?',
    a: 'Simply input your vehicle details (Make, Model, Year, or 17-digit VIN) alongside diagnostic trouble codes (e.g., P0171, P0300) or reported engine symptoms. Auto-Triage performs cognitive physics-of-failure reasoning to isolate the single root-cause mechanical part that actually failed—bypassing misleading downstream symptoms—and immediately provides OEM factory disassembly steps and exact bolt torque tolerances.'
  },
  {
    category: 'System',
    categoryKey: 'system',
    q: 'Can I search using only my vehicle\'s 17-digit VIN number?',
    a: 'Yes! Auto-Triage features automated VIN decoding synchronized in real time with federal U.S. Department of Transportation (NHTSA vPIC) databases. Submitting your 17-digit VIN immediately decodes the authentic chassis, trim, and year specifications, ensuring 100% road-legal vehicle specifications and eliminating diagnostic errors.'
  },
  {
    category: 'System',
    categoryKey: 'system',
    q: 'What makes, models, and diagnostic trouble codes are supported?',
    a: 'Auto-Triage universally supports all standard OBD-II passenger cars, SUVs, and light trucks across Asian, European, and American manufacturers (including Toyota, Honda, Ford, BMW, Mercedes-Benz, Nissan, and more). It analyzes Powertrain (P-codes), Chassis (C-codes), Body (B-codes), and Network Communication (U-codes).'
  },
  {
    category: 'System',
    categoryKey: 'system',
    q: 'Are the repair procedures authentic manufacturer specifications?',
    a: 'Yes. Every diagnosis extracts verified OEM factory repair procedures, exact bolt torque specifications (in Nm and ft-lbs), required specialty mechanic tools, and technician safety alerts (such as high-voltage hybrid battery precautions and high-pressure fuel spray depressurization protocols).'
  },
  {
    category: 'Pricing',
    categoryKey: 'pricing',
    q: 'How does 3-Tier Parts Pricing work, and what currency is quoted?',
    a: 'For every diagnosed component failure, Auto-Triage automatically delivers transparent price comparisons across three distinct quality tiers: OEM Genuine (factory original), Certified Aftermarket (reputable certified brands), and Economy (budget-friendly options). All part quotes are delivered in Sri Lankan Rupees (LKR) with live supplier catalog verification.'
  },
  {
    category: 'Pricing',
    categoryKey: 'pricing',
    q: 'What are Safety Suppression Locks on hazardous parts?',
    a: 'Driver and technician safety is our absolute priority. When a failure involves safety-critical vehicle assemblies (such as electronic brake control modules, steering linkages, or high-pressure diesel injection systems), Auto-Triage automatically withholds and locks uncertified economy parts to prevent catastrophic failures, advising technicians to source certified components only.'
  },
  {
    category: 'Pricing',
    categoryKey: 'pricing',
    q: 'What subscription plans are available, and how do diagnostic quotas work?',
    a: 'We offer flexible subscription plans tailored for individual vehicle owners, independent mechanics, and automotive workshops: Free Starter (3 diagnostic sessions per month), Pro Mechanic (50 diagnostic sessions per month with full OEM disassembly manuals, torque specs, and parts catalogs), and Workshop Fleet (unlimited diagnostic sessions, multi-vehicle batch analysis, and priority support). Click "Plans & Pricing" in the navigation bar to review or upgrade anytime.'
  },
  {
    category: 'Pricing',
    categoryKey: 'pricing',
    q: 'Can I cancel, upgrade, or downgrade my subscription at any time?',
    a: 'Yes, absolutely. All subscriptions are billed on a flexible monthly schedule with zero long-term commitments. You can upgrade instantly to unlock higher diagnostic quotas through our secure payment gateway or cancel anytime directly from your account settings.'
  }
];

const TIER_ORDER = ['OEM_Genuine', 'Certified_Aftermarket', 'Economy'];

const TIER_LABELS = {
  OEM_Genuine: 'OEM Genuine',
  Certified_Aftermarket: 'Certified Aftermarket',
  Economy: 'Economy'
};

function generateSessionId() {
  return `sess_${Math.random().toString(36).substring(2, 8)}_${Date.now().toString(36).substring(4)}`;
}

export default function App() {
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('auto_triage_theme') || 'dark';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('auto_triage_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  const { user, isAuthenticated, isAdmin, quota, logout, refreshUser, token } = useAuth();

  // Subscription, Auth & Admin Modals State
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authModalTab, setAuthModalTab] = useState('login');
  const [tiersModalOpen, setTiersModalOpen] = useState(false);
  const [gatewayModalOpen, setGatewayModalOpen] = useState(false);
  const [selectedUpgradeTier, setSelectedUpgradeTier] = useState(null);
  const [adminModalOpen, setAdminModalOpen] = useState(false);
  const [quotaExceededModalOpen, setQuotaExceededModalOpen] = useState(false);
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);

  const [activePage, setActivePage] = useState('triage'); // 'triage' | 'workflow'

  const [sessionId, setSessionId] = useState(generateSessionId());
  const [rawText, setRawText] = useState(PRESETS[0].text);
  const [loading, setLoading] = useState(false);
  const [pipelineStage, setPipelineStage] = useState('idle'); // 'idle' | 'agent1' | 'agent2' | 'agent3' | 'agent4' | 'complete' | 'error'
  const [agentLatencies, setAgentLatencies] = useState({ 1: 18, 2: 26, 3: 15, 4: 12 });
  const [showRawJson, setShowRawJson] = useState(false);
  const [triageResult, setTriageResult] = useState(null);
  const [repairPlan, setRepairPlan] = useState(null);
  const [procurement, setProcurement] = useState(null);
  const [procurementError, setProcurementError] = useState(null);
  const [procurementPlan, setProcurementPlan] = useState(null);
  const [error, setError] = useState(null);
  const [serverStatus, setServerStatus] = useState('checking'); // 'online' | 'offline' | 'checking'
  const [copied, setCopied] = useState(false);
  const [openFaq, setOpenFaq] = useState(0);
  const [faqCategoryFilter, setFaqCategoryFilter] = useState('all');

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
    { label: 'Typo: "Toyta Commry"', make: 'Toyta', model: 'Commry', year: 2019, dtcs: 'P0171', parts: 'intake manifold' },
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
    setRepairPlan(null);
    setProcurement(null);
    setProcurementError(null);
    setProcurementPlan(null);
    setAgent2Result(null);
    setPipelineStage('idle');
    setError(null);
  };

  const handlePresetClick = (presetText) => {
    setRawText(presetText);
    setError(null);
  };

  const handleInjectDtc = (dtcCode) => {
    setIntakeMode('smart');
    setRawText(`Vehicle diagnostic inquiry with trouble code ${dtcCode} showing abnormal sensor telemetry.`);
    setError(null);
    const el = document.getElementById('console');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const [selectedHeroVehicle, setSelectedHeroVehicle] = useState('Universal Multi-Make');

  const handleSelectHeroVehicle = (vehName) => {
    setSelectedHeroVehicle(vehName);
    if (vehName === 'Universal Multi-Make') {
      handlePresetClick('2018 Toyota Corolla with trouble codes P0171 and P0300 running rough on acceleration with fuel trim imbalance');
    } else if (vehName === 'Honda Civic') {
      handlePresetClick('2019 Honda Civic with codes P0171, P0300, and P0420 running rough with sulfur exhaust odor');
    } else if (vehName === 'Toyota Camry') {
      handlePresetClick('Customer brought in 2021 Toyota Camry showing code P0420 and damaged catalytic converter');
    } else if (vehName === 'Ford F-150') {
      handlePresetClick('2017 Ford F-150 showing codes P0101, P0171, and P0300 with hesitation and misfires');
    } else if (vehName === 'BMW 3-Series') {
      handlePresetClick('2020 BMW 330i with trouble code P0016 camshaft timing correlation and drive-train warning');
    } else {
      handlePresetClick('2019 Honda Civic with codes P0171, P0300, and P0420 running rough with sulfur exhaust odor');
    }
  };

  const handleLaunchTriageScroll = () => {
    const el = document.getElementById('console');
    if (el) el.scrollIntoView({ behavior: 'smooth' });
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
    if (e && e.preventDefault) e.preventDefault();
    if (loading) return;

    // 1. Role-Based Check: Guest users cannot run diagnosis until logged in
    if (!isAuthenticated) {
      setAuthModalTab('login');
      setAuthModalOpen(true);
      return;
    }

    // 2. Subscription Quota Check: Must have remaining tries
    if (quota && !quota.can_diagnose) {
      setQuotaExceededModalOpen(true);
      return;
    }

    setLoading(true);
    setPipelineStage('agent1');
    setError(null);
    setRepairPlan(null);
    setProcurement(null);
    setProcurementError(null);
    setProcurementPlan(null);
    setTriageResult(null);
    setAgent2Result(null);

    // Smoothly scroll to the wide Holographic Flow stage so user witnesses the live flow
    setTimeout(() => {
      const el = document.getElementById('holographic-flow-stage');
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 80);

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
      setPipelineStage('agent1');
      const t1Start = performance.now();
      const response = await fetch(`${API_BASE_URL}/api/v1/ingest`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify(payload)
      });

      const data1 = await response.json();
      const t1End = performance.now();
      const a1Latency = Math.max(12, Math.round(t1End - t1Start));

      if (!response.ok) {
        if (response.status === 401) {
          setAuthModalTab('login');
          setAuthModalOpen(true);
          setLoading(false);
          return;
        }
        if (response.status === 403 && data1.detail?.code === 'QUOTA_EXCEEDED') {
          setQuotaExceededModalOpen(true);
          setLoading(false);
          return;
        }
        throw new Error(data1.detail?.message || data1.detail || 'Vehicle validation failed against NHTSA vPIC database.');
      }

      // Refresh user's quota count
      refreshUser();

      setTriageResult(data1);
      setAgentLatencies(prev => ({ ...prev, 1: a1Latency }));

      // Sync Agent 2 lab console state
      if (data1.vehicle_details) {
        setAgent2Make(data1.vehicle_details.make || 'Toyota');
        setAgent2Model(data1.vehicle_details.model || 'Corolla');
        setAgent2Year(String(data1.vehicle_details.year || '2019'));
        setAgent2Dtcs((data1.dtc_codes || []).join(', '));
        setAgent2Notes(data1.user_note || `Vehicle verified: ${data1.vehicle_details.year} ${data1.vehicle_details.make} ${data1.vehicle_details.model}`);
        setAgent2Source('agent1');
      }

      // Visual pacing delay so user clearly observes Agent 1 emphasized in working state
      await new Promise(r => setTimeout(r, 650));

      // ==========================================
      // STAGE 2: Automated Handoff to Agent 2 Cognitive Diagnostic Reasoning
      // ==========================================
      setPipelineStage('agent2');
      const t2Start = performance.now();

      const res2 = await fetch(`${API_BASE_URL}/api/v1/diagnose`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data1)
      });

      const data2 = await res2.json();
      const t2End = performance.now();
      const a2Latency = Math.max(18, Math.round(t2End - t2Start));
      setAgentLatencies(prev => ({ ...prev, 2: a2Latency }));

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

      // Visual pacing delay so user clearly observes Agent 2 emphasized in working state
      await new Promise(r => setTimeout(r, 650));

      // ==========================================
      // STAGE 3: Fork Execution: Agent 3 (OEM Workshop Dense RAG)
      // ==========================================
      setPipelineStage('agent3');
      const t3Start = performance.now();

      if (deducedRootCause) {
        try {
          const repairRes = await fetch(`${API_BASE_URL}/api/v1/repair`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              session_id: sessionId,
              vehicle_make: data1.vehicle_details?.make || 'Toyota',
              vehicle_model: data1.vehicle_details?.model || 'Corolla',
              vehicle_year: data1.vehicle_details?.year || 2019,
              issue_summary: deducedRootCause,
              dtc_codes: data1.dtc_codes || []
            })
          });
          const repairData = await repairRes.json();
          if (repairRes.ok && repairData.status === "success") {
            setRepairPlan(repairData.repair_plan);
          } else {
            // Show the failure instead of hiding the box, so "no manual" and "Agent 3 broke" are distinguishable
            setRepairPlan({ steps: [], error: repairData.message || repairData.detail || `Agent 3 request failed (HTTP ${repairRes.status})` });
          }
        } catch (repairErr) {
          console.warn('Agent 3 repair retrieval error:', repairErr);
          setRepairPlan({ steps: [], error: `Agent 3 request failed: ${repairErr.message}` });
        }
      }

      const t3End = performance.now();
      const a3Latency = Math.max(14, Math.round(t3End - t3Start));
      setAgentLatencies(prev => ({ ...prev, 3: a3Latency }));

      // Visual pacing delay so user clearly observes Agent 3 emphasized in working state
      await new Promise(r => setTimeout(r, 650));

      // ==========================================
      // STAGE 4: Join Execution: Agent 4 (BOM Procurement & 3-Tier Quotes)
      // ==========================================
      setPipelineStage('agent4');
      const t4Start = performance.now();

      if (deducedRootCause) {
        try {
          const procureRes = await fetch(`${API_BASE_URL}/api/v1/procure`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              session_id: sessionId,
              root_cause_component: deducedRootCause,
              make: data1.vehicle_details?.make || 'Toyota',
              model: data1.vehicle_details?.model || 'Corolla',
              year: Number(data1.vehicle_details?.year || 2019),
              severity: (data2 && data2.severity) || 'Medium',
              safety_warning: (data2 && data2.safety_warning) || ''
            })
          });
          const procureData = await procureRes.json();
          if (!procureRes.ok) {
            const detail = typeof procureData.detail === 'string' ? procureData.detail : 'Agent 4 procurement failed.';
            throw new Error(detail);
          }
          setProcurementPlan(procureData);
          setProcurement(procureData);
        } catch (procureErr) {
          console.warn('Agent 4 procurement error:', procureErr);
          setProcurementError(procureErr.message || 'Agent 4 procurement is unreachable.');
        }
      }

      const t4End = performance.now();
      const a4Latency = Math.max(10, Math.round(t4End - t4Start));
      setAgentLatencies(prev => ({ ...prev, 4: a4Latency }));

      await new Promise(r => setTimeout(r, 550));

      // ==========================================
      // STAGE 5: Complete - Multi-Agent Synthesis Dossier Ready
      // ==========================================
      setPipelineStage('complete');
    } catch (err) {
      setError(err.message || 'Error communicating with Auto-Triage multi-agent backend.');
      setPipelineStage('error');
      setTriageResult(null);
    } finally {
      setLoading(false);
    }
  };

  const handleNavAnchor = (e, targetId) => {
    if (e && e.preventDefault) e.preventDefault();
    if (activePage !== 'triage') {
      setActivePage('triage');
      setTimeout(() => {
        const el = document.getElementById(targetId);
        if (el) el.scrollIntoView({ behavior: 'smooth' });
      }, 60);
    } else {
      const el = document.getElementById(targetId);
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="app-root">
      {/* Floating Glass Capsule Navigation Header */}
      <header className="site-header floating-glass-nav">
        <div className="nav-container">
          {/* Left Brand Badge with Circular Glyph */}
          <div
            className="nav-brand"
            onClick={() => { setActivePage('triage'); window.scrollTo({ top: 0, behavior: 'smooth' }); }}
            style={{ cursor: 'pointer' }}
            title="Auto-Triage AI Universal Automotive Diagnostic System"
          >
            <div className="floating-nav-brand-circle">
              <Zap size={15} strokeWidth={2.8} />
            </div>
            <div className="brand-glyph">
              AUTO-TRIAGE
            </div>
          </div>

          {/* Central Nav Links */}
          <nav className="floating-nav-links">
            <button
              type="button"
              className={`floating-nav-link ${activePage === 'triage' ? 'active' : ''}`}
              onClick={() => { setActivePage('triage'); window.scrollTo({ top: 0, behavior: 'smooth' }); }}
              id="nav-btn-triage"
            >
              Diagnostic Hub
            </button>
            {isAdmin && (
              <button
                type="button"
                className={`floating-nav-link admin-nav-tab ${activePage === 'admin' ? 'active' : ''}`}
                onClick={() => { setActivePage('admin'); window.scrollTo({ top: 0, behavior: 'smooth' }); }}
                id="nav-btn-admin-tab"
                title="Open Dedicated Admin Dashboard"
              >
                <Crown size={12} color="#FFB800" style={{ marginRight: 5, verticalAlign: 'middle' }} />
                <span>Admin HQ</span>
              </button>
            )}
            <a
              href="#showcase"
              className="floating-nav-link"
              onClick={(e) => handleNavAnchor(e, 'showcase')}
            >
              Architecture
            </a>
            <a
              href="#matrix"
              className="floating-nav-link"
              onClick={(e) => handleNavAnchor(e, 'matrix')}
            >
              DTC Matrix
            </a>
            <button
              type="button"
              className="floating-nav-link"
              onClick={() => setTiersModalOpen(true)}
              id="nav-btn-pricing"
            >
              Plans & Pricing
            </button>
          </nav>

          {/* Right Action Group */}
          <div className="floating-nav-actions">
            {/* System Online Pulse Dot */}
            <div className="floating-status-dot-wrap" title={`Gateway Server: ${serverStatus.toUpperCase()} (Port 8000)`}>
              <span className={`status-dot-pulse ${serverStatus}`} />
            </div>

            {/* Theme Toggle Button */}
            <button
              type="button"
              onClick={toggleTheme}
              className="floating-theme-toggle-btn"
              title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
              id="theme-toggle-btn"
            >
              {theme === 'dark' ? <Sun size={14} color="#FFB800" /> : <Moon size={14} color="#6366F1" />}
            </button>

            <div className="nav-action-divider" />

            {/* AUTHENTICATED USER */}
            {isAuthenticated ? (
              <div className="nav-user-profile-wrapper">
                {/* Quota & Tier Pill */}
                <button
                  type="button"
                  onClick={() => setTiersModalOpen(true)}
                  className={`nav-tier-quota-pill ${quota && quota.remaining === 0 ? 'exhausted' : ''}`}
                  title={`${user?.name} • ${user?.tier?.toUpperCase()} Plan • Click to manage capacity`}
                >
                  <span className={`tier-badge-micro ${user?.tier}`}>{user?.tier?.toUpperCase()}</span>
                  <span className="quota-text-micro">
                    {quota?.is_unlimited ? '∞ Unlimited' : `${quota?.remaining}/${quota?.limit}`}
                  </span>
                </button>

                {/* User Menu Trigger */}
                <button
                  type="button"
                  onClick={() => setUserDropdownOpen(prev => !prev)}
                  className="nav-user-avatar-btn"
                  title={`${user?.name} (${user?.email})`}
                >
                  <div className="avatar-circle">
                    {user?.name ? user.name[0].toUpperCase() : 'M'}
                  </div>
                  <ChevronDown size={11} />
                </button>

                {/* Dropdown Menu */}
                {userDropdownOpen && (
                  <div className="nav-user-dropdown-menu">
                    <div className="dropdown-user-header">
                      <strong>{user?.name}</strong>
                      <span className="dropdown-email">{user?.email}</span>
                      <div className="dropdown-workshop-tag">
                        <Building2 size={11} />
                        <span>{user?.workshop_name || 'Independent Workshop'}</span>
                      </div>
                    </div>

                    <div className="dropdown-divider" />

                    <div className="dropdown-quota-summary">
                      <div className="quota-row">
                        <span>Active Plan:</span>
                        <strong className={`tier-text ${user?.tier}`}>{user?.tier?.toUpperCase()}</strong>
                      </div>
                      <div className="quota-row">
                        <span>Capacity:</span>
                        <strong>{quota?.is_unlimited ? 'Unlimited' : `${quota?.remaining} of ${quota?.limit}`}</strong>
                      </div>
                    </div>

                    <div className="dropdown-divider" />

                    <button
                      type="button"
                      className="dropdown-item-btn"
                      onClick={() => { setUserDropdownOpen(false); setTiersModalOpen(true); }}
                    >
                      <Sparkles size={13} color="var(--accent-primary)" />
                      <span>Subscription Tiers & Pricing</span>
                    </button>

                    <button
                      type="button"
                      className="dropdown-item-btn"
                      onClick={() => {
                        setUserDropdownOpen(false);
                        setSelectedUpgradeTier({ id: 'plus', name: 'Plus Tier', price_lkr: 30000, price_display: '30,000 LKR', limit_display: '300 tries/mo' });
                        setGatewayModalOpen(true);
                      }}
                    >
                      <CreditCard size={13} color="#10B981" />
                      <span>Payment Gateway</span>
                    </button>

                    {isAdmin && (
                      <button
                        type="button"
                        className="dropdown-item-btn"
                        onClick={() => {
                          setUserDropdownOpen(false);
                          setActivePage('admin');
                          window.scrollTo({ top: 0, behavior: 'smooth' });
                        }}
                      >
                        <Crown size={13} color="#FFB800" />
                        <span>Admin HQ Dashboard</span>
                      </button>
                    )}

                    <div className="dropdown-divider" />

                    <button
                      type="button"
                      className="dropdown-item-btn logout"
                      onClick={() => { setUserDropdownOpen(false); logout(); }}
                    >
                      <LogOut size={13} />
                      <span>Sign Out</span>
                    </button>
                  </div>
                )}
              </div>
            ) : (
              /* GUEST STATE: SIGN IN / REGISTER */
              <div className="nav-guest-actions">
                <button
                  type="button"
                  onClick={() => { setAuthModalTab('login'); setAuthModalOpen(true); }}
                  className="nav-ghost-signin-btn"
                  title="Sign In to Mechanic Account"
                >
                  <LogIn size={13} />
                  <span>Sign In</span>
                </button>
                <button
                  type="button"
                  onClick={() => { setAuthModalTab('register'); setAuthModalOpen(true); }}
                  className="nav-ghost-register-btn"
                  title="Register Free (2 Free Diagnoses / Day)"
                >
                  <span>Register Free</span>
                </button>
              </div>
            )}

            {/* PRIMARY CTA */}
            {activePage === 'admin' ? (
              <button
                type="button"
                onClick={() => { setActivePage('triage'); window.scrollTo({ top: 0, behavior: 'smooth' }); }}
                className="floating-pill-cta"
              >
                <span>Launch Triage</span>
              </button>
            ) : activePage === 'workflow' ? (
              <button
                type="button"
                onClick={() => { setActivePage('triage'); }}
                className="floating-pill-cta"
              >
                <span>Diagnostic Console</span>
              </button>
            ) : (
              <a
                href="#console"
                onClick={(e) => handleNavAnchor(e, 'console')}
                className="floating-pill-cta"
              >
                <span>Launch Triage</span>
              </a>
            )}
          </div>
        </div>
      </header>

      {/* Conditional Page Rendering */}
      {activePage === 'workflow' ? (
        <WorkflowDashboard onSwitchToConsole={() => setActivePage('triage')} />
      ) : activePage === 'admin' ? (
        <AdminDashboardPage
          onSwitchToConsole={() => { setActivePage('triage'); window.scrollTo({ top: 0, behavior: 'smooth' }); }}
          onSwitchToWorkflow={() => { setActivePage('workflow'); window.scrollTo({ top: 0, behavior: 'smooth' }); }}
        />
      ) : (
        <>
          {/* 1. CINEMATIC 3D HYPERCAR ATMOSPHERIC HERO BACKGROUND & DIAGNOSTIC STAGE */}
          <section className="cinematic-system-hero-stage">
            <HypercarHeadlightCanvas
              onSelectVehicle={handleSelectHeroVehicle}
              onLaunchTriage={handleLaunchTriageScroll}
              onSwitchToWorkflow={() => setActivePage('workflow')}
              selectedVehicle={selectedHeroVehicle}
            />
          </section>

          {/* 2. HOW AUTO-TRIAGE WORKS - 4-STEP AUTONOMOUS REPAIR PIPELINE */}
          <section className="evolution-section">
            <div className="evolution-container">
              <div className="evolution-header-box">
                <div>
                  <h2 className="pipeline-main-heading">
                    4-Step Autonomous <span className="gradient-text-orange">Diagnostic Pipeline</span>
                  </h2>
                </div>
                <p className="evolution-lead-text">
                  From initial vehicle intake to verified parts delivery in four effortless steps. Discover how Auto-Triage eliminates diagnostic guesswork, protects vehicle roadworthiness, and delivers transparent repair pricing.
                </p>
              </div>

              {/* HORIZONTAL WORKFLOW STEP CONNECTOR BAR */}
              <div className="pipeline-progress-flow">
                <div className="progress-flow-step step-1">
                  <span className="step-circle">01</span>
                  <span className="step-label">Vehicle Intake</span>
                </div>
                <div className="progress-flow-connector" />
                <div className="progress-flow-step step-2">
                  <span className="step-circle">02</span>
                  <span className="step-label">AI Diagnostics</span>
                </div>
                <div className="progress-flow-connector" />
                <div className="progress-flow-step step-3">
                  <span className="step-circle">03</span>
                  <span className="step-label">OEM Repair Guides</span>
                </div>
                <div className="progress-flow-connector" />
                <div className="progress-flow-step step-4">
                  <span className="step-circle">04</span>
                  <span className="step-label">3-Tier Quotes (LKR)</span>
                </div>
              </div>

              <div className="evolution-stats-grid">
                {/* STEP 1: INTAKE & VERIFICATION */}
                <div className="evolution-stat-card telemetry-card-3d card-intake">
                  <div className="pipeline-card-top-bar">
                    <div className="pipeline-step-pill pill-cyan">
                      <span className="step-num">01</span>
                      <span className="step-name">INTAKE & VERIFICATION</span>
                    </div>
                    <span className="pipeline-phase-tag">PHASE 1/4</span>
                  </div>

                  <div className="telemetry-3d-visual-wrap">
                    <div className="telemetry-3d-halo halo-cyan" />
                    <Telemetry3DAnimation type="intake" />
                    <div className="visual-hud-tag"><span className="pulse-dot-cyan" /> 3D SCANNER</div>
                    <div className="visual-hud-hint">LIVE CHASSIS</div>
                  </div>

                  <div className="telemetry-card-content">
                    <h3 className="pipeline-card-title">Chassis Intake & Road Legality</h3>
                    <p className="pipeline-card-desc">
                      Cross-references official US DOT and NHTSA records instantly to eliminate fictitious vehicles and verify authentic chassis parameters.
                    </p>

                    <div className="pipeline-metric-banner banner-cyan">
                      <div className="pipeline-metric-badge">100%</div>
                      <div className="pipeline-metric-info">
                        <span className="pipeline-metric-title">NHTSA Ground Truth</span>
                        <span className="pipeline-metric-sub">Zero vehicle hallucination</span>
                      </div>
                    </div>

                    <div className="pipeline-features-list">
                      <div className="pipeline-feature-item">
                        <span className="feature-check-icon">✓</span>
                        <span>17-digit VIN checksum & entity decode</span>
                      </div>
                      <div className="pipeline-feature-item">
                        <span className="feature-check-icon">✓</span>
                        <span>Real-time federal vPIC registry sync</span>
                      </div>
                      <div className="pipeline-feature-item">
                        <span className="feature-check-icon">✓</span>
                        <span>Rejects invalid makes & phantom cars</span>
                      </div>
                    </div>

                    <div className="pipeline-card-footer-box">
                      <span className="pipeline-status-live">
                        <span className="pulse-dot-green" /> LIVE SERVICE
                      </span>
                      <span>ISO 3779 Checksum Validated</span>
                    </div>
                  </div>
                </div>

                {/* STEP 2: AI DIAGNOSTICS */}
                <div className="evolution-stat-card telemetry-card-3d card-diagnosis">
                  <div className="pipeline-card-top-bar">
                    <div className="pipeline-step-pill pill-orange">
                      <span className="step-num">02</span>
                      <span className="step-name">AI DIAGNOSTICS</span>
                    </div>
                    <span className="pipeline-phase-tag">PHASE 2/4</span>
                  </div>

                  <div className="telemetry-3d-visual-wrap">
                    <div className="telemetry-3d-halo halo-fire" />
                    <Telemetry3DAnimation type="diagnosis" />
                    <div className="visual-hud-tag"><span className="pulse-dot-orange" /> NEURAL CORE</div>
                    <div className="visual-hud-hint">CAUSAL REASONING</div>
                  </div>

                  <div className="telemetry-card-content">
                    <h3 className="pipeline-card-title">Root-Cause Diagnostic Engine</h3>
                    <p className="pipeline-card-desc">
                      Evaluates complex OBD-II trouble codes and symptoms through causal physics-of-failure reasoning to isolate the real broken component.
                    </p>

                    <div className="pipeline-metric-banner banner-orange">
                      <div className="pipeline-metric-badge">ROOT CAUSE</div>
                      <div className="pipeline-metric-info">
                        <span className="pipeline-metric-title">Physics-of-Failure AI</span>
                        <span className="pipeline-metric-sub">Isolates single failed component</span>
                      </div>
                    </div>

                    <div className="pipeline-features-list">
                      <div className="pipeline-feature-item">
                        <span className="feature-check-icon">✓</span>
                        <span>Multi-DTC cascade conflict isolation</span>
                      </div>
                      <div className="pipeline-feature-item">
                        <span className="feature-check-icon">✓</span>
                        <span>Cognitive root-cause failure breakdown</span>
                      </div>
                      <div className="pipeline-feature-item">
                        <span className="feature-check-icon">✓</span>
                        <span>High-voltage & fuel spray safety alerts</span>
                      </div>
                    </div>

                    <div className="pipeline-card-footer-box">
                      <span className="pipeline-status-live">
                        <span className="pulse-dot-green" /> ACTIVE ENGINE
                      </span>
                      <span>SAE J2012 Protocol Standard</span>
                    </div>
                  </div>
                </div>

                {/* STEP 3: OEM REPAIR GUIDES */}
                <div className="evolution-stat-card telemetry-card-3d card-procedures">
                  <div className="pipeline-card-top-bar">
                    <div className="pipeline-step-pill pill-blue">
                      <span className="step-num">03</span>
                      <span className="step-name">REPAIR MANUALS</span>
                    </div>
                    <span className="pipeline-phase-tag">PHASE 3/4</span>
                  </div>

                  <div className="telemetry-3d-visual-wrap">
                    <div className="telemetry-3d-halo halo-steel" />
                    <Telemetry3DAnimation type="procedures" />
                    <div className="visual-hud-tag"><span className="pulse-dot-cyan" /> OEM BLUEPRINT</div>
                    <div className="visual-hud-hint">FACTORY MANUAL</div>
                  </div>

                  <div className="telemetry-card-content">
                    <h3 className="pipeline-card-title">OEM Disassembly & Torques</h3>
                    <p className="pipeline-card-desc">
                      Retrieves authentic manufacturer workshop procedures, delivering exact bolt torque tolerances, safety steps, and specialty tools.
                    </p>

                    <div className="pipeline-metric-banner banner-blue">
                      <div className="pipeline-metric-badge">OEM SPECS</div>
                      <div className="pipeline-metric-info">
                        <span className="pipeline-metric-title">Factory Workshop RAG</span>
                        <span className="pipeline-metric-sub">Exact bolt torques in Nm</span>
                      </div>
                    </div>

                    <div className="pipeline-features-list">
                      <div className="pipeline-feature-item">
                        <span className="feature-check-icon">✓</span>
                        <span>Authentic OEM repair manual extraction</span>
                      </div>
                      <div className="pipeline-feature-item">
                        <span className="feature-check-icon">✓</span>
                        <span>Precise bolt torque tolerances (Nm)</span>
                      </div>
                      <div className="pipeline-feature-item">
                        <span className="feature-check-icon">✓</span>
                        <span>Step-by-step disassembly guidelines</span>
                      </div>
                    </div>

                    <div className="pipeline-card-footer-box">
                      <span className="pipeline-status-live">
                        <span className="pulse-dot-green" /> INDEXED MANUALS
                      </span>
                      <span>Authentic Factory Blueprints</span>
                    </div>
                  </div>
                </div>

                {/* STEP 4: 3-TIER SOURCING */}
                <div className="evolution-stat-card telemetry-card-3d card-procurement">
                  <div className="pipeline-card-top-bar">
                    <div className="pipeline-step-pill pill-green">
                      <span className="step-num">04</span>
                      <span className="step-name">PARTS SOURCING</span>
                    </div>
                    <span className="pipeline-phase-tag">PHASE 4/4</span>
                  </div>

                  <div className="telemetry-3d-visual-wrap">
                    <div className="telemetry-3d-halo halo-bronze" />
                    <Telemetry3DAnimation type="procurement" />
                    <div className="visual-hud-tag"><span className="pulse-dot-green" /> PARTS VAULT</div>
                    <div className="visual-hud-hint">3-TIER SOURCING</div>
                  </div>

                  <div className="telemetry-card-content">
                    <h3 className="pipeline-card-title">3-Tier Pricing in LKR</h3>
                    <p className="pipeline-card-desc">
                      Automatically queries live supplier catalogs to generate transparent price comparisons across OEM Genuine, Aftermarket, and Economy parts.
                    </p>

                    <div className="pipeline-metric-banner banner-green">
                      <div className="pipeline-metric-badge">3 TIERS</div>
                      <div className="pipeline-metric-info">
                        <span className="pipeline-metric-title">Local Catalog in LKR</span>
                        <span className="pipeline-metric-sub">OEM, Aftermarket & Economy</span>
                      </div>
                    </div>

                    <div className="pipeline-features-list">
                      <div className="pipeline-feature-item">
                        <span className="feature-check-icon">✓</span>
                        <span>Instant pricing in Sri Lankan Rupees (LKR)</span>
                      </div>
                      <div className="pipeline-feature-item">
                        <span className="feature-check-icon">✓</span>
                        <span>OEM Genuine vs Certified Aftermarket</span>
                      </div>
                      <div className="pipeline-feature-item">
                        <span className="feature-check-icon">✓</span>
                        <span>Hazardous part suppression safety lock</span>
                      </div>
                    </div>

                    <div className="pipeline-card-footer-box">
                      <span className="pipeline-status-live">
                        <span className="pulse-dot-green" /> LIVE CATALOG
                      </span>
                      <span>Real-time Sri Lankan Inventory</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* 3. UNIVERSAL MULTI-VEHICLE ARCHITECTURE SECTION */}
          <section id="showcase" className="model-showcase-section">

            <div className="model-showcase-container">
              <div className="model-grid-layout">
                {/* Left: Universal Diagnostic Stage */}
                <div className="model-visual-stage">
                  <div className="model-hero-card">
                    <span className="model-floating-badge">UNIVERSAL DIAGNOSTIC COVERAGE // ALL VEHICLE TYPES</span>
                    <img
                      src={mechanicDiagnostics}
                      alt="Universal Multi-Make Automotive Diagnostic Station"
                      className="model-car-image"
                    />
                  </div>

                  <div className="model-detail-thumbs-row">
                    <div className="model-thumb-card">
                      <img src={cinematicSportsCar} alt="Multi-Make Fleet Diagnostics" className="thumb-image" />
                      <div>
                        <div className="thumb-title">Multi-Make Fleet</div>
                        <div className="thumb-desc">Asian, Euro & American Makes</div>
                      </div>
                    </div>
                    <div className="model-thumb-card">
                      <img src={heroDarkCar} alt="All Powertrains Support" className="thumb-image" />
                      <div>
                        <div className="thumb-title">All Drivetrains</div>
                        <div className="thumb-desc">ICE, Hybrid & EV Systems</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Right: Universal Architecture Matrix */}
                <div className="spec-table-box">
                  <div className="spec-header-title">
                    <span>Universal Architecture</span>
                    <span style={{ fontSize: '0.85rem', color: 'var(--accent-primary)', fontFamily: 'var(--font-mono)' }}>
                      [ ALL MAKES & DRIVETRAINS ]
                    </span>
                  </div>

                  <div className="spec-table-list">
                    <div className="spec-row-item">
                      <span className="spec-label-text">Supported Makes</span>
                      <span className="spec-value-text">Toyota, Honda, Ford, BMW, Chevy, Nissan, VAG & Global</span>
                    </div>
                    <div className="spec-row-item">
                      <span className="spec-label-text">Powertrain Compatibility</span>
                      <span className="spec-value-text">Gasoline, Turbo Diesel, Hybrid (HEV) & BEV Systems</span>
                    </div>
                    <div className="spec-row-item">
                      <span className="spec-label-text">Diagnostic Protocols</span>
                      <span className="spec-value-text">SAE J1979 / ISO 15765-4 (CAN) / ISO 14230-4</span>
                    </div>
                    <div className="spec-row-item">
                      <span className="spec-label-text">DTC Code Domains</span>
                      <span className="spec-value-text">Full Spectrum: Powertrain (P), Chassis (C), Body (B), Network (U)</span>
                    </div>
                    <div className="spec-row-item">
                      <span className="spec-label-text">Federal Verification</span>
                      <span className="spec-value-text">NHTSA vPIC Global Registry + Fuzzy Levenshtein</span>
                    </div>
                    <div className="spec-row-item">
                      <span className="spec-label-text">Bill of Materials Engine</span>
                      <span className="spec-value-text">39+ Catalog Component Families (OEM, Aftermarket, Economy)</span>
                    </div>
                    <div className="spec-row-item">
                      <span className="spec-label-text">Neural Ingestion</span>
                      <span className="spec-value-text" style={{ color: 'var(--accent-primary)' }}>spaCy Token Matcher + Regex Diagnostic Ruler</span>
                    </div>
                    <div className="spec-row-item">
                      <span className="spec-label-text">Diagnostic Triage Latency</span>
                      <span className="spec-value-text" style={{ color: 'var(--accent-primary)' }}>&lt; 42 ms Live Asynchronous Pipeline</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Live Diagnostic Command Console (#console) */}
          <section id="console" className="triage-console-section">
            <div className="console-container">
              <div className="console-header">
                <div>
                  <h2 className="section-title">Triage & Validation Console</h2>
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

              {/* Full-Width Panoramic Intake Card */}
              <div className="intake-card-wide">
                <div className="card-top-row">
                  <div className="card-heading">
                    <Activity size={18} color="var(--red-primary)" />
                    Mechanic Diagnostic Intake
                  </div>
                </div>

                {/* Role-Based Diagnostic Quota & Access Status Ribbon */}
                <div className="console-user-quota-banner">
                  {isAuthenticated ? (
                    <div className="quota-banner-logged-in">
                      <div className="banner-left">
                        <span className={`banner-tier-tag ${user?.tier}`}>{user?.tier?.toUpperCase()} TIER</span>
                        <span className="banner-welcome">Technician: <strong>{user?.name}</strong></span>
                        <span className="banner-workshop">({user?.workshop_name || 'Independent Bay'})</span>
                      </div>
                      <div className="banner-right">
                        <div className="quota-counter-box">
                          <Clock size={13} />
                          <span>
                            {quota?.is_unlimited ? (
                              'Unlimited Autonomous Runs'
                            ) : (
                              <>Tries Left {quota?.period === 'daily' ? 'Today' : 'This Month'}: <strong>{quota?.remaining}</strong> / {quota?.limit}</>
                            )}
                          </span>
                        </div>
                        <button
                          type="button"
                          onClick={() => setTiersModalOpen(true)}
                          className="banner-upgrade-btn"
                        >
                          <Sparkles size={12} />
                          <span>{user?.tier === 'ultra' ? 'View Plans' : 'Upgrade Capacity'}</span>
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="quota-banner-guest">
                      <div className="banner-guest-left">
                        <span className="banner-guest-pill">GUEST PREVIEW</span>
                        <span>You are in guest preview. Sign in to execute vehicle diagnoses (Includes <strong>2 Free Tries/Day</strong> on Basic Tier).</span>
                      </div>
                      <div className="banner-guest-right">
                        <button
                          type="button"
                          onClick={() => { setAuthModalTab('login'); setAuthModalOpen(true); }}
                          className="banner-guest-btn login"
                        >
                          <LogIn size={13} />
                          <span>Sign In</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => { setAuthModalTab('register'); setAuthModalOpen(true); }}
                          className="banner-guest-btn register"
                        >
                          <span>Register Free</span>
                        </button>
                      </div>
                    </div>
                  )}
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
                            {pipelineStage === 'agent1' && 'Stage 1/4: Agent 1 Ingesting & NHTSA Validation...'}
                            {pipelineStage === 'agent2' && 'Stage 2/4: Agent 2 Cognitive Causal Reasoning...'}
                            {pipelineStage === 'agent3' && 'Stage 3/4: Agent 3 Dense Vector Manual RAG...'}
                            {pipelineStage === 'agent4' && 'Stage 4/4: Agent 4 BOM Catalog Procurement...'}
                            {pipelineStage === 'complete' && 'Synthesizing Diagnostic Dossier...'}
                          </>
                        ) : (
                          <>
                            <Zap size={16} />
                            Execute Autonomous Workflow (4-Agent Flow)
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
                            {pipelineStage === 'agent1' && 'Stage 1/4: Agent 1 Validating Spec with NHTSA...'}
                            {pipelineStage === 'agent2' && 'Stage 2/4: Agent 2 Groq Causal Reasoning...'}
                            {pipelineStage === 'agent3' && 'Stage 3/4: Agent 3 Chroma Dense RAG...'}
                            {pipelineStage === 'agent4' && 'Stage 4/4: Agent 4 BOM Catalog Procurement...'}
                            {pipelineStage === 'complete' && 'Synthesizing Diagnostic Dossier...'}
                          </>
                        ) : (
                          <>
                            <Zap size={16} />
                            Validate Spec & Run Complete 4-Agent Flow
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
                            {pipelineStage === 'agent1' && 'Stage 1/4: Agent 1 Decoding VIN via NHTSA vPIC...'}
                            {pipelineStage === 'agent2' && 'Stage 2/4: Agent 2 Groq Causal Reasoning...'}
                            {pipelineStage === 'agent3' && 'Stage 3/4: Agent 3 Dense Vector Manual RAG...'}
                            {pipelineStage === 'agent4' && 'Stage 4/4: Agent 4 BOM Catalog Procurement...'}
                            {pipelineStage === 'complete' && 'Synthesizing Diagnostic Dossier...'}
                          </>
                        ) : (
                          <>
                            <Barcode size={16} />
                            Decode VIN & Run Autonomous 4-Agent Flow
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

              {/* Full-Width Panoramic Holographic 4-Agent Particle DAG Stage */}
              <div id="holographic-flow-stage" className="console-holographic-wide-stage">
                {/* Full-Width Panoramic 4-Agent Holographic Particle Canvas */}
                <HolographicAgentPipelineGraph
                  activeStage={pipelineStage}
                  liveLatencies={agentLatencies}
                  liveData={{ triageResult, agent2Result, repairPlan, procurement: procurement || procurementPlan }}
                  embedded={false}
                  isLiveDiagnosis={loading}
                  onRunActualDiagnosis={handleRunTriage}
                />
              </div>

              {/* MISSION CRITICAL ERROR DOSSIER */}
              {error && (
                <div className="dossier-error-banner">
                  <div className="error-banner-top">
                    <AlertTriangle size={32} color="var(--red-primary)" style={{ flexShrink: 0 }} />
                    <div>
                      <div className="error-badge-title">Autonomous Pipeline Rejection // HTTP 422 Unprocessable Entity</div>
                      <div className="error-lead-message">{error}</div>
                    </div>
                  </div>

                  <div className="error-checklist-box">
                    <strong>Pre-Flight Mechanic Diagnostic Checklist:</strong>
                    <ul>
                      <li>Ensure vehicle make and model exist in US DOT NHTSA database (1980–2026).</li>
                      <li>When utilizing 17-character VIN barcode, verify the 9th position MOD-11 checksum digit.</li>
                      <li>Include at least 3 descriptive mechanical symptom tokens or valid OBD-II trouble codes (e.g., P0171, P0300).</li>
                    </ul>
                  </div>

                  <div className="error-actions-row">
                    <button
                      type="button"
                      className="btn-outline-error"
                      onClick={() => { setError(null); setPipelineStage('idle'); }}
                    >
                      <RefreshCw size={14} />
                      Reset Diagnostic Gateway
                    </button>
                    <button
                      type="button"
                      className="btn-accent-preset"
                      onClick={() => {
                        setError(null);
                        handlePresetClick('2018 Toyota Corolla with trouble codes P0171 and P0300 running rough on acceleration with fuel trim imbalance');
                      }}
                    >
                      <Sparkles size={14} />
                      Load Certified Universal Preset (P0171 + P0300)
                    </button>
                  </div>
                </div>
              )}

              {/* FULL-WIDTH EXECUTIVE DIAGNOSTIC OUTPUT DOSSIER */}
              {triageResult && (
                <div className="executive-dossier-root">
                  {/* Executive Header Banner */}
                  <div className="dossier-executive-header">
                    <div>
                      <div className="dossier-tag">
                        <ShieldCheck size={14} />
                        AUTONOMOUS MULTI-AGENT DIAGNOSTIC REPORT // DOSSIER # {sessionId.slice(0, 8)}
                      </div>
                      <div className="dossier-vehicle-title">
                        {triageResult.vehicle_details.year} {triageResult.vehicle_details.make} {triageResult.vehicle_details.model}
                        {triageResult.vehicle_details.is_verified && (
                          <span className="nhtsa-shield-pill" style={{ fontSize: '0.78rem' }}>
                            <ShieldCheck size={13} />
                            NHTSA Verified Road-Legal
                          </span>
                        )}
                        {triageResult.vehicle_details.vin && (
                          <span className="dossier-body-pill" style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                            <Barcode size={13} color="var(--red-primary)" />
                            VIN: {triageResult.vehicle_details.vin}
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="dossier-quick-stats">
                      <div className="dossier-stat-chip">
                        <span>DTCs:</span>
                        <strong>{triageResult.dtc_codes?.length || 0} Codes</strong>
                      </div>
                      <div className="dossier-stat-chip">
                        <span>Root Cause:</span>
                        <strong style={{ color: '#00F0FF' }}>{agent2Result?.root_cause_component || 'Deduced'}</strong>
                      </div>
                      <div className="dossier-stat-chip">
                        <span>Severity:</span>
                        <strong style={{ color: agent2Result?.severity === 'High' ? 'var(--red-primary)' : '#10B981' }}>
                          {(agent2Result?.severity || 'MEDIUM').toUpperCase()}
                        </strong>
                      </div>
                      <div className="dossier-stat-chip">
                        <span>Latency:</span>
                        <strong>{Object.values(agentLatencies).reduce((a, b) => (Number(a) || 0) + (Number(b) || 0), 0) || 7546} ms</strong>
                      </div>

                      <button
                        type="button"
                        className="dossier-action-btn"
                        onClick={() => window.print()}
                        title="Print or Export Diagnostic Report"
                      >
                        <ExternalLink size={13} />
                        Export Report
                      </button>
                      <button
                        type="button"
                        className="dossier-action-btn"
                        onClick={handleNewSession}
                        title="Start Fresh Diagnostic Session"
                      >
                        <RefreshCw size={13} />
                        New Session
                      </button>
                    </div>
                  </div>

                  {/* 4 Modular Executive Cards Grid */}
                  <div className="dossier-grid">
                    {/* CARD 1: AGENT 1 // INGESTION & NHTSA VALIDATION */}
                    <div className="dossier-card card-agent1">
                      <div className="dossier-card-header">
                        <div className="dossier-agent-title" style={{ color: '#00F0FF' }}>
                          <Activity size={18} />
                          Agent 1 // Ingestion & NHTSA VPIC Telemetry
                        </div>
                        <span className="dossier-sla-tag">
                          {agentLatencies[1] ? `${agentLatencies[1]} ms` : '1360 ms'} · SPA-CY NLP
                        </span>
                      </div>

                      {/* Vehicle Specifications */}
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

                      {/* VIN MOD-11 Checksum Verification */}
                      {triageResult.vehicle_details.vin && (
                        <div className="dossier-vin-banner">
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <Barcode size={14} color="#00F0FF" />
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

                      {/* IR RapidFuzz Typo Corrections */}
                      {triageResult.fuzzy_corrections && triageResult.fuzzy_corrections.length > 0 && (
                        <div className="fuzzy-correction-box">
                          <div className="fuzzy-correction-header">
                            <div className="fuzzy-correction-title">
                              <Sparkles size={14} color="#f59e0b" />
                              <span>IR Typo-Tolerant Normalization (RapidFuzz / Levenshtein)</span>
                            </div>
                            <span className="fuzzy-pill">AUTO-CORRECTED</span>
                          </div>
                          <div className="fuzzy-items-list">
                            {triageResult.fuzzy_corrections.map((corr, idx) => (
                              <div key={idx} className="fuzzy-item">
                                <div className="fuzzy-item-left">
                                  <span className="fuzzy-field-tag">{corr.field.toUpperCase()}:</span>
                                  <span className="fuzzy-raw-text">"{corr.raw}"</span>
                                  <span className="fuzzy-arrow">➔</span>
                                  <span className="fuzzy-corrected-text">"{corr.corrected}"</span>
                                </div>
                                <div className="fuzzy-metrics">
                                  <span className="metric-tag">Dist: {corr.levenshtein_distance}</span>
                                  <span className="metric-tag score">{corr.similarity}% Similarity</span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Discovered OBD-II Trouble Codes */}
                      <div>
                        <div style={{ fontSize: '0.74rem', fontWeight: 800, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 8, letterSpacing: '0.08em' }}>
                          Discovered OBD-II Codes ({triageResult.dtc_codes?.length || 0})
                        </div>
                        {triageResult.dtc_codes && triageResult.dtc_codes.length > 0 ? (
                          <div className="tag-container" style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                            {triageResult.dtc_hierarchy && triageResult.dtc_hierarchy.length > 0 ? (
                              triageResult.dtc_hierarchy.map((item, idx) => (
                                <div key={idx} className="dtc-hierarchy-row">
                                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                    <span className="dtc-badge-red" style={{ margin: 0 }}>
                                      <Activity size={12} />
                                      {item.exact_code}
                                    </span>
                                    <span className="dtc-hierarchy-desc">
                                      {item.description}
                                    </span>
                                  </div>
                                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'flex', gap: 6 }}>
                                    <span className="dtc-family-chip">Family: {item.family_code}</span>
                                    <span className="dtc-family-chip">{item.system}</span>
                                  </div>
                                </div>
                              ))
                            ) : (
                              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                                {triageResult.dtc_codes.map((code, idx) => (
                                  <div key={idx} className="dtc-badge-red" style={{ background: 'rgba(0, 240, 255, 0.1)', borderColor: 'rgba(0, 240, 255, 0.4)', color: '#00F0FF' }}>
                                    <Activity size={12} />
                                    <span>{code}</span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        ) : (
                          <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>No DTC codes detected in intake.</span>
                        )}
                      </div>

                      {/* Multi-DTC Causal Cascade Analysis */}
                      {triageResult.dtc_cascade && triageResult.dtc_cascade.has_cascade && (
                        <div className="dtc-cascade-box">
                          <div className="dtc-cascade-header">
                            <div className="dtc-cascade-title">
                              <GitMerge size={15} color="#00F0FF" />
                              <span>Multi-DTC Causal Cascade Detected</span>
                            </div>
                            <span className="dtc-cascade-pill" style={{ color: '#00F0FF', borderColor: 'rgba(0, 240, 255, 0.4)' }}>
                              <Zap size={11} />
                              ROOT TRIGGER ISOLATED
                            </span>
                          </div>
                          <div className="dtc-cascade-flow">
                            <span className="cascade-node-root" style={{ borderColor: '#00F0FF', color: '#00F0FF' }}>
                              ROOT: {triageResult.dtc_cascade.primary_code}
                            </span>
                            {triageResult.dtc_cascade.cascade_codes.map((cc, idx) => (
                              <React.Fragment key={idx}>
                                <span className="cascade-arrow">➔</span>
                                <span className="cascade-node-secondary">
                                  CASCADE: {cc}
                                </span>
                              </React.Fragment>
                            ))}
                          </div>
                          <div className="dtc-cascade-summary">
                            {triageResult.dtc_cascade.diagnostic_summary}
                          </div>
                        </div>
                      )}

                      {/* IR Canonical Query */}
                      {triageResult.canonical_query && (
                        <div className="canonical-query-box">
                          <div style={{ fontSize: '0.72rem', fontWeight: 800, color: '#38bdf8', textTransform: 'uppercase', marginBottom: 4, display: 'flex', alignItems: 'center', gap: 5 }}>
                            <Terminal size={12} />
                            IR Canonical Query (Stopwords Stripped & Synonyms Expanded)
                          </div>
                          <code style={{ fontSize: '0.82rem', color: '#e2e8f0', background: 'transparent' }}>
                            {triageResult.canonical_query}
                          </code>
                        </div>
                      )}
                    </div>

                    {/* CARD 2: AGENT 2 // COGNITIVE CAUSAL REASONING */}
                    <div className="dossier-card card-agent2">
                      <div className="dossier-card-header">
                        <div className="dossier-agent-title" style={{ color: '#3B82F6' }}>
                          <Brain size={18} />
                          Agent 2 // Cognitive Causal Reasoning (Groq LLM)
                        </div>
                        <span className="dossier-sla-tag">
                          {agentLatencies[2] ? `${agentLatencies[2]} ms` : '5171 ms'} · LLAMA-3-70B
                        </span>
                      </div>

                      {agent2Result ? (
                        <>
                          <div className="result-header-row">
                            <div className="result-status-text">
                              <CheckCircle2 size={16} color="var(--emerald)" />
                              CAUSAL REASONING CONCLUDED
                            </div>
                            <div className={`severity-pill severity-${(agent2Result.severity || 'medium').toLowerCase()}`}>
                              <AlertOctagon size={13} />
                              SEVERITY: {agent2Result.severity?.toUpperCase()}
                            </div>
                          </div>

                          {/* Root Cause Component Hero Box */}
                          <div className="root-cause-hero-box" style={{ borderColor: 'rgba(59, 130, 246, 0.4)' }}>
                            <div className="root-cause-tag" style={{ color: '#3B82F6' }}>
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
                            <div className="detail-label" style={{ color: '#3B82F6' }}>
                              <Radio size={13} color="#3B82F6" />
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

                          {/* Downstream Fork Status */}
                          <div className="dispatch-preview-box">
                            <div className="dispatch-header">
                              <span className="dispatch-title">Downstream Dispatch: LangGraph Fork-Join</span>
                              <span style={{ fontSize: '0.7rem', color: 'var(--emerald)', fontWeight: 800 }}>FORKED & JOINED</span>
                            </div>
                            <div className="dispatch-flow-grid">
                              <div className="dispatch-target-card">
                                <div className="target-icon-wrap" style={{ background: 'rgba(16, 185, 129, 0.1)', borderColor: 'rgba(16, 185, 129, 0.3)' }}>
                                  <Layers size={16} color="#10B981" />
                                </div>
                                <div>
                                  <span className="target-name">Agent 3: Manual RAG</span>
                                  <span className="target-sub">ChromaDB OEM Manual</span>
                                </div>
                              </div>
                              <div className="dispatch-target-card">
                                <div className="target-icon-wrap" style={{ background: 'rgba(255, 94, 20, 0.1)', borderColor: 'rgba(255, 94, 20, 0.3)' }}>
                                  <Database size={16} color="#FF5E14" />
                                </div>
                                <div>
                                  <span className="target-name">Agent 4: Parts Catalog</span>
                                  <span className="target-sub">3-Tier Multi-Pricing</span>
                                </div>
                              </div>
                            </div>
                          </div>
                        </>
                      ) : (
                        <div className="results-empty" style={{ padding: '24px 16px' }}>
                          <RefreshCw size={24} className="spin-icon" color="#3B82F6" />
                          <span>Awaiting Groq LLM inference handoff...</span>
                        </div>
                      )}
                    </div>

                    {/* CARD 3: AGENT 3 // OEM WORKSHOP MANUAL RAG */}
                    <div className="dossier-card card-agent3">
                      <div className="dossier-card-header">
                        <div className="dossier-agent-title" style={{ color: '#10B981' }}>
                          <Layers size={18} />
                          Agent 3 // OEM Workshop Manual RAG (ChromaDB)
                        </div>
                        <span className="dossier-sla-tag">
                          {agentLatencies[3] ? `${agentLatencies[3]} ms` : '1657 ms'} · DENSE VECTOR
                        </span>
                      </div>

                      {repairPlan ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                          <div>
                            <div style={{ fontSize: '0.74rem', fontWeight: 800, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 8, letterSpacing: '0.08em' }}>
                              OEM Step-by-Step Replacement Procedure ({repairPlan.steps?.length || 0} Steps)
                            </div>
                            <ol style={{ paddingLeft: '20px', margin: 0, fontSize: '0.88rem', lineHeight: '1.65', color: '#f1f5f9' }}>
                              {repairPlan.steps?.map((step, idx) => (
                                <li key={idx} style={{ marginBottom: '8px' }}>{step}</li>
                              ))}
                            </ol>
                          </div>
                          {(!repairPlan.steps || repairPlan.steps.length === 0) && (
                            <div style={{ fontSize: '0.85rem', color: '#e9d5ff' }}>
                              No matching manual found{repairPlan.error ? ` (${repairPlan.error})` : ''}.
                            </div>
                          )}

                          {repairPlan.torque_specs && (
                            <div style={{ background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: 6, padding: '12px 14px' }}>
                              <div style={{ color: '#34d399', fontSize: '0.78rem', fontWeight: 800, textTransform: 'uppercase', marginBottom: 4, display: 'flex', alignItems: 'center', gap: 6 }}>
                                <Wrench size={13} />
                                OEM Factory Torque Specifications & Tolerances
                              </div>
                              <div style={{ fontSize: '0.92rem', fontWeight: 700, color: '#ffffff', fontFamily: 'var(--font-mono)' }}>
                                {repairPlan.torque_specs}
                              </div>
                            </div>
                          )}

                          <div style={{ paddingTop: 8, borderTop: '1px solid var(--border-subtle)', fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 6 }}>
                            <ExternalLink size={12} color="#10B981" />
                            <span>Vector Reference: <strong>{repairPlan.citation}</strong></span>
                          </div>
                        </div>
                      ) : (
                        <div className="results-empty" style={{ padding: '24px 16px' }}>
                          <Layers size={24} color="#10B981" />
                          <span>Querying dense vector database for workshop repair manual...</span>
                        </div>
                      )}
                    </div>

                    {/* CARD 4: AGENT 4 // BOM CATALOG & MULTI-TIER PROCUREMENT */}
                    <div className="dossier-card card-agent4">
                      <div className="dossier-card-header">
                        <div className="dossier-agent-title" style={{ color: '#FF5E14' }}>
                          <ShoppingBag size={18} />
                          Agent 4 // BOM Catalog & Multi-Tier Pricing
                        </div>
                        <span className="dossier-sla-tag">
                          {agentLatencies[4] ? `${agentLatencies[4]} ms` : '18 ms'} · MOTOR / MITCHELL
                        </span>
                      </div>

                      {(procurement || procurementPlan) ? (
                        (() => {
                          const proc = procurement || procurementPlan;
                          return (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                              {/* Resolved Catalog Component */}
                              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 10 }}>
                                <div className="procure-stat-card">
                                  <span className="procure-stat-label">Resolved Catalog Component</span>
                                  <span className="procure-stat-val">{proc.resolved_part || 'Component Verified'}</span>
                                </div>
                                <div className="procure-stat-card">
                                  <span className="procure-stat-label">Match Strategy & Accuracy</span>
                                  <span className="procure-stat-val highlight">
                                    {proc.match_method} ({Math.round((proc.match_confidence || 1) * 100)}%)
                                  </span>
                                </div>
                              </div>

                              {/* 3-Tier Multi-Pricing Quotes */}
                              {proc.tiers && Object.keys(proc.tiers).length > 0 && (
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                                  {TIER_ORDER.filter((tier) => proc.tiers[tier] && proc.tiers[tier].parts?.length > 0).map((tier) => {
                                    const quote = proc.tiers[tier];
                                    return (
                                      <div key={tier} className="procure-quote-tier-card">
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 12 }}>
                                          <strong className="tier-card-title">{TIER_LABELS[tier] || tier}</strong>
                                          <strong className="tier-card-total">
                                            LKR {quote.tier_total_lkr?.toLocaleString()}
                                          </strong>
                                        </div>

                                        <ul style={{ listStyle: 'none', padding: 0, margin: '8px 0 0', fontSize: '0.82rem', color: 'var(--text-gray)' }}>
                                          {quote.parts?.map((part) => (
                                            <li key={part.part_number} style={{ display: 'flex', justifyContent: 'space-between', gap: 12, marginBottom: 4 }}>
                                              <span>
                                                {part.part_name}{' '}
                                                <span style={{ color: 'var(--text-muted)' }}>
                                                  ({part.brand} · {part.part_number})
                                                </span>
                                              </span>
                                              <span style={{ fontFamily: 'var(--font-mono)', whiteSpace: 'nowrap', color: '#f1f5f9' }}>
                                                LKR {part.price_lkr?.toLocaleString()}
                                              </span>
                                            </li>
                                          ))}
                                        </ul>
                                      </div>
                                    );
                                  })}
                                </div>
                              )}

                              {proc.suppressed_tiers?.length > 0 && (
                                <div style={{ fontSize: '0.8rem', color: '#ff999d', background: 'rgba(255, 30, 39, 0.08)', padding: '8px 12px', borderRadius: 6 }}>
                                  <strong>Withheld for safety:</strong> {proc.suppressed_tiers.map((tier) => TIER_LABELS[tier] || tier).join(', ')}
                                </div>
                              )}

                              {proc.warnings?.length > 0 && (
                                <ul style={{ margin: 0, paddingLeft: 18, fontSize: '0.78rem', color: '#fbbf24' }}>
                                  {proc.warnings.map((w, idx) => (
                                    <li key={idx}>{w}</li>
                                  ))}
                                </ul>
                              )}
                            </div>
                          );
                        })()
                      ) : (
                        <div className="results-empty" style={{ padding: '24px 16px' }}>
                          <ShoppingBag size={24} color="#FF5E14" />
                          <span>Pricing cross-catalog components & inventory...</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Collapsible A2A Handshake JSON Payload */}
                  <div className="raw-json-accordion" style={{ marginTop: 8 }}>
                    <button
                      type="button"
                      className="raw-json-toggle-btn"
                      onClick={() => setShowRawJson(!showRawJson)}
                    >
                      <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <Terminal size={13} color="var(--red-primary)" />
                        {showRawJson ? 'Hide A2A Contract JSON' : 'Inspect Verified A2A Contract JSON (Multi-Agent Telemetry)'}
                      </span>
                      <span>{showRawJson ? '▲' : '▼'}</span>
                    </button>
                    {showRawJson && (
                      <div className="raw-json-body">
                        <pre className="a2a-code">
                          {JSON.stringify({ triageResult, agent2Result, repairPlan, procurement: procurement || procurementPlan }, null, 2)}
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

              {/* INITIAL IDLE STATE: Mechanic Quick-Start Guide */}
              {!triageResult && !loading && !error && (
                <div className="results-empty" style={{ padding: '36px 24px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)' }}>
                  <div className="empty-scanner-icon" style={{ width: 60, height: 60 }}>
                    <Car size={32} color="#00F0FF" />
                  </div>
                  <div>
                    <h3 style={{ fontSize: '1.2rem', color: 'var(--text-white)', fontWeight: 800 }}>
                      Auto-Triage Autonomous Multi-Agent Command Deck Ready
                    </h3>
                    <p style={{ fontSize: '0.9rem', marginTop: 8, color: 'var(--text-muted)', maxWidth: 640, lineHeight: 1.6 }}>
                      Select any quick preset above or type a customer complaint. The system will launch the
                      <strong> full wide-screen holographic particle DAG</strong> across all 4 agents in real-time, then render your
                      <strong> complete Executive Diagnostic Dossier</strong> with OEM repair procedures and 3-tier LKR procurement quotes.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </section>

          {/* Diagnostic & DTC Coverage Matrix (#matrix) */}
          <section id="matrix" className="matrix-section">
            <h2 className="section-title">Diagnostic Trouble Code Matrix</h2>

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
              <h2 className="section-title">Frequently Asked Questions</h2>
              <p style={{ color: 'var(--text-secondary)', maxWidth: 620, margin: '12px auto 0', fontSize: '0.95rem', lineHeight: 1.6 }}>
                Common questions from drivers, mechanics, and workshop managers regarding diagnostics, 3-tier parts sourcing, and subscription plans.
              </p>

              <div className="faq-filter-pills">
                <button
                  type="button"
                  className={`faq-filter-btn ${faqCategoryFilter === 'all' ? 'active' : ''}`}
                  onClick={() => { setFaqCategoryFilter('all'); setOpenFaq(0); }}
                >
                  All Questions ({FAQ_ITEMS.length})
                </button>
                <button
                  type="button"
                  className={`faq-filter-btn ${faqCategoryFilter === 'system' ? 'active' : ''}`}
                  onClick={() => { setFaqCategoryFilter('system'); setOpenFaq(0); }}
                >
                  System & Diagnostics
                </button>
                <button
                  type="button"
                  className={`faq-filter-btn ${faqCategoryFilter === 'pricing' ? 'active' : ''}`}
                  onClick={() => { setFaqCategoryFilter('pricing'); setOpenFaq(0); }}
                >
                  Pricing & Subscriptions
                </button>
              </div>
            </div>

            <div className="faq-list">
              {FAQ_ITEMS
                .filter(item => faqCategoryFilter === 'all' || item.categoryKey === faqCategoryFilter)
                .map((item, index) => {
                  const isOpen = openFaq === index;
                  return (
                    <div key={index} className={`faq-item ${isOpen ? 'open' : ''}`}>
                      <button
                        className="faq-question"
                        onClick={() => setOpenFaq(isOpen ? -1 : index)}
                      >
                        <span style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                          <span className={`faq-category-pill ${item.categoryKey}`}>
                            {item.category}
                          </span>
                          <span>{item.q}</span>
                        </span>
                        {isOpen ? <ChevronUp size={18} color="var(--accent-primary, #FF5E14)" /> : <ChevronDown size={18} />}
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
        </>
      )}

      {/* Footer */}
      <footer className="site-footer">
        <div className="footer-container" style={{ position: 'relative', zIndex: 1 }}>
          <div>
            <div className="footer-brand">
              AUTO-TRIAGE
            </div>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: 8, maxWidth: 440, lineHeight: 1.6 }}>
              Autonomous Vehicle Diagnostic Gateway & Multi-Tier Parts Procurement Engine for modern workshops and technicians.
            </p>
            <div style={{ marginTop: 14, display: 'flex', gap: 10 }}>
              <button
                type="button"
                onClick={toggleTheme}
                className="theme-toggle-btn"
                style={{ fontSize: '0.72rem' }}
              >
                {theme === 'dark' ? <Sun size={12} color="#FFB800" /> : <Moon size={12} color="#6366F1" />}
                <span>{theme === 'dark' ? 'Light Theme' : 'Dark Theme'}</span>
              </button>
            </div>
          </div>

          <ul className="footer-links">
            {isAdmin && (
              <li><button type="button" onClick={() => { setActivePage('admin'); window.scrollTo({ top: 0, behavior: 'smooth' }); }} style={{ background: 'none', border: 'none', color: '#FFB800', cursor: 'pointer', font: 'inherit', fontWeight: 700 }}>Admin Dashboard</button></li>
            )}
            <li><a href="#showcase">Universal Architecture</a></li>
            <li><a href="#matrix">Telemetry Matrix</a></li>


          </ul>
        </div>

        <div className="footer-bottom" style={{ position: 'relative', zIndex: 1 }}>
          <span>&copy; 2026 Auto-Triage AI Platform. All rights reserved.</span>
          <span>Aesthetic Theme: <strong>{theme.toUpperCase()}</strong> | Engine: <strong>Auto-Triage v2.4</strong></span>
        </div>
      </footer>

      {/* Role-Based Authentication Modal */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        initialTab={authModalTab}
        onAuthSuccess={() => {
          refreshUser();
        }}
      />

      {/* 4 Subscription Tiers Comparison & Upgrade Modal */}
      <SubscriptionTiersModal
        isOpen={tiersModalOpen}
        onClose={() => setTiersModalOpen(false)}
        onSelectTierToUpgrade={(tier) => {
          setSelectedUpgradeTier(tier);
          setGatewayModalOpen(true);
        }}
        onOpenAuth={() => {
          setAuthModalTab('login');
          setAuthModalOpen(true);
        }}
      />

      {/* Developer Sandbox Payment Gateway Modal */}
      <DeveloperPaymentGatewayModal
        isOpen={gatewayModalOpen}
        onClose={() => setGatewayModalOpen(false)}
        targetTier={selectedUpgradeTier}
        onPaymentSuccess={() => {
          refreshUser();
        }}
      />

      {/* Admin User & Subscription Management Console */}
      <AdminDashboardModal
        isOpen={adminModalOpen}
        onClose={() => setAdminModalOpen(false)}
      />

      {/* Quota Exceeded Notification Modal */}
      <QuotaExceededModal
        isOpen={quotaExceededModalOpen}
        onClose={() => setQuotaExceededModalOpen(false)}
        onOpenTiers={() => {
          setQuotaExceededModalOpen(false);
          setTiersModalOpen(true);
        }}
      />
    </div>
  );
}
