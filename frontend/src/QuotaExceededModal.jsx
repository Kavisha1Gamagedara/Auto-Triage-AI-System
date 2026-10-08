import React from 'react';
import { 
  X, 
  AlertTriangle, 
  Zap, 
  Crown, 
  Sparkles, 
  ArrowRight, 
  Clock, 
  CheckCircle2 
} from 'lucide-react';
import { useAuth } from './AuthContext';

export default function QuotaExceededModal({ isOpen, onClose, onOpenTiers }) {
  const { user } = useAuth();

  if (!isOpen) return null;

  const tier = user?.tier || 'basic';
  const quota = user?.quota;
  const isBasic = tier === 'basic';

  const handleUpgradeClick = () => {
    onClose();
    if (onOpenTiers) onOpenTiers();
  };

  return (
    <div className="quota-modal-backdrop" onClick={onClose}>
      <div className="quota-modal-card" onClick={e => e.stopPropagation()}>
        <div className="quota-modal-header">
          <div className="quota-warning-badge">
            <AlertTriangle size={18} color="#FF5E14" />
            <span>DIAGNOSTIC CAPACITY LIMIT REACHED</span>
          </div>
          <button type="button" onClick={onClose} className="auth-close-btn">
            <X size={18} />
          </button>
        </div>

        <div className="quota-modal-body">
          <h3 className="quota-title">
            {isBasic 
              ? 'Daily Quota Limit Reached (2/2 Tries Used)' 
              : `Monthly Capacity Reached (${quota?.used || 0}/${quota?.limit || 0} Tries)`}
          </h3>

          <p className="quota-message">
            {isBasic ? (
              <>
                You have reached your <strong>2 free diagnostic tries for today</strong> on the <strong>Basic Free tier</strong>.
                Daily quotas reset every midnight at 00:00 UTC. To continue diagnosing vehicles immediately without waiting, upgrade your mechanic account!
              </>
            ) : (
              <>
                You have reached your monthly allocation of <strong>{quota?.limit} tries</strong> for the <strong>{tier.toUpperCase()} tier</strong>.
                Upgrade to a higher tier or Ultra unlimited to keep diagnosing vehicles!
              </>
            )}
          </p>

          <div className="quota-upgrade-perks">
            <div className="perk-item">
              <CheckCircle2 size={15} color="#10B981" />
              <span><strong>Plus Tier (30,000 LKR):</strong> 300 tries/mo + Dense Vector Manual RAG</span>
            </div>
            <div className="perk-item">
              <CheckCircle2 size={15} color="#10B981" />
              <span><strong>Pro Tier (50,000 LKR):</strong> 600 tries/mo + Automated BOM Procurement</span>
            </div>
            <div className="perk-item">
              <CheckCircle2 size={15} color="#10B981" />
              <span><strong>Ultra Tier (100,000 LKR):</strong> Unlimited Tries (Zero Caps)</span>
            </div>
          </div>

          <div className="quota-action-row">
            <button type="button" onClick={onClose} className="quota-btn-dismiss">
              Dismiss & Wait
            </button>
            <button type="button" onClick={handleUpgradeClick} className="quota-btn-upgrade">
              <Sparkles size={14} />
              <span>Upgrade Capacity via Developer Gateway</span>
              <ArrowRight size={13} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
