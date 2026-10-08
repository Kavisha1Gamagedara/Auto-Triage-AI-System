import React, { useState, useEffect } from 'react';
import { 
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
  AlertCircle,
  ArrowLeft,
  Sliders,
  ExternalLink,
  ChevronRight,
  TrendingUp,
  Sparkles,
  RefreshCw,
  X,
  Lock
} from 'lucide-react';
import { useAuth } from './AuthContext';
import { TIERS_DATA } from './SubscriptionTiersModal';

export default function AdminDashboardPage({ onSwitchToConsole, onSwitchToWorkflow }) {
  const { fetchAdminUsers, fetchAdminMetrics, adminUpdateSubscription, user: currentUser, isAdmin, isAuthenticated } = useAuth();

  const [users, setUsers] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [tierFilter, setTierFilter] = useState('');

  // Edit Drawer state
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
      setUsers(usersData || []);
      setMetrics(metricsData || null);
    } catch (err) {
      console.error('Failed to load admin dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated && isAdmin) {
      loadData();
    }
  }, [isAuthenticated, isAdmin, tierFilter]);

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
      await adminUpdateSubscription(editingUser.id, selectedTier, resetUsage);
      setFeedback({ 
        type: 'success', 
        message: `Successfully updated subscription for ${editingUser.name} to ${selectedTier.toUpperCase()} tier!` 
      });
      setEditingUser(null);
      await loadData();
    } catch (err) {
      setFeedback({ 
        type: 'error', 
        message: err.message || 'Failed to update subscription. Please verify input.' 
      });
    } finally {
      setSaving(false);
    }
  };

  // Access Protection Guard
  if (!isAuthenticated || !isAdmin) {
    return (
      <div className="admin-page-root access-restricted">
        <div className="restricted-card">
          <div className="restricted-icon-box">
            <Lock size={36} color="#EF4444" />
          </div>
          <h2 className="restricted-title">Admin Access Restricted</h2>
          <p className="restricted-desc">
            This command dashboard is strictly restricted to authenticated administrators. 
            Please sign in with administrator credentials (e.g. <code>admin@autotriage.io</code>) to access the system oversight controls.
          </p>
          <div className="restricted-actions">
            <button 
              type="button" 
              onClick={onSwitchToConsole} 
              className="restricted-btn primary"
            >
              <ArrowLeft size={14} />
              <span>Return to Diagnostic Console</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-page-root">
      <div className="admin-page-container">
        {/* Top Header & Breadcrumb Bar */}
        <div className="admin-page-header">
          <div className="admin-header-breadcrumbs">
            <button type="button" onClick={onSwitchToConsole} className="breadcrumb-back-link">
              <ArrowLeft size={14} />
              <span>Diagnostic Console</span>
            </button>
            <span className="breadcrumb-slash">/</span>
            <span className="breadcrumb-current">Admin HQ Command Center</span>
          </div>

          <div className="admin-header-title-row">
            <div>
              <div className="admin-badge-gold">
                <Crown size={14} color="#FFB800" />
                <span>EXECUTIVE HQ CONTROL // ROLE & SUBSCRIPTION OVERSIGHT</span>
              </div>
              <h1 className="admin-page-h1">System Administration & Subscription Portal</h1>
              <p className="admin-page-tagline">
                Real-time operational metrics, multi-tier capacity allocations, user directory management, and billing overrides.
              </p>
            </div>

            <div className="admin-header-actions">
              <button 
                type="button" 
                onClick={loadData} 
                className="admin-header-btn secondary"
                title="Refresh user data & metrics"
              >
                <RefreshCw size={13} className={loading ? 'spin-icon' : ''} />
                <span>Refresh Data</span>
              </button>
              <button 
                type="button" 
                onClick={onSwitchToConsole} 
                className="admin-header-btn primary"
              >
                <Zap size={14} />
                <span>Open Diagnostic Hub</span>
              </button>
            </div>
          </div>
        </div>

        {/* Real-time Business KPI Metric Cards */}
        {metrics && (
          <div className="admin-kpi-grid">
            <div className="admin-kpi-card card-blue">
              <div className="kpi-icon-box blue">
                <Users size={20} />
              </div>
              <div className="kpi-info">
                <span className="kpi-label">TOTAL REGISTERED MECHANICS</span>
                <strong className="kpi-value">{metrics.mechanics_count}</strong>
                <span className="kpi-subtext">Active accounts across bays</span>
              </div>
            </div>

            <div className="admin-kpi-card card-emerald">
              <div className="kpi-icon-box emerald">
                <ShieldCheck size={20} />
              </div>
              <div className="kpi-info">
                <span className="kpi-label">ACTIVE PAID SUBSCRIBERS</span>
                <strong className="kpi-value">
                  {(metrics.tier_distribution.plus || 0) + (metrics.tier_distribution.pro || 0) + (metrics.tier_distribution.ultra || 0)}
                </strong>
                <span className="kpi-subtext">Plus, Pro, & Ultra tiers</span>
              </div>
            </div>

            <div className="admin-kpi-card card-orange">
              <div className="kpi-icon-box orange">
                <DollarSign size={20} />
              </div>
              <div className="kpi-info">
                <span className="kpi-label">MONTHLY RECURRING REVENUE (MRR)</span>
                <strong className="kpi-value highlight">
                  {metrics.monthly_recurring_revenue_lkr.toLocaleString()} LKR
                </strong>
                <span className="kpi-subtext">Calculated active monthly run rate</span>
              </div>
            </div>

            <div className="admin-kpi-card card-cyan">
              <div className="kpi-icon-box cyan">
                <Zap size={20} />
              </div>
              <div className="kpi-info">
                <span className="kpi-label">SYSTEM DIAGNOSES TODAY</span>
                <strong className="kpi-value">{metrics.total_diagnoses_today}</strong>
                <span className="kpi-subtext">Autonomous multi-agent runs</span>
              </div>
            </div>
          </div>
        )}

        {/* Global Feedback Banner */}
        {feedback && (
          <div className={`admin-feedback-banner ${feedback.type}`}>
            {feedback.type === 'success' ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
            <span>{feedback.message}</span>
          </div>
        )}

        {/* Search, Filter & Quick Filter Toolbar */}
        <div className="admin-toolbar-card">
          <form onSubmit={handleSearchSubmit} className="admin-search-form">
            <Search size={15} className="search-icon" />
            <input
              type="text"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search by mechanic name, email address, phone, or workshop..."
              className="admin-search-input"
            />
            <button type="submit" className="admin-search-btn">Search Directory</button>
          </form>

          <div className="admin-filter-bar">
            <div className="admin-filter-select-wrapper">
              <Filter size={13} color="var(--text-muted)" />
              <span className="filter-label">Filter Tier:</span>
              <select
                value={tierFilter}
                onChange={e => setTierFilter(e.target.value)}
                className="admin-tier-select"
              >
                <option value="">All Tiers</option>
                <option value="basic">Basic Free (2 / day)</option>
                <option value="plus">Plus (300 / month)</option>
                <option value="pro">Pro (600 / month)</option>
                <option value="ultra">Ultra (Unlimited)</option>
              </select>
            </div>

            <span className="user-count-chip">
              Showing <strong>{users.length}</strong> accounts
            </span>
          </div>
        </div>

        {/* High-Density Subscribers & Mechanics Directory Table */}
        <div className="admin-table-card">
          <div className="table-card-header">
            <div>
              <h3 className="table-card-title">Registered Mechanics & Enterprise Users</h3>
              <span className="table-card-sub">Manage subscription quotas, override tiers, and monitor diagnostic throughput</span>
            </div>
          </div>

          <div className="admin-table-scroll-wrap">
            <table className="admin-users-table">
              <thead>
                <tr>
                  <th>Mechanic / Technician</th>
                  <th>Contact Details</th>
                  <th>Role</th>
                  <th>Active Tier</th>
                  <th>Quota Used / Capacity</th>
                  <th>Billing Status</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={7} className="table-loading-cell">
                      <div className="table-spinner-row">
                        <div className="admin-loading-spinner" />
                        <span>Querying registered user profiles from backend database...</span>
                      </div>
                    </td>
                  </tr>
                ) : users.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="table-empty-cell">
                      <span>No user accounts found matching current query or filter.</span>
                    </td>
                  </tr>
                ) : (
                  users.map(u => {
                    const quota = u.quota;
                    const isUltra = u.tier === 'ultra';
                    const tierDef = TIERS_DATA.find(t => t.id === u.tier) || { color: '#06B6D4' };

                    return (
                      <tr key={u.id} className="admin-user-row">
                        {/* Name & Garage */}
                        <td>
                          <div className="user-name-cell">
                            <strong className="user-full-name">{u.name}</strong>
                            <span className="user-workshop-sub">
                              <Building2 size={11} />
                              {u.workshop_name || 'Independent Bay'}
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
                              {u.phone || 'No telephone'}
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
                            style={{ borderColor: tierDef.color, color: tierDef.color }}
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
                            <span className="status-badge-active">
                              <CheckCircle2 size={11} />
                              Continuous
                            </span>
                            {u.subscription_expires && (
                              <span className="expiry-date-text">
                                Expires: {new Date(u.subscription_expires).toLocaleDateString()}
                              </span>
                            )}
                          </div>
                        </td>

                        {/* Actions */}
                        <td style={{ textAlign: 'right' }}>
                          <button
                            type="button"
                            onClick={() => handleOpenEdit(u)}
                            className="admin-edit-action-btn"
                            title={`Edit subscription for ${u.name}`}
                          >
                            <Edit3 size={12} />
                            <span>Manage Plan</span>
                          </button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Tier Override & Quota Reset Drawer Modal */}
        {editingUser && (
          <div className="admin-edit-drawer-backdrop" onClick={() => setEditingUser(null)}>
            <div className="admin-edit-drawer-card" onClick={e => e.stopPropagation()}>
              <div className="drawer-header">
                <div className="drawer-title-group">
                  <div className="drawer-badge">
                    <Sliders size={13} color="var(--accent-primary)" />
                    <span>SUBSCRIPTION OVERRIDE // ADMIN COMMAND</span>
                  </div>
                  <h3 className="drawer-title">Manage Capacity for {editingUser.name}</h3>
                  <span className="drawer-sub">{editingUser.email} • {editingUser.role.toUpperCase()}</span>
                </div>
                <button type="button" onClick={() => setEditingUser(null)} className="auth-close-btn">
                  <X size={18} />
                </button>
              </div>

              <form onSubmit={handleSaveSubscription} className="drawer-form">
                <div className="drawer-input-group">
                  <label className="drawer-label">Assign Subscription Tier</label>
                  <div className="tier-select-options">
                    {TIERS_DATA.map(t => (
                      <label 
                        key={t.id} 
                        className={`tier-option-card ${selectedTier === t.id ? 'selected' : ''}`}
                        style={{ '--opt-color': t.color }}
                      >
                        <input
                          type="radio"
                          name="tier"
                          value={t.id}
                          checked={selectedTier === t.id}
                          onChange={e => setSelectedTier(e.target.value)}
                        />
                        <div className="option-info">
                          <strong className="option-name">{t.name}</strong>
                          <span className="option-limit">{t.limit_display}</span>
                          <span className="option-price">{t.price_display} {t.cadence}</span>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>

                <div className="drawer-checkbox-group">
                  <label className="checkbox-row">
                    <input
                      type="checkbox"
                      checked={resetUsage}
                      onChange={e => setResetUsage(e.target.checked)}
                    />
                    <div className="checkbox-labels">
                      <span className="cb-main">Reset Diagnostic Usage Counter to Zero</span>
                      <span className="cb-sub">Immediately resets current daily or monthly tries so the mechanic has full capacity today.</span>
                    </div>
                  </label>
                </div>

                <div className="drawer-footer-actions">
                  <button
                    type="button"
                    onClick={() => setEditingUser(null)}
                    className="drawer-btn cancel"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={saving}
                    className="drawer-btn save"
                  >
                    {saving ? 'Updating Subscription...' : 'Apply Subscription Override'}
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
