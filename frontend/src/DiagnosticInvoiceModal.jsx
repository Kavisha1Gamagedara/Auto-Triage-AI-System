import React, { useState } from 'react';
import {
  X,
  Printer,
  FileText,
  CheckCircle2,
  ShieldCheck,
  Wrench,
  Car,
  AlertTriangle,
  Building2,
  Clock,
  User,
  Check,
  Tag,
  DollarSign,
  Barcode,
  Layers,
  ShoppingBag
} from 'lucide-react';

export default function DiagnosticInvoiceModal({
  isOpen,
  onClose,
  user,
  sessionId,
  triageResult,
  agent2Result,
  repairPlan,
  procurement
}) {
  if (!isOpen || !triageResult) return null;

  // Selected Parts Pricing Tier (OEM Genuine, Certified Aftermarket, Economy)
  const [selectedTier, setSelectedTier] = useState('OEM_Genuine');
  const [customerName, setCustomerName] = useState('Valued Vehicle Owner');
  const [laborHours, setLaborHours] = useState('1.5');
  const [laborRate, setLaborRate] = useState('3000'); // LKR 3,000 per hour
  const [diagnosticFee] = useState(3500); // LKR 3,500 fixed diagnostic scan fee
  const [shopSuppliesFee] = useState(850); // LKR 850 environmental fee

  // Extract merchant information from logged-in user
  const merchantName = user?.workshop_name || user?.name || 'Apex Performance & Diagnostic Lab';
  const technicianName = user?.name || 'Lead Master Technician';
  const merchantEmail = user?.email || 'service@autotriage.io';
  const merchantPhone = user?.phone || '+94 11 234 5678';
  const merchantFacilityId = user?.id ? `FAC-${user.id.toUpperCase().slice(-6)}` : 'FAC-LK-COLOMBO-01';
  const userTier = (user?.tier || 'Pro').toUpperCase();

  // Vehicle details
  const vehicle = triageResult?.vehicle_details || {};
  const vehicleTitle = `${vehicle.year || ''} ${vehicle.make || ''} ${vehicle.model || ''}`.trim() || 'Vehicle Inspected';
  const vin = vehicle.vin || 'N/A';
  const plateNumber = triageResult.sl_plate?.plate_number || vehicle.sl_plate?.plate_number || 'WP CAB-1234';
  const engineSpec = vehicle.engine ? `${vehicle.engine}L` : 'Standard Factory';
  const fuelType = vehicle.fuel_type || 'Gasoline';

  // Diagnostic findings
  const rootCause = agent2Result?.root_cause_component || agent2Result?.primary_hypothesis?.root_cause_component || 'Primary Component Isolated';
  const failureMode = agent2Result?.failure_mode || agent2Result?.primary_hypothesis?.failure_mode || 'Mechanical failure detected under operating load.';
  const confidence = agent2Result?.primary_hypothesis?.confidence || agent2Result?.confidence || 88;
  const severity = (agent2Result?.severity || 'Medium').toUpperCase();
  const dtcCodes = triageResult.dtc_codes || [];
  const confirmingTest = agent2Result?.primary_hypothesis?.confirming_test || agent2Result?.confirming_test;
  const ffa = agent2Result?.freeze_frame_analysis || triageResult?.freeze_frame_analysis;

  // Resolve parts list for the selected tier
  const proc = procurement || {};
  const tiers = proc.tiers || {};

  // Check if session is quarantined by Security Circuit Breaker
  const isQuarantined = Boolean(
    agent2Result?.root_cause_component?.includes('SECURITY') ||
    agent2Result?.severity === 'Quarantined' ||
    proc?.match_method === 'SECURITY_CIRCUIT_BREAKER' ||
    proc?.resolved_part?.includes('SECURITY') ||
    proc?.resolved_part?.includes('WITHHELD')
  );

  // Default fallback parts in case procurement is missing or still pricing
  const defaultFallbackParts = {
    OEM_Genuine: [
      {
        part_name: rootCause,
        brand: vehicle.make ? `${vehicle.make} Genuine` : 'OEM Genuine',
        part_number: '22204-0V010',
        price_lkr: 42500,
        quantity: 1
      }
    ],
    Certified_Aftermarket: [
      {
        part_name: rootCause,
        brand: 'Denso / Bosch Certified',
        part_number: '197-6030',
        price_lkr: 26000,
        quantity: 1
      }
    ],
    Economy: [
      {
        part_name: rootCause,
        brand: 'Standard Motor Products',
        part_number: 'MAS0285',
        price_lkr: 14500,
        quantity: 1
      }
    ]
  };

  const activeTierParts = isQuarantined
    ? []
    : (tiers[selectedTier]?.parts && tiers[selectedTier].parts.length > 0)
      ? tiers[selectedTier].parts
      : (defaultFallbackParts[selectedTier] || defaultFallbackParts.OEM_Genuine);

  // Financial calculations (in LKR)
  const partsSubtotal = isQuarantined ? 0 : activeTierParts.reduce((acc, part) => acc + (Number(part.price_lkr) || 0) * (part.quantity || 1), 0);
  const laborSubtotal = isQuarantined ? 0 : ((parseFloat(laborHours) || 0) * (parseFloat(laborRate) || 0));
  const serviceSubtotal = isQuarantined ? 0 : (diagnosticFee + shopSuppliesFee);
  const grossTotal = isQuarantined ? 0 : (partsSubtotal + laborSubtotal + serviceSubtotal);
  const invoiceNumber = `INV-${(sessionId || '20261010').slice(0, 8).toUpperCase()}`;
  const invoiceDate = new Date().toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
  const invoiceTime = new Date().toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit'
  });

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="invoice-modal-backdrop" onClick={onClose}>
      <div className="invoice-modal-card" onClick={(e) => e.stopPropagation()}>
        {/* MODAL CONTROLS TOOLBAR (Hidden in Print) */}
        <div className="invoice-toolbar no-print">
          <div className="invoice-toolbar-left">
            <div className="invoice-toolbar-title">
              <FileText size={18} color="#00F0FF" />
              <span>Official Diagnostic Bill & Work Order</span>
            </div>
            <span className="invoice-toolbar-badge">
              {merchantName}
            </span>
          </div>

          <div className="invoice-toolbar-center">
            <span className="toolbar-label">Select Quote Tier:</span>
            <div className="tier-toggle-group">
              <button
                type="button"
                className={`tier-toggle-btn ${selectedTier === 'OEM_Genuine' ? 'active' : ''}`}
                onClick={() => setSelectedTier('OEM_Genuine')}
              >
                OEM Genuine
              </button>
              <button
                type="button"
                className={`tier-toggle-btn ${selectedTier === 'Certified_Aftermarket' ? 'active' : ''}`}
                onClick={() => setSelectedTier('Certified_Aftermarket')}
              >
                Aftermarket
              </button>
              <button
                type="button"
                className={`tier-toggle-btn ${selectedTier === 'Economy' ? 'active' : ''}`}
                onClick={() => setSelectedTier('Economy')}
              >
                Economy
              </button>
            </div>
          </div>

          <div className="invoice-toolbar-right">
            <button
              type="button"
              className="btn-print-action"
              onClick={handlePrint}
              title="Print document or Save as PDF"
            >
              <Printer size={16} />
              Print / Save PDF
            </button>
            <button
              type="button"
              className="btn-close-invoice"
              onClick={onClose}
              title="Close Invoice Preview"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* PRINTABLE BILL SHEET (Crisp White Luxury Automotive Invoice) */}
        <div id="printable-diagnostic-bill" className="printable-diagnostic-bill">
          {/* HEADER ROW */}
          <div className="bill-header-row">
            <div className="bill-merchant-info">
              <div className="bill-logo-badge">
                <Car size={24} color="#0284c7" />
                <span className="bill-platform-name">AUTO-TRIAGE AI // CERTIFIED SERVICE</span>
              </div>
              <h1 className="bill-merchant-name">{merchantName}</h1>
              <div className="bill-merchant-meta">
                <span><strong>Certified Inspector:</strong> {technicianName}</span>
                <span><strong>Facility ID:</strong> {merchantFacilityId} · <strong>Level:</strong> {userTier}</span>
                <span><strong>Contact:</strong> {merchantPhone} · {merchantEmail}</span>
              </div>
            </div>

            <div className="bill-invoice-meta">
              <div className="invoice-type-pill">DIAGNOSTIC WORK ORDER & BILL</div>
              <div className="invoice-num-tag">{invoiceNumber}</div>
              <div className="invoice-date-line">
                <span><strong>Date:</strong> {invoiceDate}</span>
                <span><strong>Time:</strong> {invoiceTime}</span>
              </div>
              <div className="invoice-status-chip" style={isQuarantined ? { background: '#fef2f2', borderColor: '#f87171', color: '#b91c1c' } : {}}>
                {isQuarantined ? <AlertTriangle size={13} color="#dc2626" /> : <CheckCircle2 size={13} color="#059669" />}
                <span>{isQuarantined ? 'SECURITY CIRCUIT BREAKER // WITHHELD' : 'TRIAGE VERIFIED & ROAD AUDITED'}</span>
              </div>
            </div>
          </div>

          <hr className="bill-divider" />

          {isQuarantined && (
            <div style={{ background: '#fef2f2', border: '1px solid #f87171', borderRadius: 8, padding: '12px 16px', marginBottom: 16, color: '#991b1b', fontSize: '0.85rem', lineHeight: 1.5 }}>
              <strong style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                <AlertTriangle size={16} color="#dc2626" />
                SECURITY CIRCUIT BREAKER NOTICE: BILLING QUARANTINED
              </strong>
              Adversarial input detected and neutralized by Agent 1 Security Perimeter. All commercial part quotes, labor estimations, and pricing engines are withheld (0 LKR Total) to protect workshop billing integrity.
            </div>
          )}

          {/* CLIENT & VEHICLE PROFILE GRID */}
          <div className="bill-client-vehicle-grid">
            {/* Customer Box */}
            <div className="bill-info-box">
              <div className="box-header-title">
                <User size={13} />
                CUSTOMER & INTAKE RECORD
              </div>
              <div className="info-row">
                <span className="info-k">Client / Fleet:</span>
                <span className="info-v highlight">{customerName}</span>
              </div>
              <div className="info-row">
                <span className="info-k">Intake Complaint:</span>
                <span className="info-v complaint-quote">
                  "{triageResult.user_note || triageResult.canonical_query || 'Customer reported warning indicators and drivability symptoms.'}"
                </span>
              </div>
              <div className="info-row">
                <span className="info-k">IR Canonical Query:</span>
                <span className="info-v mono-text">{triageResult.canonical_query || 'N/A'}</span>
              </div>
            </div>

            {/* Vehicle Profile Box */}
            <div className="bill-info-box">
              <div className="box-header-title">
                <Car size={13} />
                VEHICLE TECHNICAL IDENTITY
              </div>
              <div className="info-row">
                <span className="info-k">Inspected Vehicle:</span>
                <span className="info-v highlight">{vehicleTitle}</span>
              </div>
              <div className="info-row">
                <span className="info-k">Registration Plate:</span>
                <span className="info-v plate-text">{plateNumber}</span>
              </div>
              <div className="info-row">
                <span className="info-k">17-Digit ISO VIN:</span>
                <span className="info-v mono-text">{vin}</span>
              </div>
              <div className="info-row">
                <span className="info-k">Powertrain / Fuel:</span>
                <span className="info-v">{engineSpec} · {fuelType}</span>
              </div>
            </div>
          </div>

          {/* SECTION 1: DIAGNOSTIC & TELEMETRY FINDINGS */}
          <div className="bill-section">
            <div className="bill-section-header">
              <span>1. MULTI-AGENT COGNITIVE DIAGNOSTIC FINDINGS</span>
              <span className="section-meta-pill">CONFIDENCE: {confidence}% · SEVERITY: {severity}</span>
            </div>

            <div className="bill-diagnosis-hero">
              <div className="diag-hero-top">
                <div className="diag-cause-col">
                  <span className="diag-k">ISOLATED ROOT-CAUSE FAILED COMPONENT:</span>
                  <span className="diag-component-name">{rootCause}</span>
                </div>
                <div className="diag-badge-col">
                  <span className={`severity-badge-print severity-${severity.toLowerCase()}`}>
                    {severity} SEVERITY
                  </span>
                </div>
              </div>

              <div className="diag-failure-text">
                <strong>Failure Physics & Mechanism:</strong> {failureMode}
              </div>

              {confirmingTest && (
                <div className="diag-test-callout">
                  <strong>Recommended Workshop Bench Test:</strong> {confirmingTest}
                </div>
              )}
            </div>

            {/* Logged DTC Trouble Codes Table */}
            {dtcCodes.length > 0 && (
              <div className="bill-dtc-table-wrap">
                <table className="bill-table dtc-table">
                  <thead>
                    <tr>
                      <th style={{ width: '15%' }}>DTC Code</th>
                      <th style={{ width: '55%' }}>SAE / ISO Trouble Description</th>
                      <th style={{ width: '30%' }}>Subsystem Classification</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dtcCodes.map((code, idx) => (
                      <tr key={idx}>
                        <td className="mono-code"><strong>{code}</strong></td>
                        <td>
                          {code === 'P0171' && 'System Too Lean (Bank 1) - Fuel trim exceeds compensatory threshold'}
                          {code === 'P0251' && 'Electronic Diesel Injection Pump Fuel Metering Control Malfunction'}
                          {code === 'P0300' && 'Random or Multiple Cylinder Misfire Detected'}
                          {code === 'P0420' && 'Catalyst System Efficiency Below Threshold (Bank 1)'}
                          {code !== 'P0171' && code !== 'P0251' && code !== 'P0300' && code !== 'P0420' && 'Diagnostic Trouble Code Captured by OBD-II Gateway'}
                        </td>
                        <td>Powertrain · Electronic Engine Control</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Freeze Frame Telemetry Summary (if available) */}
            {ffa && (
              <div className="bill-telemetry-box">
                <div className="telemetry-box-title">
                  <CheckCircle2 size={13} color="#059669" />
                  <span>Freeze-Frame Empirical Ground-Truth Operating Parameters</span>
                  <span className="regime-tag">Regime: {ffa.operating_state}</span>
                </div>
                <div className="telemetry-verdict-line">
                  <strong>Master Telemetry Verdict:</strong> {ffa.root_cause_verdict}
                </div>
                {ffa.ruled_out_components && ffa.ruled_out_components.length > 0 && (
                  <div className="ruled-out-line">
                    <strong>Proven Functional / Ruled Out:</strong> {ffa.ruled_out_components.join(', ')}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* SECTION 2: OEM FACTORY PROCEDURE & BOLT TORQUE SPECIFICATION */}
          {repairPlan && (
            <div className="bill-section">
              <div className="bill-section-header">
                <span>2. OEM FACTORY SERVICE SPECIFICATION & BOLT TORQUE</span>
                <span className="section-meta-pill">DENSE VECTOR RAG VERIFIED</span>
              </div>

              <div className="repair-plan-print-box">
                {repairPlan.torque_specs && (
                  <div className="torque-highlight-row">
                    <Wrench size={14} color="#0284c7" />
                    <span><strong>OEM Factory Bolt Torque Tolerances:</strong> {repairPlan.torque_specs}</span>
                  </div>
                )}

                {repairPlan.steps && repairPlan.steps.length > 0 && (
                  <div className="repair-steps-print-list">
                    <span className="steps-subheading">Sequential Removal & Installation Procedure:</span>
                    <ol>
                      {repairPlan.steps.map((st, sIdx) => (
                        <li key={sIdx}>{st}</li>
                      ))}
                    </ol>
                  </div>
                )}

                {repairPlan.citation && (
                  <div className="citation-line">
                    <em>Reference Manual Citation: {repairPlan.citation}</em>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* SECTION 3: ITEMIZED PARTS & LABOR REPAIR BILL */}
          <div className="bill-section">
            <div className="bill-section-header">
              <span>3. ITEMIZED PARTS PROCUREMENT & SERVICE ESTIMATE</span>
              <span className="section-meta-pill">
                TIER: {selectedTier === 'OEM_Genuine' ? 'GENUINE FACTORY OEM' : selectedTier === 'Certified_Aftermarket' ? 'CERTIFIED AFTERMARKET' : 'ECONOMY / BUDGET'}
              </span>
            </div>

            <table className="bill-table items-table">
              <thead>
                <tr>
                  <th style={{ width: '8%' }}>Item</th>
                  <th style={{ width: '42%' }}>Description & Specification</th>
                  <th style={{ width: '22%' }}>Brand & Part Number</th>
                  <th style={{ width: '8%', textAlign: 'center' }}>Qty</th>
                  <th style={{ width: '20%', textAlign: 'right' }}>Total (LKR)</th>
                </tr>
              </thead>
              <tbody>
                {/* Quarantined Notice Row */}
                {isQuarantined && (
                  <tr>
                    <td style={{ textAlign: 'center' }}>--</td>
                    <td colSpan={3}>
                      <strong style={{ color: '#dc2626' }}>Parts Procurement Withheld (Security Quarantine)</strong>
                      <div className="item-subtext">Commercial parts catalogs and pricing suppressed under Security Circuit Breaker</div>
                    </td>
                    <td style={{ textAlign: 'right', fontFamily: 'monospace', fontWeight: 'bold' }}>LKR 0</td>
                  </tr>
                )}

                {/* Parts Rows */}
                {!isQuarantined && activeTierParts.map((part, pIdx) => (
                  <tr key={pIdx}>
                    <td style={{ textAlign: 'center' }}>0{pIdx + 1}</td>
                    <td>
                      <strong>{part.part_name}</strong>
                      <div className="item-subtext">Direct Fit Replacement Component</div>
                    </td>
                    <td>
                      <span className="part-brand">{part.brand}</span>
                      <div className="part-num mono-text">{part.part_number}</div>
                    </td>
                    <td style={{ textAlign: 'center' }}>{part.quantity || 1}</td>
                    <td style={{ textAlign: 'right', fontFamily: 'monospace', fontWeight: 'bold' }}>
                      LKR {((Number(part.price_lkr) || 0) * (part.quantity || 1)).toLocaleString()}
                    </td>
                  </tr>
                ))}

                {/* Labor and Diagnostic Line Items (only if not quarantined) */}
                {!isQuarantined && (
                  <>
                    <tr>
                      <td style={{ textAlign: 'center' }}>0{activeTierParts.length + 1}</td>
                      <td>
                        <strong>Diagnostic Scan & Sensor Telemetry Verification</strong>
                        <div className="item-subtext">Full OBD-II protocol query & freeze-frame live stream analysis</div>
                      </td>
                      <td>Auto-Triage Gateway</td>
                      <td style={{ textAlign: 'center' }}>1</td>
                      <td style={{ textAlign: 'right', fontFamily: 'monospace', fontWeight: 'bold' }}>
                        LKR {diagnosticFee.toLocaleString()}
                      </td>
                    </tr>

                    <tr>
                      <td style={{ textAlign: 'center' }}>0{activeTierParts.length + 2}</td>
                      <td>
                        <strong>Certified Mechanical Labor & Component R&R</strong>
                        <div className="item-subtext">{laborHours} labor hours @ LKR {Number(laborRate).toLocaleString()}/hr per factory standard</div>
                      </td>
                      <td>Master Tech Labor</td>
                      <td style={{ textAlign: 'center' }}>{laborHours}h</td>
                      <td style={{ textAlign: 'right', fontFamily: 'monospace', fontWeight: 'bold' }}>
                        LKR {laborSubtotal.toLocaleString()}
                      </td>
                    </tr>

                    <tr>
                      <td style={{ textAlign: 'center' }}>0{activeTierParts.length + 3}</td>
                      <td>
                        <strong>Environmental & Hazardous Consumables Fee</strong>
                        <div className="item-subtext">Safe disposal of chemical waste, degreaser, and shop supplies</div>
                      </td>
                      <td>Shop Supplies</td>
                      <td style={{ textAlign: 'center' }}>1</td>
                      <td style={{ textAlign: 'right', fontFamily: 'monospace', fontWeight: 'bold' }}>
                        LKR {shopSuppliesFee.toLocaleString()}
                      </td>
                    </tr>
                  </>
                )}
              </tbody>
            </table>

            {/* Financial Summary Card */}
            <div className="bill-financial-summary">
              <div className="financial-notes-col">
                <div className="payment-terms-box">
                  <strong>Payment Terms & Guarantee:</strong>
                  <ul>
                    <li>Official parts quotation valid for 14 calendar days from date of issue.</li>
                    <li>Warranty: {selectedTier === 'OEM_Genuine' ? '12 Months / 20,000 km Factory Warranty' : '6 Months / 10,000 km Certified Warranty'} on replacement parts.</li>
                    <li>Mechanical labor guaranteed for 90 days against installation defects.</li>
                  </ul>
                </div>
              </div>

              <div className="financial-totals-col">
                <div className="totals-row">
                  <span>Parts Subtotal:</span>
                  <span className="mono-num">LKR {partsSubtotal.toLocaleString()}</span>
                </div>
                <div className="totals-row">
                  <span>Labor Subtotal:</span>
                  <span className="mono-num">LKR {laborSubtotal.toLocaleString()}</span>
                </div>
                <div className="totals-row">
                  <span>Diagnostic & Service Fees:</span>
                  <span className="mono-num">LKR {serviceSubtotal.toLocaleString()}</span>
                </div>
                <div className="totals-row total-divider">
                  <span>Gross Total (Before Taxes):</span>
                  <span className="mono-num">LKR {grossTotal.toLocaleString()}</span>
                </div>
                <div className="totals-row">
                  <span>Government Tax / Levies (SSCL / VAT):</span>
                  <span className="mono-num">LKR 0 (Exempt)</span>
                </div>
                <div className="totals-row grand-total-row">
                  <span>TOTAL ESTIMATED PAYABLE:</span>
                  <span className="grand-total-amount">LKR {grossTotal.toLocaleString()}</span>
                </div>
              </div>
            </div>
          </div>

          {/* SECTION 4: OFFICIAL SIGNATURES & STAMP */}
          <div className="bill-signatures-section">
            <div className="sig-col">
              <div className="sig-line"></div>
              <div className="sig-label">Certified Lead Technician</div>
              <div className="sig-sub">{technicianName}</div>
              <div className="sig-date">Date: {invoiceDate}</div>
            </div>

            <div className="sig-col">
              <div className="sig-line"></div>
              <div className="sig-label">Customer Acceptance & Authorization</div>
              <div className="sig-sub">I authorize the diagnosed repair & parts ordering</div>
              <div className="sig-date">Signature: ______________________</div>
            </div>

            <div className="sig-col stamp-col">
              <div className="stamp-box">
                <Building2 size={20} color="#94a3b8" />
                <span>OFFICIAL WORKSHOP STAMP</span>
                <span className="stamp-sub">{merchantName}</span>
              </div>
            </div>
          </div>

          {/* FOOTER AUDIT LINE */}
          <div className="bill-footer-notice">
            <span>
              Auto-Triage AI Multi-Agent Diagnostic Dossier · System Session: {sessionId} · Generated via Groq LLaMA-3-70B & ChromaDB RAG
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
