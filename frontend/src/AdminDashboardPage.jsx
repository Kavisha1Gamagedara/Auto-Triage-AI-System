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
  Lock,
  Tag,
  CreditCard,
  Plus,
  Minus,
  Trash2,
  BarChart3,
  LineChart,
  PieChart,
  Award,
  Lightbulb,
  Compass,
  Layers,
  ArrowUpRight,
  Activity,
  Check
} from 'lucide-react';
import { useAuth } from './AuthContext';
import { TIERS_DATA } from './SubscriptionTiersModal';

export default function AdminDashboardPage({ onSwitchToConsole, onSwitchToWorkflow }) {
  const { 
    fetchAdminUsers, 
    fetchAdminMetrics, 
    adminUpdateSubscription, 
    adminUpdateTier, 
    adminCreateTier,
    adminDeleteTier,
    tiers, 
    fetchTiers, 
    user: currentUser, 
    isAdmin, 
    isAuthenticated 
  } = useAuth();

  const [adminTab, setAdminTab] = useState('directory'); // 'directory' | 'pricing' | 'analytics'
  const [users, setUsers] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [tierFilter, setTierFilter] = useState('');

  // Analytics & Charts state
  const [lineChartMetric, setLineChartMetric] = useState('diagnoses'); // 'diagnoses' | 'new_users'
  const [barChartMetric, setBarChartMetric] = useState('subscribers'); // 'subscribers' | 'revenue'
  const [hoveredPointIndex, setHoveredPointIndex] = useState(null);
  const [hoveredBarId, setHoveredBarId] = useState(null);

  // User Edit Drawer state
  const [editingUser, setEditingUser] = useState(null);
  const [selectedTier, setSelectedTier] = useState('basic');
  const [resetUsage, setResetUsage] = useState(false);
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState(null);

  // Tier Pricing & Quota Edit Drawer state
  const [editingTier, setEditingTier] = useState(null);
  const [tierPrice, setTierPrice] = useState(0);
  const [tierLimit, setTierLimit] = useState(0);
  const [tierPeriod, setTierPeriod] = useState('monthly');
  const [tierUnlimited, setTierUnlimited] = useState(false);
  const [tierDescription, setTierDescription] = useState('');
  const [tierBadge, setTierBadge] = useState('');
  const [tierSaving, setTierSaving] = useState(false);

  // Create New Tier Modal state
  const [showCreateTierModal, setShowCreateTierModal] = useState(false);
  const [newTierName, setNewTierName] = useState('');
  const [newTierId, setNewTierId] = useState('');
  const [newTierPrice, setNewTierPrice] = useState(45000);
  const [newTierLimit, setNewTierLimit] = useState(500);
  const [newTierPeriod, setNewTierPeriod] = useState('monthly');
  const [newTierUnlimited, setNewTierUnlimited] = useState(false);
  const [newTierBadge, setNewTierBadge] = useState('CUSTOM TIER');
  const [newTierColor, setNewTierColor] = useState('#8B5CF6');
  const [newTierDesc, setNewTierDesc] = useState('');
  const [newTierFeatures, setNewTierFeatures] = useState('');
  const [createLoading, setCreateLoading] = useState(false);
  const [deletingTierId, setDeletingTierId] = useState(null);

  const loadData = async () => {
    setLoading(true);
    setFeedback(null);
    try {
      const [usersData, metricsData] = await Promise.all([
        fetchAdminUsers(search, tierFilter),
        fetchAdminMetrics(),
        fetchTiers()
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

  const handleOpenEditTier = (tierDef) => {
    const live = tiers?.find(t => t.id === tierDef.id) || tierDef;
    setEditingTier(tierDef);
    setTierPrice(live.price_lkr || 0);
    setTierLimit(live.is_unlimited ? 999999 : (live.limit || tierDef.limit || 100));
    setTierPeriod(live.period || 'monthly');
    setTierUnlimited(Boolean(live.is_unlimited));
    setTierDescription(live.description || tierDef.limit_description || '');
    setTierBadge(live.badge || tierDef.badge || '');
    setFeedback(null);
  };

  const handleSaveTier = async (e) => {
    e.preventDefault();
    if (!editingTier) return;
    setTierSaving(true);
    setFeedback(null);
    try {
      await adminUpdateTier(editingTier.id, {
        price_lkr: Number(tierPrice),
        limit: tierUnlimited ? 999999 : Number(tierLimit),
        period: tierPeriod,
        is_unlimited: tierUnlimited,
        description: tierDescription,
        badge: tierBadge
      });
      setFeedback({ 
        type: 'success', 
        message: `Successfully updated ${editingTier.name}! Price: ${Number(tierPrice).toLocaleString()} LKR, Quota: ${tierUnlimited ? 'Unlimited (∞)' : `${tierLimit} ${tierPeriod} tries`}.` 
      });
      setEditingTier(null);
      await loadData();
    } catch (err) {
      setFeedback({ 
        type: 'error', 
        message: err.message || 'Failed to update subscription tier details.' 
      });
    } finally {
      setTierSaving(false);
    }
  };

  const allTiers = React.useMemo(() => {
    if (!tiers || tiers.length === 0) {
      return TIERS_DATA.map(t => ({ ...t, isCore: true }));
    }
    return tiers.map(live => {
      const standard = TIERS_DATA.find(t => t.id === live.id);
      if (standard) {
        return {
          ...standard,
          name: live.name || standard.name,
          price_lkr: live.price_lkr,
          price_display: live.price_lkr === 0 ? 'FREE' : `${Number(live.price_lkr).toLocaleString()} LKR`,
          limit: live.limit,
          period: live.period,
          cadence: live.period === 'daily' ? 'Daily' : '/ month',
          limit_display: live.is_unlimited ? 'UNLIMITED tries' : `${live.limit} tries / ${live.period === 'daily' ? 'day' : 'month'}`,
          limit_description: live.description || standard.limit_description,
          description: live.description || standard.limit_description,
          badge: live.badge || standard.badge,
          color: live.color || standard.color,
          features: (live.features && live.features.length > 0) ? live.features : standard.features,
          is_unlimited: live.is_unlimited,
          isCore: true
        };
      }
      return {
        id: live.id,
        name: live.name,
        price_lkr: live.price_lkr,
        price_display: live.price_lkr === 0 ? 'FREE' : `${Number(live.price_lkr).toLocaleString()} LKR`,
        limit: live.limit,
        period: live.period || 'monthly',
        cadence: live.period === 'daily' ? 'Daily' : '/ month',
        limit_display: live.is_unlimited ? 'UNLIMITED tries' : `${live.limit} tries / ${live.period === 'daily' ? 'day' : 'month'}`,
        limit_description: live.description || 'Custom tailored diagnostic capacity tier.',
        description: live.description || 'Custom tailored diagnostic capacity tier.',
        badge: live.badge || 'CUSTOM',
        color: live.color || '#8B5CF6',
        features: (live.features && live.features.length > 0) ? live.features : [
          `${live.is_unlimited ? 'Unlimited' : live.limit} Autonomous Diagnoses / ${live.period || 'monthly'}`,
          'Multi-Agent Diagnostic Pipeline Access',
          'SAE DTC Cascade Isolation'
        ],
        is_unlimited: live.is_unlimited,
        isCore: false
      };
    });
  }, [tiers]);

  const handleOpenCreateTier = (preset = null) => {
    if (preset) {
      setNewTierName(preset.name || '');
      setNewTierId(preset.id || '');
      setNewTierPrice(preset.price_lkr !== undefined ? preset.price_lkr : 45000);
      setNewTierLimit(preset.limit !== undefined ? preset.limit : 500);
      setNewTierPeriod(preset.period || 'monthly');
      setNewTierUnlimited(Boolean(preset.is_unlimited));
      setNewTierBadge(preset.badge || 'CUSTOM TIER');
      setNewTierColor(preset.color || '#8B5CF6');
      setNewTierDesc(preset.description || '');
      setNewTierFeatures(Array.isArray(preset.features) ? preset.features.join('\n') : (preset.features || ''));
    } else {
      setNewTierName('');
      setNewTierId('');
      setNewTierPrice(45000);
      setNewTierLimit(500);
      setNewTierPeriod('monthly');
      setNewTierUnlimited(false);
      setNewTierBadge('ENTERPRISE FLEET');
      setNewTierColor('#8B5CF6');
      setNewTierDesc('Dedicated capacity tier for multi-bay fleet workshops & specialty tuning centers.');
      setNewTierFeatures('500 Autonomous Diagnoses per Month\nPriority Multi-Agent LangGraph Pipeline\nChromaDB Dense Semantic Manual Chunk Retrieval\nAutomated BOM Catalog & Multi-Distributor Quoting\nDedicated Engineering SLA Support');
    }
    setShowCreateTierModal(true);
    setFeedback(null);
  };

  // Derived Analytics Data for Charts and Insights
  const analyticsData = React.useMemo(() => {
    const rawTrends = (metrics?.daily_trends && metrics.daily_trends.length > 0) ? metrics.daily_trends : [
      { date: '2026-10-02', label: 'Oct 02', weekday: 'Fri', diagnoses: 3, new_users: 0 },
      { date: '2026-10-03', label: 'Oct 03', weekday: 'Sat', diagnoses: 5, new_users: 1 },
      { date: '2026-10-04', label: 'Oct 04', weekday: 'Sun', diagnoses: 4, new_users: 0 },
      { date: '2026-10-05', label: 'Oct 05', weekday: 'Mon', diagnoses: 7, new_users: 0 },
      { date: '2026-10-06', label: 'Oct 06', weekday: 'Tue', diagnoses: 6, new_users: 1 },
      { date: '2026-10-07', label: 'Oct 07', weekday: 'Wed', diagnoses: 8, new_users: 0 },
      { date: '2026-10-08', label: 'Oct 08', weekday: 'Thu', diagnoses: metrics?.total_diagnoses_today || 6, new_users: 0 }
    ];

    const totalUsers = users.length || metrics?.total_users || 4;
    const totalMrr = metrics?.monthly_recurring_revenue_lkr || 190000;

    // Per tier breakdown merging allTiers with metrics.tier_distribution
    const tierBreakdown = allTiers.map(t => {
      const subs = metrics?.tier_distribution?.[t.id] || 0;
      const live = tiers?.find(lt => lt.id === t.id) || t;
      const price = live.price_lkr || 0;
      const mrr = subs * price;
      const userShare = totalUsers > 0 ? (subs / totalUsers) * 100 : 0;
      const revShare = totalMrr > 0 ? (mrr / totalMrr) * 100 : 0;
      return {
        id: t.id,
        name: t.name,
        color: t.color,
        badge: live.badge || t.badge,
        subscribers: subs,
        price_lkr: price,
        mrr_lkr: mrr,
        userShare: Math.round(userShare * 10) / 10,
        revShare: Math.round(revShare * 10) / 10,
        limit_display: live.is_unlimited ? 'Unlimited (∞)' : `${live.limit} tries / ${live.period || 'mo'}`,
        isCore: t.isCore
      };
    });

    // Best revenue tier
    const topRevenueTier = [...tierBreakdown].sort((a, b) => b.mrr_lkr - a.mrr_lkr)[0] || tierBreakdown[0];
    // Most popular tier by subscribers
    const topAdoptionTier = [...tierBreakdown].sort((a, b) => b.subscribers - a.subscribers)[0] || tierBreakdown[0];

    const paidSubscribers = tierBreakdown.filter(t => t.id !== 'basic').reduce((sum, t) => sum + t.subscribers, 0);
    const freeSubscribers = tierBreakdown.find(t => t.id === 'basic')?.subscribers || 0;
    const paidConversionRate = totalUsers > 0 ? Math.round((paidSubscribers / totalUsers) * 100) : 0;
    const arpu = paidSubscribers > 0 ? Math.round(totalMrr / paidSubscribers) : 0;

    const zeroSubTier = tierBreakdown.find(t => t.subscribers === 0 && t.id !== 'basic');

    const defaultInsights = [
      {
        type: 'revenue_leader',
        severity: 'success',
        category: 'REVENUE CHAMPION',
        title: `${topRevenueTier.name} Drives Primary Cashflow`,
        metric: `${topRevenueTier.mrr_lkr.toLocaleString()} LKR / mo`,
        observation: `Generates ${topRevenueTier.revShare}% of total platform revenue with ${topRevenueTier.subscribers} active workshop subscribers. High retention indicates optimal pricing fit.`,
        action: `Lock in recurring revenue by introducing an Annual Billing Option with a 15% discount (e.g. ${(topRevenueTier.price_lkr * 12 * 0.85).toLocaleString()} LKR / year).`
      },
      {
        type: 'conversion_opportunity',
        severity: 'info',
        category: 'UPGRADE PIPELINE',
        title: `Basic Free Tier Pipeline (${freeSubscribers} Users)`,
        metric: `${freeSubscribers} Free Accounts`,
        observation: `Independent technicians on Free Basic (${freeSubscribers} workshops) consistently exhaust their 2 daily tries. There is immediate latent demand for higher capacity.`,
        action: 'Trigger an automated modal after the 2nd daily diagnosis offering a 3-day trial of Plus Tier to increase checkout conversion.'
      },
      {
        type: 'pricing_recalibration',
        severity: zeroSubTier ? 'warning' : 'success',
        category: zeroSubTier ? 'CALIBRATION NEEDED' : 'HEALTHY ADOPTION',
        title: zeroSubTier ? `${zeroSubTier.name} Adoption Friction` : 'Balanced Tier Adoption Across All Plans',
        metric: zeroSubTier ? `0 Subscribers (${zeroSubTier.price_lkr.toLocaleString()} LKR)` : '100% Active Coverage',
        observation: zeroSubTier
          ? `The price jump to ${zeroSubTier.name} (${zeroSubTier.price_lkr.toLocaleString()} LKR) represents a noticeable premium, causing busy bays to remain on lower plans.`
          : 'Every active tier has paid workshop subscribers. Current pricing boundaries are well aligned with workshop willingness to pay.',
        action: zeroSubTier
          ? `Calibrate ${zeroSubTier.name} price down to ${(zeroSubTier.price_lkr * 0.84).toLocaleString()} LKR or emphasize Agent 4 multi-distributor parts quoting as a headline ROI generator.`
          : 'Continue monitoring bay capacity and test a high-tier premium add-on module.'
      },
      {
        type: 'expansion_recommendation',
        severity: 'purple',
        category: 'EXPANSION ROADMAP',
        title: 'Launch Commercial Fleet Hub Tier',
        metric: 'High Fleet Demand',
        observation: 'Multi-bay commercial diesel depots and fleet centers in Sri Lanka require 1,200+ monthly diagnostic capacity and multi-seat logins.',
        action: 'Launch a 75,000 LKR / mo plan with 1,200 tries to capture commercial fleet contracts.'
      }
    ];

    const activeInsights = (metrics?.optimization_insights && metrics.optimization_insights.length > 0)
      ? metrics.optimization_insights
      : defaultInsights;

    return {
      trends: rawTrends,
      tierBreakdown,
      topRevenueTier,
      topAdoptionTier,
      totalUsers,
      totalMrr,
      paidSubscribers,
      freeSubscribers,
      paidConversionRate,
      arpu,
      insights: activeInsights
    };
  }, [metrics, allTiers, users, tiers]);

  const handleCreateTierSubmit = async (e) => {
    e.preventDefault();
    if (!newTierName.trim()) {
      setFeedback({ type: 'error', message: 'Tier name is required.' });
      return;
    }
    setCreateLoading(true);
    setFeedback(null);
    try {
      const featList = newTierFeatures
        .split('\n')
        .map(f => f.trim())
        .filter(Boolean);

      const created = await adminCreateTier({
        id: newTierId.trim() || undefined,
        name: newTierName.trim(),
        price_lkr: Number(newTierPrice),
        limit: newTierUnlimited ? 999999 : Number(newTierLimit),
        period: newTierPeriod,
        is_unlimited: newTierUnlimited,
        badge: newTierBadge.trim() || 'CUSTOM',
        color: newTierColor,
        description: newTierDesc.trim(),
        features: featList
      });

      setShowCreateTierModal(false);
      setFeedback({
        type: 'success',
        message: `Successfully created new tier "${created.name}" (${Number(created.price_lkr).toLocaleString()} LKR / ${created.period})!`
      });
      await loadData();
    } catch (err) {
      setFeedback({
        type: 'error',
        message: err.message || 'Failed to create new subscription tier.'
      });
    } finally {
      setCreateLoading(false);
    }
  };

  const handleDeleteTier = async (tierDef) => {
    if (tierDef.isCore || ['basic', 'plus', 'pro', 'ultra'].includes(tierDef.id)) {
      setFeedback({ type: 'error', message: 'Standard core system tiers (Basic, Plus, Pro, Ultra) cannot be deleted.' });
      return;
    }
    const confirmed = window.confirm(`Are you sure you want to permanently delete tier "${tierDef.name}" (${tierDef.id})? This will remove it from all pricing options.`);
    if (!confirmed) return;

    setDeletingTierId(tierDef.id);
    setFeedback(null);
    try {
      await adminDeleteTier(tierDef.id);
      setFeedback({
        type: 'success',
        message: `Tier "${tierDef.name}" was successfully removed from the system.`
      });
      await loadData();
    } catch (err) {
      setFeedback({
        type: 'error',
        message: err.message || 'Failed to delete subscription tier.'
      });
    } finally {
      setDeletingTierId(null);
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
                  {Object.entries(metrics.tier_distribution || {}).reduce((acc, [tId, count]) => (tId === 'basic' ? acc : acc + count), 0)}
                </strong>
                <span className="kpi-subtext">Active accounts across paid tiers</span>
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

        {/* View Switcher Tabs: Directory vs Pricing & Quota Controls */}
        <div className="admin-view-nav-tabs">
          <button
            type="button"
            className={`admin-view-nav-tab ${adminTab === 'directory' ? 'active' : ''}`}
            onClick={() => setAdminTab('directory')}
          >
            <Users size={15} />
            <span>Registered Mechanics Directory</span>
            <span className="tab-count-badge">{users.length} accounts</span>
          </button>
          <button
            type="button"
            className={`admin-view-nav-tab ${adminTab === 'pricing' ? 'active' : ''}`}
            onClick={() => setAdminTab('pricing')}
          >
            <Sliders size={15} />
            <span>Subscription Plans, Pricing & Quotas</span>
            <span className="tab-security-pill">ADMIN CONFIG</span>
          </button>
          <button
            type="button"
            className={`admin-view-nav-tab ${adminTab === 'analytics' ? 'active' : ''}`}
            onClick={() => setAdminTab('analytics')}
          >
            <BarChart3 size={15} />
            <span>Tier Analytics & BI Intelligence</span>
            <span className="tab-security-pill" style={{ background: 'rgba(0, 240, 255, 0.1)', color: '#00F0FF', borderColor: 'rgba(0, 240, 255, 0.3)' }}>NEW BI ENGINE</span>
          </button>
        </div>

        {/* VIEW A: REGISTERED MECHANICS DIRECTORY */}
        {adminTab === 'directory' && (
          <>
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
                    {allTiers.map(t => (
                      <option key={t.id} value={t.id}>{t.name}</option>
                    ))}
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
                        const tierDef = allTiers.find(t => t.id === u.tier) || { color: '#06B6D4', name: u.tier };

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
          </>
        )}

        {/* VIEW B: SUBSCRIPTION PLANS, PRICING & QUOTA CONTROLS */}
        {adminTab === 'pricing' && (
          <div className="admin-pricing-management-section">
            <div className="pricing-section-header-card">
              <div>
                <div className="pricing-section-badge">
                  <Sliders size={13} color="#10B981" />
                  <span>SUBSCRIPTION PRICING & QUOTA ENGINE</span>
                </div>
                <h3 className="pricing-section-title">Configure Tier Prices (LKR) & Quotas</h3>
                <p className="pricing-section-desc">
                  Update subscription fees, create tailored workshop tiers, and calibrate diagnostic quotas. 
                  Price updates immediately recalculate MRR and apply to future and current checkouts.
                  Quota changes immediately update active capacity across all workshops.
                </p>
              </div>
              <div className="pricing-header-actions-group">
                <div className="pricing-section-status-pill">
                  <ShieldCheck size={14} color="#10B981" />
                  <span>Admin Authority Verified</span>
                </div>
                <button
                  type="button"
                  onClick={() => handleOpenCreateTier()}
                  className="create-tier-cta-btn"
                  id="create-new-tier-btn"
                >
                  <Plus size={15} />
                  <span>Create New Tier</span>
                </button>
              </div>
            </div>

            {/* Quick Analytics & Intelligence Banner */}
            <div className="pricing-analytics-quick-banner" onClick={() => setAdminTab('analytics')}>
              <div className="quick-banner-left">
                <div className="quick-banner-icon">
                  <TrendingUp size={16} color="#00F0FF" />
                </div>
                <div>
                  <strong className="quick-banner-title">
                    Tier Intelligence: {analyticsData.topRevenueTier.name} is your #1 Revenue Champion ({analyticsData.topRevenueTier.mrr_lkr.toLocaleString()} LKR / mo • {analyticsData.topRevenueTier.revShare}% MRR)
                  </strong>
                  <p className="quick-banner-sub">
                    Explore interactive 7-day line activity charts, tier adoption breakdown bar charts, and AI capacity update recommendations.
                  </p>
                </div>
              </div>
              <button type="button" className="quick-banner-btn">
                <span>Open Tier BI Analytics</span>
                <ArrowUpRight size={14} />
              </button>
            </div>

            <div className="admin-tiers-grid">
              {allTiers.map(tierDef => {
                const live = tiers?.find(t => t.id === tierDef.id) || tierDef;
                const subscriberCount = metrics?.tier_distribution?.[tierDef.id] || 0;
                const tierMrr = (live.price_lkr || 0) * subscriberCount;

                return (
                  <div key={tierDef.id} className="admin-tier-card" style={{ '--tier-accent': tierDef.color }}>
                    <div className="admin-tier-top-row">
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span className="admin-tier-badge" style={{ color: tierDef.color, borderColor: tierDef.color }}>
                          {live.badge || tierDef.badge}
                        </span>
                        {!tierDef.isCore && (
                          <span className="admin-tier-custom-tag">CUSTOM TIER</span>
                        )}
                      </div>
                      <div className="admin-tier-indicator" style={{ background: tierDef.color }} />
                    </div>

                    <h4 className="admin-tier-name">{tierDef.name}</h4>
                    <p className="admin-tier-desc">{live.description || tierDef.limit_description}</p>

                    <div className="admin-tier-stats-list">
                      <div className="admin-stat-row">
                        <span className="stat-label">Subscription Rate:</span>
                        <strong className="stat-val price-val">
                          {live.price_lkr === 0 ? 'FREE' : `${Number(live.price_lkr).toLocaleString()} LKR`}
                          <span className="stat-cadence">/ {live.period === 'daily' ? 'day' : 'month'}</span>
                        </strong>
                      </div>

                      <div className="admin-stat-row">
                        <span className="stat-label">Diagnostic Quota:</span>
                        <strong className="stat-val quota-val">
                          {live.is_unlimited ? 'Unlimited (∞)' : `${live.limit} tries / ${live.period}`}
                        </strong>
                      </div>

                      <div className="admin-stat-row">
                        <span className="stat-label">Active Technicians:</span>
                        <strong className="stat-val subscriber-val">
                          {subscriberCount} subscribers
                        </strong>
                      </div>

                      <div className="admin-stat-row">
                        <span className="stat-label">Monthly Run Rate:</span>
                        <strong className="stat-val mrr-val">
                          {tierMrr.toLocaleString()} LKR / mo
                        </strong>
                      </div>
                    </div>

                    <div className="admin-tier-card-actions">
                      <button
                        type="button"
                        onClick={() => handleOpenEditTier(tierDef)}
                        className="admin-tier-edit-btn"
                      >
                        <Sliders size={13} />
                        <span>Change Price & Quota</span>
                      </button>

                      {!tierDef.isCore && (
                        <button
                          type="button"
                          onClick={() => handleDeleteTier(tierDef)}
                          disabled={deletingTierId === tierDef.id}
                          className="admin-tier-delete-btn"
                          title={`Permanently delete ${tierDef.name}`}
                        >
                          <Trash2 size={13} />
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}

              {/* Add New Tier Interactive Card Slot */}
              <button
                type="button"
                onClick={handleOpenCreateTier}
                className="add-tier-card-slot"
                id="add-tier-card-slot-btn"
              >
                <div className="add-tier-icon-circle">
                  <Plus size={24} />
                </div>
                <strong className="add-tier-title">Add New Tier</strong>
                <p className="add-tier-sub">Create custom pricing, diagnostic quotas, and tailored feature sets for specialized workshops.</p>
              </button>
            </div>
          </div>
        )}

        {/* VIEW C: TIER ANALYTICS, LINE CHARTS & STRATEGIC BI INTELLIGENCE */}
        {adminTab === 'analytics' && (
          <div className="admin-analytics-management-section">
            {/* Header */}
            <div className="analytics-section-header-card">
              <div>
                <div className="analytics-section-badge">
                  <BarChart3 size={13} color="#00F0FF" />
                  <span>REAL-TIME BI // TIER CAPACITY & ADOPTION ANALYTICS</span>
                </div>
                <h3 className="analytics-section-title">Tier Selection & Diagnostic Velocity Analytics</h3>
                <p className="analytics-section-desc">
                  Interactive line velocity charts, tier adoption distributions, and AI capacity forecasting to identify top-performing tiers and calibrate roadmap updates.
                </p>
              </div>

              <div className="analytics-header-actions">
                <button
                  type="button"
                  onClick={() => setAdminTab('pricing')}
                  className="analytics-header-btn secondary"
                >
                  <Sliders size={13} />
                  <span>Configure Tier Pricing</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleOpenCreateTier()}
                  className="analytics-header-btn primary"
                >
                  <Plus size={14} />
                  <span>Create New Tier</span>
                </button>
              </div>
            </div>

            {/* Row 1: Executive KPI Summary Ribbon */}
            <div className="analytics-kpi-ribbon">
              <div className="analytics-kpi-card best-tier">
                <div className="kpi-top">
                  <span className="kpi-tag-pill green">
                    <Award size={11} />
                    <span>REVENUE CHAMPION</span>
                  </span>
                  <span className="kpi-color-dot" style={{ background: analyticsData.topRevenueTier.color }} />
                </div>
                <strong className="kpi-main-val">{analyticsData.topRevenueTier.name}</strong>
                <div className="kpi-detail-row">
                  <span>Monthly Revenue:</span>
                  <strong>{analyticsData.topRevenueTier.mrr_lkr.toLocaleString()} LKR</strong>
                </div>
                <div className="kpi-detail-row">
                  <span>Revenue Share:</span>
                  <span className="highlight-green">{analyticsData.topRevenueTier.revShare}% of Total MRR</span>
                </div>
              </div>

              <div className="analytics-kpi-card most-adopted">
                <div className="kpi-top">
                  <span className="kpi-tag-pill blue">
                    <Users size={11} />
                    <span>MOST POPULAR TIER</span>
                  </span>
                  <span className="kpi-color-dot" style={{ background: analyticsData.topAdoptionTier.color }} />
                </div>
                <strong className="kpi-main-val">{analyticsData.topAdoptionTier.name}</strong>
                <div className="kpi-detail-row">
                  <span>Active Mechanics:</span>
                  <strong>{analyticsData.topAdoptionTier.subscribers} Subscribers</strong>
                </div>
                <div className="kpi-detail-row">
                  <span>Mechanic Base:</span>
                  <span className="highlight-blue">{analyticsData.topAdoptionTier.userShare}% adoption</span>
                </div>
              </div>

              <div className="analytics-kpi-card conversion-rate">
                <div className="kpi-top">
                  <span className="kpi-tag-pill cyan">
                    <TrendingUp size={11} />
                    <span>PAID CONVERSION RATE</span>
                  </span>
                  <Zap size={14} color="#00F0FF" />
                </div>
                <strong className="kpi-main-val highlight-cyan">{analyticsData.paidConversionRate}%</strong>
                <div className="kpi-detail-row">
                  <span>Paid vs Free:</span>
                  <strong>{analyticsData.paidSubscribers} Paid / {analyticsData.freeSubscribers} Free</strong>
                </div>
                <div className="kpi-detail-row">
                  <span>Pipeline Status:</span>
                  <span className="highlight-cyan">Healthy Mechanic Funnel</span>
                </div>
              </div>

              <div className="analytics-kpi-card arpu">
                <div className="kpi-top">
                  <span className="kpi-tag-pill amber">
                    <DollarSign size={11} />
                    <span>AVG REVENUE PER USER (ARPU)</span>
                  </span>
                  <Activity size={14} color="#F59E0B" />
                </div>
                <strong className="kpi-main-val highlight-amber">
                  {analyticsData.arpu.toLocaleString()} LKR
                </strong>
                <div className="kpi-detail-row">
                  <span>Across Paid Bays:</span>
                  <strong>{analyticsData.paidSubscribers} Workspaces</strong>
                </div>
                <div className="kpi-detail-row">
                  <span>MRR Velocity:</span>
                  <span className="highlight-amber">{analyticsData.totalMrr.toLocaleString()} LKR total</span>
                </div>
              </div>
            </div>

            {/* Row 2: Interactive SVG Line Analytics Chart */}
            <div className="analytics-chart-card line-chart-card">
              <div className="chart-card-header">
                <div>
                  <div className="chart-title-group">
                    <LineChart size={17} color="#00F0FF" />
                    <h4 className="chart-title">7-Day Diagnostic Throughput & Activity Trajectory</h4>
                  </div>
                  <p className="chart-sub">
                    Real-time trajectory of multi-agent triage runs across all active workshops in Sri Lanka.
                  </p>
                </div>

                <div className="chart-metric-toggle-group">
                  <button
                    type="button"
                    className={`metric-toggle-btn ${lineChartMetric === 'diagnoses' ? 'active' : ''}`}
                    onClick={() => setLineChartMetric('diagnoses')}
                  >
                    <Zap size={12} />
                    <span>Autonomous Diagnoses</span>
                  </button>
                  <button
                    type="button"
                    className={`metric-toggle-btn ${lineChartMetric === 'new_users' ? 'active' : ''}`}
                    onClick={() => setLineChartMetric('new_users')}
                  >
                    <Users size={12} />
                    <span>New Mechanics</span>
                  </button>
                </div>
              </div>

              {/* SVG Line Chart Renderer */}
              <div className="svg-chart-viewport-wrap">
                {(() => {
                  const trends = analyticsData.trends;
                  const vals = trends.map(t => t[lineChartMetric]);
                  const maxV = Math.max(...vals, lineChartMetric === 'diagnoses' ? 10 : 3);
                  const W = 720;
                  const H = 220;
                  const pL = 50;
                  const pR = 30;
                  const pT = 25;
                  const pB = 40;
                  const iW = W - pL - pR;
                  const iH = H - pT - pB;

                  const points = trends.map((t, idx) => {
                    const x = pL + (idx / Math.max(1, trends.length - 1)) * iW;
                    const y = pT + iH - (t[lineChartMetric] / maxV) * iH;
                    return { x, y, data: t };
                  });

                  let lineD = `M ${points[0].x},${points[0].y}`;
                  for (let i = 0; i < points.length - 1; i++) {
                    const curr = points[i];
                    const next = points[i + 1];
                    const cpX = (curr.x + next.x) / 2;
                    lineD += ` C ${cpX},${curr.y} ${cpX},${next.y} ${next.x},${next.y}`;
                  }

                  const areaD = `${lineD} L ${points[points.length - 1].x},${pT + iH} L ${points[0].x},${pT + iH} Z`;
                  const gridSteps = [0, 0.33, 0.66, 1];

                  return (
                    <div className="svg-relative-container">
                      <svg viewBox={`0 0 ${W} ${H}`} className="analytics-svg-element" preserveAspectRatio="none">
                        <defs>
                          <linearGradient id="lineAreaGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#00F0FF" stopOpacity="0.4" />
                            <stop offset="70%" stopColor="#00F0FF" stopOpacity="0.08" />
                            <stop offset="100%" stopColor="#00F0FF" stopOpacity="0.0" />
                          </linearGradient>
                          <linearGradient id="lineStrokeGrad" x1="0" y1="0" x2="1" y2="0">
                            <stop offset="0%" stopColor="#00F0FF" />
                            <stop offset="50%" stopColor="#3B82F6" />
                            <stop offset="100%" stopColor="#10B981" />
                          </linearGradient>
                          <filter id="glowFilter" x="-20%" y="-20%" width="140%" height="140%">
                            <feGaussianBlur stdDeviation="3" result="blur" />
                            <feMerge>
                              <feMergeNode in="blur" />
                              <feMergeNode in="SourceGraphic" />
                            </feMerge>
                          </filter>
                        </defs>

                        {/* Horizontal Grid lines */}
                        {gridSteps.map((step, idx) => {
                          const yPos = pT + iH - step * iH;
                          const labelVal = Math.round(step * maxV);
                          return (
                            <g key={idx}>
                              <line
                                x1={pL}
                                y1={yPos}
                                x2={W - pR}
                                y2={yPos}
                                stroke="rgba(255, 255, 255, 0.08)"
                                strokeDasharray="4 4"
                              />
                              <text
                                x={pL - 10}
                                y={yPos + 4}
                                textAnchor="end"
                                fill="var(--text-muted, #94A3B8)"
                                fontSize="11"
                                fontFamily="var(--font-mono)"
                              >
                                {labelVal}
                              </text>
                            </g>
                          );
                        })}

                        {/* Area Gradient Fill */}
                        <path d={areaD} fill="url(#lineAreaGrad)" />

                        {/* Glowing Stroke Curve */}
                        <path
                          d={lineD}
                          fill="none"
                          stroke="url(#lineStrokeGrad)"
                          strokeWidth="3"
                          filter="url(#glowFilter)"
                        />

                        {/* Data Points */}
                        {points.map((pt, idx) => {
                          const isHovered = hoveredPointIndex === idx;
                          return (
                            <g 
                              key={idx}
                              onMouseEnter={() => setHoveredPointIndex(idx)}
                              onMouseLeave={() => setHoveredPointIndex(null)}
                              style={{ cursor: 'pointer' }}
                            >
                              <circle cx={pt.x} cy={pt.y} r="16" fill="transparent" />

                              <circle
                                cx={pt.x}
                                cy={pt.y}
                                r={isHovered ? 7 : 4.5}
                                fill={isHovered ? '#FFFFFF' : '#00F0FF'}
                                stroke={isHovered ? '#00F0FF' : '#11141D'}
                                strokeWidth={isHovered ? 3 : 2}
                                filter={isHovered ? 'url(#glowFilter)' : 'none'}
                                style={{ transition: 'all 0.15s ease' }}
                              />

                              <text
                                x={pt.x}
                                y={pT + iH + 18}
                                textAnchor="middle"
                                fill={isHovered ? '#FFFFFF' : 'var(--text-muted, #94A3B8)'}
                                fontSize="11"
                                fontWeight={isHovered ? 700 : 500}
                                fontFamily="var(--font-mono)"
                              >
                                {pt.data.label}
                              </text>
                              <text
                                x={pt.x}
                                y={pT + iH + 31}
                                textAnchor="middle"
                                fill="rgba(148, 163, 184, 0.6)"
                                fontSize="9.5"
                              >
                                {pt.data.weekday}
                              </text>
                            </g>
                          );
                        })}
                      </svg>

                      {/* Hover Floating HUD Tooltip */}
                      {hoveredPointIndex !== null && points[hoveredPointIndex] && (
                        <div 
                          className="chart-floating-tooltip"
                          style={{
                            left: `${(points[hoveredPointIndex].x / W) * 100}%`,
                            top: `${(points[hoveredPointIndex].y / H) * 100}%`
                          }}
                        >
                          <div className="tooltip-date">
                            {points[hoveredPointIndex].data.label} ({points[hoveredPointIndex].data.weekday})
                          </div>
                          <div className="tooltip-value-row">
                            <span className="tooltip-dot" />
                            <strong>
                              {points[hoveredPointIndex].data[lineChartMetric]}{' '}
                              {lineChartMetric === 'diagnoses' ? 'Autonomous Diagnoses' : 'New Mechanics'}
                            </strong>
                          </div>
                          <div className="tooltip-sub">
                            {lineChartMetric === 'diagnoses' ? 'Full Multi-Agent Particle Pipeline' : 'Onboarded workshop accounts'}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })()}
              </div>

              <div className="chart-footer-stats-bar">
                <div className="chart-stat-chip">
                  <span className="chip-label">7-Day Diagnostic Sum:</span>
                  <strong>{analyticsData.trends.reduce((acc, t) => acc + (t.diagnoses || 0), 0)} runs</strong>
                </div>
                <div className="chart-stat-chip">
                  <span className="chip-label">Peak Daily Velocity:</span>
                  <strong style={{ color: '#00F0FF' }}>
                    {Math.max(...analyticsData.trends.map(t => t.diagnoses || 0))} runs / day
                  </strong>
                </div>
                <div className="chart-stat-chip">
                  <span className="chip-label">System Reliability:</span>
                  <strong style={{ color: '#10B981' }}>99.98% SLA</strong>
                </div>
              </div>
            </div>

            {/* Row 3: Two-Column Charts: Tier Selection Bar Chart + Donut Market Share */}
            <div className="analytics-dual-charts-grid">
              {/* Column A: Tier Selection Bar Chart */}
              <div className="analytics-chart-card bar-chart-card">
                <div className="chart-card-header">
                  <div>
                    <div className="chart-title-group">
                      <BarChart3 size={17} color="#10B981" />
                      <h4 className="chart-title">Tier Selection & Adoption Breakdown</h4>
                    </div>
                    <p className="chart-sub">
                      Comparison of registered mechanics and monthly recurring revenue across all tiers.
                    </p>
                  </div>

                  <div className="chart-metric-toggle-group">
                    <button
                      type="button"
                      className={`metric-toggle-btn ${barChartMetric === 'subscribers' ? 'active' : ''}`}
                      onClick={() => setBarChartMetric('subscribers')}
                    >
                      <Users size={12} />
                      <span>Subscribers</span>
                    </button>
                    <button
                      type="button"
                      className={`metric-toggle-btn ${barChartMetric === 'revenue' ? 'active' : ''}`}
                      onClick={() => setBarChartMetric('revenue')}
                    >
                      <DollarSign size={12} />
                      <span>MRR (LKR)</span>
                    </button>
                  </div>
                </div>

                {/* Tier Bar List */}
                <div className="tier-bars-vertical-list">
                  {(() => {
                    const maxBarVal = Math.max(
                      ...analyticsData.tierBreakdown.map(t => barChartMetric === 'subscribers' ? t.subscribers : t.mrr_lkr),
                      1
                    );

                    return analyticsData.tierBreakdown.map(t => {
                      const val = barChartMetric === 'subscribers' ? t.subscribers : t.mrr_lkr;
                      const fillPct = Math.max(8, Math.round((val / maxBarVal) * 100));
                      const isHovered = hoveredBarId === t.id;

                      return (
                        <div
                          key={t.id}
                          className={`tier-bar-row ${isHovered ? 'hovered' : ''}`}
                          onMouseEnter={() => setHoveredBarId(t.id)}
                          onMouseLeave={() => setHoveredBarId(null)}
                        >
                          <div className="tier-bar-label-col">
                            <div className="tier-bar-title-row">
                              <span className="tier-dot" style={{ background: t.color }} />
                              <strong className="tier-bar-name">{t.name}</strong>
                              <span className="tier-bar-badge" style={{ color: t.color, borderColor: `${t.color}55` }}>
                                {t.badge}
                              </span>
                            </div>
                            <span className="tier-bar-quota">{t.limit_display}</span>
                          </div>

                          <div className="tier-bar-track-col">
                            <div className="tier-bar-track">
                              <div
                                className="tier-bar-fill"
                                style={{
                                  width: `${fillPct}%`,
                                  background: `linear-gradient(90deg, ${t.color}88, ${t.color})`,
                                  boxShadow: isHovered ? `0 0 14px ${t.color}` : 'none'
                                }}
                              />
                            </div>
                          </div>

                          <div className="tier-bar-val-col">
                            <strong className="tier-bar-val-num">
                              {barChartMetric === 'subscribers' ? `${t.subscribers} accounts` : `${t.mrr_lkr.toLocaleString()} LKR`}
                            </strong>
                            <span className="tier-bar-val-pct">
                              {barChartMetric === 'subscribers' ? `${t.userShare}% of users` : `${t.revShare}% of MRR`}
                            </span>
                          </div>
                        </div>
                      );
                    });
                  })()}
                </div>
              </div>

              {/* Column B: Visual Market Share Donut Chart */}
              <div className="analytics-chart-card donut-chart-card">
                <div className="chart-card-header">
                  <div>
                    <div className="chart-title-group">
                      <PieChart size={17} color="#F59E0B" />
                      <h4 className="chart-title">Visual Tier Market Share</h4>
                    </div>
                    <p className="chart-sub">
                      Proportional capacity allocation across active workshop plans.
                    </p>
                  </div>
                </div>

                <div className="donut-and-legend-wrap">
                  {/* SVG Donut Circle */}
                  <div className="donut-svg-box">
                    {(() => {
                      const r = 62;
                      const C = 2 * Math.PI * r;
                      let accumulatedPct = 0;

                      return (
                        <svg viewBox="0 0 160 160" className="donut-svg">
                          <circle
                            cx="80"
                            cy="80"
                            r={r}
                            fill="transparent"
                            stroke="rgba(255, 255, 255, 0.05)"
                            strokeWidth="18"
                          />

                          {analyticsData.tierBreakdown.map(t => {
                            const pct = t.userShare;
                            if (pct <= 0) return null;
                            const strokeLen = (pct / 100) * C;
                            const offset = -((accumulatedPct / 100) * C);
                            accumulatedPct += pct;

                            return (
                              <circle
                                key={t.id}
                                cx="80"
                                cy="80"
                                r={r}
                                fill="transparent"
                                stroke={t.color}
                                strokeWidth="18"
                                strokeDasharray={`${strokeLen} ${C}`}
                                strokeDashoffset={offset}
                                strokeLinecap="round"
                                transform="rotate(-90 80 80)"
                                style={{ transition: 'all 0.3s ease' }}
                              />
                            );
                          })}

                          <text x="80" y="74" textAnchor="middle" fill="#FFFFFF" fontSize="20" fontWeight="900" fontFamily="var(--font-mono)">
                            {analyticsData.totalUsers}
                          </text>
                          <text x="80" y="92" textAnchor="middle" fill="var(--text-muted)" fontSize="9" fontWeight="700" letterSpacing="0.05em">
                            MECHANICS
                          </text>
                        </svg>
                      );
                    })()}
                  </div>

                  {/* Legend Items */}
                  <div className="donut-legend-list">
                    {analyticsData.tierBreakdown.map(t => (
                      <div key={t.id} className="donut-legend-item">
                        <span className="legend-dot" style={{ background: t.color }} />
                        <div className="legend-info">
                          <span className="legend-name">{t.name}</span>
                          <span className="legend-detail">
                            {t.subscribers} accounts • <strong>{t.userShare}%</strong>
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Row 4: AI Tier Optimization & Future Roadmap Advisor */}
            <div className="ai-tier-insights-section">
              <div className="insights-section-header">
                <div className="insights-badge">
                  <Lightbulb size={13} color="#F59E0B" />
                  <span>AI TIER INTELLIGENCE & ROADMAP ADVISOR</span>
                </div>
                <h4 className="insights-title">Strategic Insights: Which Tiers Work Best & What to Update Next</h4>
                <p className="insights-sub">
                  Continuous algorithmic evaluation of Sri Lankan mechanic capacity, tier selection trends, and workshop price elasticity.
                </p>
              </div>

              <div className="ai-insights-cards-grid">
                {analyticsData.insights.map((item, idx) => {
                  const sev = item.severity || 'info';
                  return (
                    <div key={idx} className={`ai-insight-card ${sev}`}>
                      <div className="insight-card-top">
                        <span className={`insight-category-pill ${sev}`}>
                          {sev === 'success' && <Award size={12} />}
                          {sev === 'info' && <Sparkles size={12} />}
                          {sev === 'warning' && <AlertCircle size={12} />}
                          {sev === 'purple' && <Compass size={12} />}
                          <span>{item.category || item.type?.replace('_', ' ').toUpperCase()}</span>
                        </span>
                        <span className="insight-metric-tag">{item.metric}</span>
                      </div>

                      <h5 className="insight-card-title">{item.title}</h5>
                      <p className="insight-card-observation">{item.observation}</p>

                      <div className="insight-card-action-box">
                        <strong>Recommended Future Update:</strong>
                        <span>{item.action}</span>
                      </div>

                      {item.type === 'expansion_recommendation' && (
                        <button
                          type="button"
                          onClick={() => handleOpenCreateTier({
                            name: 'Commercial Fleet Hub',
                            id: 'fleet_hub',
                            price_lkr: 75000,
                            limit: 1200,
                            period: 'monthly',
                            badge: 'COMMERCIAL FLEET',
                            color: '#8B5CF6',
                            description: 'Dedicated high-capacity multi-bay tier for commercial fleet garages & diesel networks.',
                            features: [
                              '1,200 Autonomous Diagnoses per Month',
                              'Priority Multi-Bay Queue Routing Engine',
                              'ChromaDB Dense Semantic Manual Chunk Retrieval',
                              'Automated BOM Multi-Distributor Parts Quoting',
                              'Dedicated 24/7 SLA & Telemetry Stream Export'
                            ]
                          })}
                          className="launch-recommended-tier-btn"
                        >
                          <Plus size={14} />
                          <span>Deploy Recommended Fleet Tier (75k LKR)</span>
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* User Tier Override & Quota Reset Drawer Modal */}
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
                    {allTiers.map(t => (
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

        {/* Tier Pricing & Quota Configuration Modal Drawer */}
        {editingTier && (
          <div className="admin-edit-drawer-backdrop" onClick={() => setEditingTier(null)}>
            <div className="admin-edit-drawer-card tier-edit-card" onClick={e => e.stopPropagation()}>
              <div className="drawer-header">
                <div className="drawer-title-group">
                  <div className="drawer-badge" style={{ color: '#10B981', borderColor: 'rgba(16, 185, 129, 0.35)', background: 'rgba(16, 185, 129, 0.1)' }}>
                    <Sliders size={13} color="#10B981" />
                    <span>ADMIN PRICING & QUOTA CONTROLS</span>
                  </div>
                  <h3 className="drawer-title">Configure {editingTier.name}</h3>
                  <span className="drawer-sub">Update subscription price in LKR and diagnosis capacity limits</span>
                </div>
                <button type="button" onClick={() => setEditingTier(null)} className="auth-close-btn">
                  <X size={18} />
                </button>
              </div>

              <form onSubmit={handleSaveTier} className="drawer-form">
                {/* Price in LKR */}
                <div className="drawer-input-group">
                  <label className="drawer-label">Subscription Price in LKR (Monthly Rate)</label>
                  <div className="drawer-number-input-wrap">
                    <input
                      type="number"
                      min="0"
                      step="500"
                      required
                      value={tierPrice}
                      onChange={e => setTierPrice(Math.max(0, parseInt(e.target.value) || 0))}
                      className="gateway-input"
                      style={{ fontSize: '1.05rem', fontWeight: 800 }}
                    />
                    <span className="currency-unit-tag">LKR</span>
                  </div>
                  <div className="quick-presets-row">
                    <span className="presets-label">Quick Adjust:</span>
                    <button type="button" onClick={() => setTierPrice(p => Math.max(0, p - 5000))} className="preset-pill">-5,000</button>
                    <button type="button" onClick={() => setTierPrice(p => p + 5000)} className="preset-pill">+5,000</button>
                    <button type="button" onClick={() => setTierPrice(p => p + 10000)} className="preset-pill">+10,000</button>
                    {editingTier.id === 'basic' && (
                      <button type="button" onClick={() => setTierPrice(0)} className="preset-pill">Set Free (0 LKR)</button>
                    )}
                  </div>
                </div>

                {/* Quota Limit */}
                <div className="drawer-input-group">
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                    <label className="drawer-label" style={{ margin: 0 }}>Diagnostic Quota Limit</label>
                    <label className="unlimited-toggle-label">
                      <input
                        type="checkbox"
                        checked={tierUnlimited}
                        onChange={e => setTierUnlimited(e.target.checked)}
                      />
                      <span>Unlimited (∞)</span>
                    </label>
                  </div>

                  {!tierUnlimited ? (
                    <>
                      <div className="drawer-number-input-wrap">
                        <input
                          type="number"
                          min="1"
                          step="1"
                          required
                          value={tierLimit}
                          onChange={e => setTierLimit(Math.max(1, parseInt(e.target.value) || 1))}
                          className="gateway-input"
                          style={{ fontSize: '1.05rem', fontWeight: 800 }}
                        />
                        <span className="currency-unit-tag">tries</span>
                      </div>
                      <div className="quick-presets-row">
                        <span className="presets-label">Quick Quota Adjust:</span>
                        <button type="button" onClick={() => setTierLimit(l => Math.max(1, l - 50))} className="preset-pill">-50</button>
                        <button type="button" onClick={() => setTierLimit(l => l + 50)} className="preset-pill">+50</button>
                        <button type="button" onClick={() => setTierLimit(l => l + 100)} className="preset-pill">+100</button>
                        <button type="button" onClick={() => setTierLimit(l => l + 500)} className="preset-pill">+500</button>
                      </div>
                    </>
                  ) : (
                    <div className="unlimited-quota-notice">
                      <Sparkles size={15} color="#FFB800" />
                      <span>Technicians on this plan have unlimited autonomous diagnoses with no caps.</span>
                    </div>
                  )}
                </div>

                {/* Cadence */}
                <div className="drawer-input-group">
                  <label className="drawer-label">Quota Reset Period</label>
                  <div className="cadence-radio-group">
                    <label className={`cadence-option ${tierPeriod === 'monthly' ? 'selected' : ''}`}>
                      <input
                        type="radio"
                        name="tierPeriod"
                        value="monthly"
                        checked={tierPeriod === 'monthly'}
                        onChange={e => setTierPeriod(e.target.value)}
                      />
                      <div>
                        <strong>Monthly Reset</strong>
                        <span>Quota resets on the 1st of each month</span>
                      </div>
                    </label>
                    <label className={`cadence-option ${tierPeriod === 'daily' ? 'selected' : ''}`}>
                      <input
                        type="radio"
                        name="tierPeriod"
                        value="daily"
                        checked={tierPeriod === 'daily'}
                        onChange={e => setTierPeriod(e.target.value)}
                      />
                      <div>
                        <strong>Daily Reset</strong>
                        <span>Quota resets daily at 00:00 UTC</span>
                      </div>
                    </label>
                  </div>
                </div>

                {/* Badge Label */}
                <div className="drawer-input-group">
                  <label className="drawer-label">Badge Label</label>
                  <input
                    type="text"
                    value={tierBadge}
                    onChange={e => setTierBadge(e.target.value)}
                    placeholder="e.g. MOST POPULAR, PROFESSIONAL, ENTERPRISE"
                    className="gateway-input"
                  />
                </div>

                {/* Description */}
                <div className="drawer-input-group">
                  <label className="drawer-label">Plan Description</label>
                  <textarea
                    value={tierDescription}
                    onChange={e => setTierDescription(e.target.value)}
                    placeholder="Brief description displayed on subscription tiers modal..."
                    className="gateway-input"
                    rows={2}
                    style={{ resize: 'vertical' }}
                  />
                </div>

                {/* Live Impact Preview */}
                <div className="tier-impact-summary-box">
                  <div className="impact-row">
                    <span>New Subscription Price:</span>
                    <strong>{Number(tierPrice).toLocaleString()} LKR / {tierPeriod === 'daily' ? 'day' : 'month'}</strong>
                  </div>
                  <div className="impact-row">
                    <span>New Quota Allowance:</span>
                    <strong>{tierUnlimited ? 'Unlimited (∞)' : `${tierLimit} tries / ${tierPeriod}`}</strong>
                  </div>
                  <div className="impact-note">
                    Saving will immediately update the pricing shown to mechanics, adjust gateway charges, and enforce the new quota limit platform-wide.
                  </div>
                </div>

                <div className="drawer-footer-actions">
                  <button
                    type="button"
                    onClick={() => setEditingTier(null)}
                    className="drawer-btn cancel"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={tierSaving}
                    className="drawer-btn save"
                    style={{ background: '#10B981', color: '#FFFFFF' }}
                  >
                    {tierSaving ? 'Applying Changes...' : 'Save & Update Tier Platform-Wide'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* CREATE NEW TIER MODAL DRAWER */}
        {showCreateTierModal && (
          <div className="admin-edit-drawer-backdrop" onClick={() => setShowCreateTierModal(false)}>
            <div className="admin-edit-drawer-card tier-edit-card create-tier-drawer-card" onClick={e => e.stopPropagation()}>
              <div className="drawer-header">
                <div className="drawer-title-group">
                  <div className="drawer-badge" style={{ color: newTierColor, borderColor: `${newTierColor}55`, background: `${newTierColor}15` }}>
                    <Plus size={13} color={newTierColor} />
                    <span>NEW SUBSCRIPTION TIER // ADMIN CONFIG</span>
                  </div>
                  <h3 className="drawer-title">Create New Diagnostic Tier</h3>
                  <span className="drawer-sub">Configure a custom pricing plan, diagnostic capacity limit, and feature permissions.</span>
                </div>
                <button type="button" onClick={() => setShowCreateTierModal(false)} className="auth-close-btn" title="Close drawer">
                  <X size={18} />
                </button>
              </div>

              <form onSubmit={handleCreateTierSubmit} className="drawer-form">
                {/* Tier Name */}
                <div className="drawer-input-group">
                  <label className="drawer-label">Tier Display Name <span style={{ color: '#EF4444' }}>*</span></label>
                  <input
                    type="text"
                    required
                    value={newTierName}
                    onChange={e => {
                      const name = e.target.value;
                      setNewTierName(name);
                      const autoSlug = name.toLowerCase().trim().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
                      if (!newTierId || newTierId.startsWith('tier_') || newTierId.includes('_')) {
                        setNewTierId(autoSlug);
                      }
                    }}
                    placeholder="e.g. Fleet Pro, Performance Hub, Commercial Express"
                    className="gateway-input"
                    style={{ fontSize: '1rem', fontWeight: 700 }}
                  />
                </div>

                {/* Tier ID / Slug */}
                <div className="drawer-input-group">
                  <label className="drawer-label">
                    Tier Identifier Slug <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>(Unique system ID, e.g. fleet_pro)</span>
                  </label>
                  <input
                    type="text"
                    value={newTierId}
                    onChange={e => setNewTierId(e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, ''))}
                    placeholder="Auto-generated from name if left empty"
                    className="gateway-input"
                    style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}
                  />
                </div>

                {/* Accent Color Palette */}
                <div className="drawer-input-group">
                  <label className="drawer-label">Brand Theme Accent Color</label>
                  <div className="color-picker-grid">
                    {[
                      { hex: '#8B5CF6', name: 'Violet' },
                      { hex: '#EC4899', name: 'Rose Pink' },
                      { hex: '#10B981', name: 'Emerald' },
                      { hex: '#F59E0B', name: 'Amber' },
                      { hex: '#00F0FF', name: 'Cyan' },
                      { hex: '#3B82F6', name: 'Electric Blue' },
                      { hex: '#FF5E14', name: 'Racing Coral' },
                      { hex: '#14B8A6', name: 'Teal' }
                    ].map(col => (
                      <button
                        key={col.hex}
                        type="button"
                        onClick={() => setNewTierColor(col.hex)}
                        className={`color-chip-btn ${newTierColor === col.hex ? 'selected' : ''}`}
                        style={{ background: col.hex }}
                        title={col.name}
                      />
                    ))}
                  </div>
                </div>

                {/* Badge Tag */}
                <div className="drawer-input-group">
                  <label className="drawer-label">Badge Tag Label</label>
                  <input
                    type="text"
                    value={newTierBadge}
                    onChange={e => setNewTierBadge(e.target.value)}
                    placeholder="e.g. FLEET SPECIALIST, ENTERPRISE, RECOMMENDED"
                    className="gateway-input"
                  />
                </div>

                {/* Price in LKR */}
                <div className="drawer-input-group">
                  <label className="drawer-label">Subscription Rate in LKR</label>
                  <div className="drawer-number-input-wrap">
                    <input
                      type="number"
                      min="0"
                      step="500"
                      required
                      value={newTierPrice}
                      onChange={e => setNewTierPrice(Math.max(0, parseInt(e.target.value) || 0))}
                      className="gateway-input"
                      style={{ fontSize: '1.05rem', fontWeight: 800 }}
                    />
                    <span className="currency-unit-tag">LKR</span>
                  </div>
                  <div className="quick-presets-row">
                    <span className="presets-label">Quick Adjust:</span>
                    <button type="button" onClick={() => setNewTierPrice(0)} className="preset-pill">Set Free (0 LKR)</button>
                    <button type="button" onClick={() => setNewTierPrice(25000)} className="preset-pill">25,000</button>
                    <button type="button" onClick={() => setNewTierPrice(45000)} className="preset-pill">45,000</button>
                    <button type="button" onClick={() => setNewTierPrice(75000)} className="preset-pill">75,000</button>
                    <button type="button" onClick={() => setNewTierPrice(120000)} className="preset-pill">120,000</button>
                  </div>
                </div>

                {/* Diagnostic Quota */}
                <div className="drawer-input-group">
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                    <label className="drawer-label" style={{ margin: 0 }}>Diagnostic Quota Limit</label>
                    <label className="unlimited-toggle-label">
                      <input
                        type="checkbox"
                        checked={newTierUnlimited}
                        onChange={e => setNewTierUnlimited(e.target.checked)}
                      />
                      <span>Unlimited (∞)</span>
                    </label>
                  </div>

                  {!newTierUnlimited ? (
                    <>
                      <div className="drawer-number-input-wrap">
                        <input
                          type="number"
                          min="1"
                          step="1"
                          required
                          value={newTierLimit}
                          onChange={e => setNewTierLimit(Math.max(1, parseInt(e.target.value) || 1))}
                          className="gateway-input"
                          style={{ fontSize: '1.05rem', fontWeight: 800 }}
                        />
                        <span className="currency-unit-tag">tries</span>
                      </div>
                      <div className="quick-presets-row">
                        <span className="presets-label">Presets:</span>
                        <button type="button" onClick={() => setNewTierLimit(100)} className="preset-pill">100</button>
                        <button type="button" onClick={() => setNewTierLimit(250)} className="preset-pill">250</button>
                        <button type="button" onClick={() => setNewTierLimit(500)} className="preset-pill">500</button>
                        <button type="button" onClick={() => setNewTierLimit(1000)} className="preset-pill">1,000</button>
                        <button type="button" onClick={() => setNewTierLimit(2500)} className="preset-pill">2,500</button>
                      </div>
                    </>
                  ) : (
                    <div className="unlimited-quota-notice">
                      <Sparkles size={15} color="#FFB800" />
                      <span>Technicians on this plan will have unrestricted autonomous diagnoses with zero quota caps.</span>
                    </div>
                  )}
                </div>

                {/* Reset Cadence */}
                <div className="drawer-input-group">
                  <label className="drawer-label">Billing & Quota Cadence</label>
                  <div className="cadence-radio-group">
                    <label className={`cadence-option ${newTierPeriod === 'monthly' ? 'selected' : ''}`}>
                      <input
                        type="radio"
                        name="newTierPeriod"
                        value="monthly"
                        checked={newTierPeriod === 'monthly'}
                        onChange={e => setNewTierPeriod(e.target.value)}
                      />
                      <div>
                        <strong>Monthly Billing & Reset</strong>
                        <span>Renews and resets quota monthly</span>
                      </div>
                    </label>
                    <label className={`cadence-option ${newTierPeriod === 'daily' ? 'selected' : ''}`}>
                      <input
                        type="radio"
                        name="newTierPeriod"
                        value="daily"
                        checked={newTierPeriod === 'daily'}
                        onChange={e => setNewTierPeriod(e.target.value)}
                      />
                      <div>
                        <strong>Daily Reset</strong>
                        <span>Quota resets daily at 00:00 UTC</span>
                      </div>
                    </label>
                  </div>
                </div>

                {/* Description */}
                <div className="drawer-input-group">
                  <label className="drawer-label">Plan Description</label>
                  <textarea
                    value={newTierDesc}
                    onChange={e => setNewTierDesc(e.target.value)}
                    placeholder="Short summary displayed on the checkout and tiers modal..."
                    className="gateway-input"
                    rows={2}
                    style={{ resize: 'vertical' }}
                  />
                </div>

                {/* Features (One per line) */}
                <div className="drawer-input-group">
                  <label className="drawer-label">
                    Features Included <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>(One feature per line)</span>
                  </label>
                  <textarea
                    value={newTierFeatures}
                    onChange={e => setNewTierFeatures(e.target.value)}
                    placeholder="500 Autonomous Diagnoses per Month&#10;Full Multi-Agent Particle Pipeline&#10;SAE DTC Cascade Isolation&#10;Automated BOM Catalog & Parts Resolver"
                    className="gateway-input"
                    rows={4}
                    style={{ resize: 'vertical', fontSize: '0.8rem', lineHeight: 1.5 }}
                  />
                </div>

                {/* Live Card Preview Box */}
                <div className="tier-impact-summary-box" style={{ borderColor: `${newTierColor}55`, background: `${newTierColor}0c` }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ fontSize: '0.72rem', fontWeight: 800, color: newTierColor, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      {newTierBadge || 'CUSTOM TIER'}
                    </span>
                    <span style={{ width: 8, height: 8, borderRadius: '50%', background: newTierColor }} />
                  </div>
                  <div className="impact-row">
                    <span style={{ fontWeight: 800, fontSize: '0.9rem', color: '#FFFFFF' }}>{newTierName || 'New Tier Preview'}</span>
                    <strong style={{ color: '#10B981', fontSize: '0.9rem' }}>
                      {newTierPrice === 0 ? 'FREE' : `${Number(newTierPrice).toLocaleString()} LKR`}
                      <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 400 }}> / {newTierPeriod === 'daily' ? 'day' : 'mo'}</span>
                    </strong>
                  </div>
                  <div className="impact-row">
                    <span>Diagnostic Allowance:</span>
                    <strong>{newTierUnlimited ? 'Unlimited (∞)' : `${newTierLimit} tries / ${newTierPeriod}`}</strong>
                  </div>
                </div>

                <div className="drawer-footer-actions">
                  <button
                    type="button"
                    onClick={() => setShowCreateTierModal(false)}
                    className="drawer-btn cancel"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={createLoading}
                    className="drawer-btn save"
                    style={{ background: newTierColor || '#10B981', color: '#FFFFFF' }}
                  >
                    {createLoading ? 'Deploying Tier to System...' : 'Create & Launch Tier'}
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
