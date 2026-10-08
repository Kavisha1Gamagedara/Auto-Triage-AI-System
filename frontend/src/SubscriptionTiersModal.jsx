import React from 'react';
import { 
  X, 
  Check, 
  Zap, 
  Crown, 
  Sparkles, 
  Flame, 
  CreditCard, 
  Clock, 
  CheckCircle2, 
  ShieldAlert,
  ArrowRight
} from 'lucide-react';
import { useAuth } from './AuthContext';

export const TIERS_DATA = [
  {
    id: 'basic',
    name: 'Basic Tier',
    badge: 'FREE ENTRY',
    price_lkr: 0,
    price_display: 'FREE',
    cadence: 'Always Free',
    limit_display: '2 tries / day',
    limit_description: 'Daily quota reset at 00:00 UTC',
    color: '#06B6D4',
    features: [
      '2 Autonomous Diagnoses per Day',
      'Agent 1 Ingestion & NHTSA Ground Truth',
      'Agent 2 Physics of Failure Root Cause',
      'Standard 4-Agent Particle Pipeline',
      'SAE DTC Cascade Isolation'
    ]
  },
  {
    id: 'plus',
    name: 'Plus Tier',
    badge: 'MOST POPULAR',
    price_lkr: 30000,
    price_display: '30,000 LKR',
    cadence: '/ month',
    limit_display: '300 tries / month',
    limit_description: 'For busy independent garages & repair bays',
    color: '#3B82F6',
    popular: true,
    features: [
      '300 Autonomous Diagnoses per Month',
      'Priority Groq Llama-3 70B Causal Reasoning',
      'Agent 3 OEM Workshop Dense Vector RAG',
      'Interactive Holographic Flow Controls',
      'Executive Repair Dossier Generation',
      'Monthly Quota Rollover Support'
    ]
  },
  {
    id: 'pro',
    name: 'Pro Tier',
    badge: 'PROFESSIONAL',
    price_lkr: 50000,
    price_display: '50,000 LKR',
    cadence: '/ month',
    limit_display: '600 tries / month',
    limit_description: 'For multi-bay specialty shops & fleet centers',
    color: '#10B981',
    features: [
      '600 Autonomous Diagnoses per Month',
      'Agent 4 Automated BOM Catalog & Parts Resolver',
      '3-Tier Multi-Distributor Quoting (OEM / Aftermarket / Economy)',
      'ChromaDB Dense Semantic Manual Chunk Retrieval',
      'Sub-50ms Execution SLA & Full Telemetry Drawer',
      'Multi-Vehicle Workshop Queue'
    ]
  },
  {
    id: 'ultra',
    name: 'Ultra Tier',
    badge: 'ENTERPRISE',
    price_lkr: 100000,
    price_display: '100,000 LKR',
    cadence: '/ month',
    limit_display: 'UNLIMITED tries',
    limit_description: 'Zero caps • Infinite throughput',
    color: '#FF5E14',
    features: [
      'Unlimited Autonomous Diagnoses per Month',
      'Zero Daily or Monthly Caps (Infinite Runs)',
      'Dedicated Low-Latency Inference Pipeline',
      'Full Multi-Agent LangGraph Asynchronous DAG Engine',
      'Enterprise Multi-Mechanic Team Seat Management',
      '24/7 Priority Automotive Engineering Support'
    ]
  }
];

