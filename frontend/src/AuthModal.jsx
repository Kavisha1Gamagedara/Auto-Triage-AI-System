import React, { useState } from 'react';
import { 
  X, 
  LogIn, 
  UserPlus, 
  Mail, 
  Lock, 
  User, 
  Phone, 
  Building2, 
  ShieldCheck, 
  AlertCircle, 
  CheckCircle2,
  Sparkles,
  Zap,
  Crown
} from 'lucide-react';
import { useAuth } from './AuthContext';

export default function AuthModal({ isOpen, onClose, initialTab = 'login', onAuthSuccess }) {
  const { login, register } = useAuth();
  const [tab, setTab] = useState(initialTab); // 'login' | 'register'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Form states
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [workshopName, setWorkshopName] = useState('');

  if (!isOpen) return null;

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      if (onAuthSuccess) onAuthSuccess();
      onClose();
    } catch (err) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await register({
        name,
        email,
        phone,
        password,
        workshop_name: workshopName || 'Independent Diagnostic Workshop'
      });
      if (onAuthSuccess) onAuthSuccess();
      onClose();
    } catch (err) {
      setError(err.message || 'Registration failed. Please check required fields.');
    } finally {
      setLoading(false);
    }
  };

  const fillQuickDemo = (demoType) => {
    setError(null);
    if (demoType === 'admin') {
      setTab('login');
      setEmail('admin@autotriage.io');
      setPassword('admin123');
    } else if (demoType === 'basic') {
      setTab('login');
      setEmail('mechanic@workshop.com');
      setPassword('mechanic123');
    } else if (demoType === 'plus') {
      setTab('login');
      setEmail('plus@workshop.com');
      setPassword('plus123');
    }
  };

  return (
    <div className="auth-modal-backdrop" onClick={onClose}>
      <div className="auth-modal-card" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="auth-modal-header">
          <div className="auth-brand-badge">
            <ShieldCheck size={18} color="var(--accent-primary)" />
            <span>AUTO-TRIAGE // ROLE ACCESS GATEWAY</span>
          </div>
          <button type="button" onClick={onClose} className="auth-close-btn" title="Close modal">
            <X size={18} />
          </button>
        </div>

        {/* Guest Warning Pill */}
        <div className="auth-guest-notice">
          <Sparkles size={14} color="#00F0FF" />
          <span>Guest mode is preview only. Log in or create a mechanic account to execute multi-agent diagnoses.</span>
        </div>

        {/* Tab Switcher */}
        <div className="auth-tabs-bar">
          <button
            type="button"
            className={`auth-tab-btn ${tab === 'login' ? 'active' : ''}`}
            onClick={() => { setTab('login'); setError(null); }}
          >
            <LogIn size={14} />
            <span>Sign In</span>
          </button>
          <button
            type="button"
            className={`auth-tab-btn ${tab === 'register' ? 'active' : ''}`}
            onClick={() => { setTab('register'); setError(null); }}
          >
            <UserPlus size={14} />
            <span>Register Account</span>
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="auth-alert-error">
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        {/* Form Body */}
        {tab === 'login' ? (
          <form onSubmit={handleLoginSubmit} className="auth-form-body">
            <div className="auth-input-group">
              <label className="auth-label">
                <Mail size={13} />
                <span>Email Address</span>
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="mechanic@workshop.com"
                className="auth-input"
              />
            </div>

            <div className="auth-input-group">
              <label className="auth-label">
                <Lock size={13} />
                <span>Password</span>
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                className="auth-input"
              />
            </div>

            <button type="submit" disabled={loading} className="auth-submit-btn">
              {loading ? (
                <span>AUTHENTICATING CREDENTIALS...</span>
              ) : (
                <>
                  <LogIn size={15} />
                  <span>SIGN IN TO DIAGNOSTIC WORKSHOP</span>
                </>
              )}
            </button>
          </form>
        ) : (
          <form onSubmit={handleRegisterSubmit} className="auth-form-body">
            <div className="auth-input-group">
              <label className="auth-label">
                <User size={13} />
                <span>Full Name</span>
              </label>
              <input
                type="text"
                required
                value={name}
                onChange={e => setName(e.target.value)}
                placeholder="e.g. Kavisha Gamagedara"
                className="auth-input"
              />
            </div>

            <div className="auth-input-row">
              <div className="auth-input-group">
                <label className="auth-label">
                  <Mail size={13} />
                  <span>Email Address</span>
                </label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="name@domain.com"
                  className="auth-input"
                />
              </div>

              <div className="auth-input-group">
                <label className="auth-label">
                  <Phone size={13} />
                  <span>Telephone Number</span>
                </label>
                <input
                  type="tel"
                  required
                  value={phone}
                  onChange={e => setPhone(e.target.value)}
                  placeholder="+94 77 123 4567"
                  className="auth-input"
                />
              </div>
            </div>

            <div className="auth-input-row">
              <div className="auth-input-group">
                <label className="auth-label">
                  <Building2 size={13} />
                  <span>Workshop / Garage (Optional)</span>
                </label>
                <input
                  type="text"
                  value={workshopName}
                  onChange={e => setWorkshopName(e.target.value)}
                  placeholder="Apex Diagnostic Bay"
                  className="auth-input"
                />
              </div>

              <div className="auth-input-group">
                <label className="auth-label">
                  <Lock size={13} />
                  <span>Password</span>
                </label>
                <input
                  type="password"
                  required
                  minLength={6}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="Min 6 characters"
                  className="auth-input"
                />
              </div>
            </div>

            <div className="auth-free-tier-callout">
              <CheckCircle2 size={15} color="#10B981" />
              <span>Includes <strong>Basic Free Tier</strong>: 2 free autonomous vehicle diagnoses per day!</span>
            </div>

            <button type="submit" disabled={loading} className="auth-submit-btn">
              {loading ? (
                <span>CREATING MECHANIC ACCOUNT...</span>
              ) : (
                <>
                  <UserPlus size={15} />
                  <span>REGISTER & ACTIVATE BASIC TIER</span>
                </>
              )}
            </button>
          </form>
        )}

        {/* 1-Click Fast Sandbox Test Accounts */}
        <div className="auth-demo-footer">
          <span className="auth-demo-title">// 1-CLICK TEST CREDENTIALS:</span>
          <div className="auth-demo-chips-row">
            <button
              type="button"
              onClick={() => fillQuickDemo('basic')}
              className="auth-demo-chip basic"
              title="Mechanic on Free Basic tier (2 tries/day)"
            >
              <Zap size={11} />
              <span>Mechanic (Basic: 2/day)</span>
            </button>
            <button
              type="button"
              onClick={() => fillQuickDemo('plus')}
              className="auth-demo-chip plus"
              title="Mechanic on Plus tier (300 tries/mo)"
            >
              <Sparkles size={11} />
              <span>Mechanic (Plus: 300/mo)</span>
            </button>
            <button
              type="button"
              onClick={() => fillQuickDemo('admin')}
              className="auth-demo-chip admin"
              title="Admin role with full subscription management & user oversight"
            >
              <Crown size={11} />
              <span>Admin (HQ Console)</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
