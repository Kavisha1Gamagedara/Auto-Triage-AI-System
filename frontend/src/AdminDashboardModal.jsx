import React, { useState, useEffect } from 'react';
import { 
  X, 
  Crown, 
  Users, 
  DollarSign, 
  Zap, 
  Search, 
  Filter, 
  Edit3, 
  RotateCcw, 
  ShieldCheck, 
  CheckCircle2, 
  Clock, 
  Phone, 
  Mail, 
  Building2, 
  Calendar,
  AlertCircle
} from 'lucide-react';
import { useAuth } from './AuthContext';
import { TIERS_DATA } from './SubscriptionTiersModal';

export default function AdminDashboardModal({ isOpen, onClose }) {
  const { fetchAdminUsers, fetchAdminMetrics, adminUpdateSubscription, user: currentUser } = useAuth();

  const [users, setUsers] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [tierFilter, setTierFilter] = useState('');

  // Editing state
  const [editingUser, setEditingUser] = useState(null);
  const [selectedTier, setSelectedTier] = useState('basic');
  const [resetUsage, setResetUsage] = useState(false);
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState(null);

  const loadData = async () => {
    setLoading(true);
    setFeedback(null);
    try {
      const [usersData, metricsData] = await Promise.all([
        fetchAdminUsers(search, tierFilter),
        fetchAdminMetrics()
      ]);
      setUsers(usersData);
      setMetrics(metricsData);
    } catch (err) {
      console.error('Failed to load admin data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadData();
    }
  }, [isOpen, tierFilter]);

  // Handle Search submit / enter
  const handleSearchSubmit = (e) => {
    e.preventDefault();
    loadData();
  };

  const handleOpenEdit = (targetUser) => {
    setEditingUser(targetUser);
    setSelectedTier(targetUser.tier);
    setResetUsage(false);
    setFeedback(null);
  };

  const handleSaveSubscription = async (e) => {
    e.preventDefault();
    if (!editingUser) return;
    setSaving(true);
    setFeedback(null);
    try {
      const updated = await adminUpdateSubscription(editingUser.id, selectedTier, resetUsage);
      setFeedback({ type: 'success', message: `Updated ${editingUser.name} to ${selectedTier.toUpperCase()} tier successfully!` });
      setEditingUser(null);
      // Reload table
      await loadData();
    } catch (err) {
      setFeedback({ type: 'error', message: err.message || 'Failed to update subscription.' });
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="admin-modal-backdrop" onClick={onClose}>
      <div className="admin-modal-container" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="admin-modal-header">
          <div className="admin-header-title-box">
            <div className="admin-role-badge">
              <Crown size={15} color="#FFB800" />
              <span>HEADQUARTERS COMMAND // ADMIN OVERSIGHT</span>
            </div>
            <h2 className="admin-heading">User & Subscription Management Console</h2>
          </div>
          <button type="button" onClick={onClose} className="auth-close-btn" title="Close admin console">
            <X size={20} />
          </button>
        </div>

        {/* Top Business Metrics Bar */}
        {metrics && (
          <div className="admin-metrics-grid">
            <div className="admin-metric-card">
              <div className="metric-icon-box blue">
                <Users size={18} />
              </div>
              <div className="metric-info">
                <span className="metric-label">TOTAL REGISTERED MECHANICS</span>
                <strong className="metric-value">{metrics.mechanics_count}</strong>
              </div>
            </div>

            <div className="admin-metric-card">
              <div className="metric-icon-box emerald">
                <ShieldCheck size={18} />
              </div>
              <div className="metric-info">
                <span className="metric-label">ACTIVE PAID SUBSCRIBERS</span>
                <strong className="metric-value">
                  {(metrics.tier_distribution.plus || 0) + (metrics.tier_distribution.pro || 0) + (metrics.tier_distribution.ultra || 0)}
                </strong>
              </div>
            </div>

            <div className="admin-metric-card">
              <div className="metric-icon-box orange">
                <DollarSign size={18} />
              </div>
              <div className="metric-info">
                <span className="metric-label">MONTHLY RECURRING REVENUE (MRR)</span>
                <strong className="metric-value highlight">
                  {metrics.monthly_recurring_revenue_lkr.toLocaleString()} LKR
                </strong>
              </div>
            </div>

            <div className="admin-metric-card">
              <div className="metric-icon-box cyan">
                <Zap size={18} />
              </div>
              <div className="metric-info">
                <span className="metric-label">SYSTEM DIAGNOSES TODAY</span>
                <strong className="metric-value">{metrics.total_diagnoses_today}</strong>
              </div>
            </div>
          </div>
        )}

        {/* Feedback message banner */}
        {feedback && (
          <div className={`admin-feedback-banner ${feedback.type}`}>
            {feedback.type === 'success' ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
            <span>{feedback.message}</span>
          </div>
        )}

        {/* Search & Filter Bar */}
        <div className="admin-toolbar-row">
          <form onSubmit={handleSearchSubmit} className="admin-search-form">
            <Search size={14} className="search-icon" />
            <input
              type="text"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search by mechanic name, email, phone number, or garage..."
              className="admin-search-input"
            />
            <button type="submit" className="admin-search-btn">Search</button>
          </form>

          <div className="admin-filter-group">
            <Filter size={14} color="var(--text-muted)" />
            <span className="filter-label">Filter Tier:</span>
            <select
              value={tierFilter}
              onChange={e => setTierFilter(e.target.value)}
              className="admin-tier-select"
            >
              <option value="">All Tiers</option>
              <option value="basic">Basic Free (2/day)</option>
              <option value="plus">Plus (300/mo)</option>
              <option value="pro">Pro (600/mo)</option>
              <option value="ultra">Ultra (Unlimited)</option>
            </select>

            <button type="button" onClick={loadData} className="admin-refresh-btn" title="Refresh list">
              <RotateCcw size={13} />
            </button>
          </div>
        </div>

        {/* Users Table */}
        <div className="admin-table-container">
          <table className="admin-users-table">
            <thead>
              <tr>
                <th>Mechanic / User</th>
                <th>Contact Information</th>
                <th>Role</th>
                <th>Current Tier</th>
                <th>Quota Used / Capacity</th>
                <th>Status / Expiry</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} className="table-loading-cell">
                    <span>Loading registered users from system database...</span>
                  </td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={7} className="table-empty-cell">
                    <span>No users found matching query.</span>
                  </td>
                </tr>
              ) : (
                users.map(u => {
                  const quota = u.quota;
                  const isUltra = u.tier === 'ultra';
                  const tierColor = TIERS_DATA.find(t => t.id === u.tier)?.color || '#06B6D4';

                  return (
                    <tr key={u.id} className="admin-user-row">
                      {/* Name & Workshop */}
                      <td>
                        <div className="user-name-cell">
                          <strong className="user-full-name">{u.name}</strong>
                          <span className="user-workshop-sub">
                            <Building2 size={11} />
                            {u.workshop_name || 'Independent Workshop'}
                          </span>
                        </div>
                      </td>

                      {/* Contact */}
                      <td>
                        <div className="user-contact-cell">
                          <span className="contact-item">
                            <Mail size={11} />
                            {u.email}
                          </span>
                          <span className="contact-item phone">
                            <Phone size={11} />
                            {u.phone || 'No phone'}
                          </span>
                        </div>
                      </td>

                      {/* Role */}
                      <td>
                        <span className={`user-role-badge ${u.role}`}>
                          {u.role.toUpperCase()}
                        </span>
                      </td>

                      {/* Tier */}
                      <td>
                        <span 
                          className={`user-tier-pill tier-${u.tier}`}
                          style={{ borderColor: tierColor, color: tierColor }}
                        >
                          {u.tier.toUpperCase()}
                        </span>
                      </td>

                      {/* Quota */}
                      <td>
                        <div className="user-quota-cell">
                          {isUltra ? (
                            <span className="quota-unlimited-text">Unlimited (∞)</span>
                          ) : (
                            <>
                              <span className="quota-fraction">
                                <strong>{quota?.used || 0}</strong> / {quota?.limit || 0}
                              </span>
                              <span className="quota-period">({quota?.period})</span>
                            </>
                          )}
                        </div>
                      </td>

                      {/* Expiry */}
                      <td>
                        <div className="user-expiry-cell">
                          <span className="status-dot-active" />
                          <span>{u.subscription_expires ? new Date(u.subscription_expires).toLocaleDateString() : 'Continuous'}</span>
                        </div>
                      </td>

                      {/* Actions */}
                      <td style={{ textAlign: 'right' }}>
                        <button
                          type="button"
                          onClick={() => handleOpenEdit(u)}
                          className="admin-edit-sub-btn"
                          title="Manage Subscription Tier"
                        >
                          <Edit3 size={13} />
                          <span>Manage</span>
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Edit Subscription Modal Overlay */}
        {editingUser && (
          <div className="admin-edit-modal-backdrop" onClick={() => setEditingUser(null)}>
            <div className="admin-edit-modal-card" onClick={e => e.stopPropagation()}>
              <div className="edit-modal-header">
                <div>
                  <div className="section-tag">// ADMIN OVERRIDE</div>
                  <h4>Manage Subscription for {editingUser.name}</h4>
                  <span className="edit-sub-email">{editingUser.email}</span>
                </div>
                <button type="button" onClick={() => setEditingUser(null)} className="auth-close-btn">
                  <X size={16} />
                </button>
              </div>

              <form onSubmit={handleSaveSubscription} className="edit-form-body">
                <div className="edit-input-group">
                  <label className="edit-label">Select Subscription Tier:</label>
                  <div className="edit-tiers-radios">
                    {TIERS_DATA.map(t => (
                      <label 
                        key={t.id} 
                        className={`tier-radio-card ${selectedTier === t.id ? 'active' : ''}`}
                        style={{ '--tier-border': t.color }}
                      >
                        <input
                          type="radio"
                          name="tier"
                          value={t.id}
                          checked={selectedTier === t.id}
                          onChange={e => setSelectedTier(e.target.value)}
                        />
                        <div className="radio-card-content">
                          <div className="radio-card-top">
                            <strong>{t.name}</strong>
                            <span className="radio-price">{t.price_display}</span>
                          </div>
                          <span className="radio-limit">{t.limit_display}</span>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>

                <label className="edit-checkbox-row">
                  <input
                    type="checkbox"
                    checked={resetUsage}
                    onChange={e => setResetUsage(e.target.checked)}
                  />
                  <span>Reset current usage quota count to 0 for this cycle</span>
                </label>

                <div className="edit-action-row">
                  <button type="button" onClick={() => setEditingUser(null)} className="edit-cancel-btn">
                    Cancel
                  </button>
                  <button type="submit" disabled={saving} className="edit-save-btn">
                    {saving ? 'Updating...' : 'Save Subscription Changes'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