export default function SubscriptionTiersModal({ 
  isOpen, 
  onClose, 
  onSelectTierToUpgrade, 
  onOpenAuth 
}) {
  const { user, isAuthenticated } = useAuth();

  if (!isOpen) return null;

  const currentTierId = user?.tier || 'basic';
  const quota = user?.quota;

  const handleTierAction = (tier) => {
    if (!isAuthenticated) {
      onClose();
      if (onOpenAuth) onOpenAuth();
      return;
    }
    if (tier.id === currentTierId) return;
    onClose();
    if (onSelectTierToUpgrade) onSelectTierToUpgrade(tier);
  };

  return (
    <div className="tiers-modal-backdrop" onClick={onClose}>
      <div className="tiers-modal-container" onClick={e => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="tiers-modal-header">
          <div>
            <div className="section-tag" style={{ marginBottom: 4 }}>// WORKSHOP CAPACITY & SUBSCRIPTION PLANS</div>
            <h2 className="tiers-modal-title">
              <Sparkles size={22} color="var(--accent-primary)" />
              Choose Your Auto-Triage Diagnostic Capacity
            </h2>
            <p className="tiers-modal-sub">
              Tailored subscription tiers designed for single technicians, multi-bay garages, and enterprise fleet centers in Sri Lanka.
            </p>
          </div>
          <button type="button" onClick={onClose} className="auth-close-btn" title="Close modal">
            <X size={20} />
          </button>
        </div>

        {/* Current User Quota Ribbon */}
        {isAuthenticated && quota && (
          <div className="current-quota-ribbon">
            <div className="quota-ribbon-left">
              <span className="ribbon-tier-pill">{quota.tier.toUpperCase()} PLAN ACTIVE</span>
              <span className="ribbon-usage-text">
                Current Usage: <strong>{quota.used}</strong> / {quota.is_unlimited ? '∞' : quota.limit} {quota.period} tries
              </span>
            </div>
            <div className="quota-ribbon-right">
              {quota.is_unlimited ? (
                <span className="quota-status-pill ok">UNLIMITED QUOTA</span>
              ) : quota.remaining > 0 ? (
                <span className="quota-status-pill ok">{quota.remaining} Tries Remaining</span>
              ) : (
                <span className="quota-status-pill empty">QUOTA EXHAUSTED // UPGRADE REQUIRED</span>
              )}
            </div>
          </div>
        )}

        {/* 4-Tier Grid */}
        <div className="tiers-cards-grid">
          {TIERS_DATA.map(tier => {
            const isCurrent = isAuthenticated && currentTierId === tier.id;
            const isUpgrade = !isCurrent && tier.id !== 'basic';

            return (
              <div 
                key={tier.id} 
                className={`tier-card tier-${tier.id} ${tier.popular ? 'popular' : ''} ${isCurrent ? 'current-active' : ''}`}
                style={{ '--tier-accent': tier.color }}
              >
                {/* Popular or Current Badge */}
                {tier.popular && !isCurrent && (
                  <div className="tier-popular-tag">
                    <Flame size={12} fill="currentColor" />
                    <span>RECOMMENDED</span>
                  </div>
                )}
                {isCurrent && (
                  <div className="tier-current-tag">
                    <CheckCircle2 size={12} />
                    <span>ACTIVE PLAN</span>
                  </div>
                )}

                {/* Card Header */}
                <div className="tier-card-top">
                  <div className="tier-badge-pill">{tier.badge}</div>
                  <h3 className="tier-name">{tier.name}</h3>
                  <div className="tier-price-box">
                    <strong className="tier-price-number">{tier.price_display}</strong>
                    <span className="tier-price-cadence">{tier.cadence}</span>
                  </div>
                </div>

                {/* Limit Callout */}
                <div className="tier-limit-callout">
                  <div className="limit-highlight">
                    <Clock size={14} color={tier.color} />
                    <strong>{tier.limit_display}</strong>
                  </div>
                  <span className="limit-sub">{tier.limit_description}</span>
                </div>

                {/* Feature List */}
                <ul className="tier-features-list">
                  {tier.features.map((feat, idx) => (
                    <li key={idx} className="tier-feature-item">
                      <Check size={14} color={tier.color} className="feat-check" />
                      <span>{feat}</span>
                    </li>
                  ))}
                </ul>

                {/* Action CTA Button */}
                <div className="tier-card-footer">
                  {isCurrent ? (
                    <button type="button" disabled className="tier-action-btn current">
                      <CheckCircle2 size={14} />
                      <span>Current Active Plan</span>
                    </button>
                  ) : isUpgrade ? (
                    <button 
                      type="button" 
                      onClick={() => handleTierAction(tier)}
                      className="tier-action-btn upgrade"
                    >
                      <CreditCard size={14} />
                      <span>Upgrade to {tier.name}</span>
                      <ArrowRight size={13} />
                    </button>
                  ) : (
                    <button 
                      type="button" 
                      onClick={() => handleTierAction(tier)}
                      className="tier-action-btn default"
                    >
                      <span>Select Basic Free</span>
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Developer Payment Notice */}
        <div className="tiers-modal-footer-notice">
          <CreditCard size={15} color="var(--accent-primary)" />
          <span>
            Upgrades utilize the <strong>Developer Sandbox Payment Gateway</strong> supporting instant mock card checkout & test decline simulations in LKR.
          </span>
        </div>
      </div>
    </div>
  );
}
