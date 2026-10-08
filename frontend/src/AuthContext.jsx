import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('autotriage_token') || null);
  const [loading, setLoading] = useState(true);
  const [tiers, setTiers] = useState([]);

  // Fetch live subscription tier pricing & limits
  const fetchTiers = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/subscriptions/tiers`);
      if (res.ok) {
        const data = await res.json();
        setTiers(data);
        return data;
      }
    } catch (err) {
      console.warn('[AuthContext] Could not fetch subscription tiers:', err);
    }
    return [];
  }, []);

  // Refresh current user profile and quota from backend
  const refreshUser = useCallback(async (activeToken = token) => {
    if (!activeToken) {
      setUser(null);
      setLoading(false);
      return null;
    }
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
        headers: {
          'Authorization': `Bearer ${activeToken}`
        }
      });
      if (res.ok) {
        const userData = await res.json();
        setUser(userData);
        return userData;
      } else {
        // Token expired or invalid
        localStorage.removeItem('autotriage_token');
        setToken(null);
        setUser(null);
        return null;
      }
    } catch (err) {
      console.warn('[AuthContext] Backend offline or unreachable:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    refreshUser();
    fetchTiers();
  }, [refreshUser, fetchTiers]);

  // Login handler
  const login = async (email, password) => {
    const res = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || 'Authentication failed. Please verify credentials.');
    }
    localStorage.setItem('autotriage_token', data.token);
    setToken(data.token);
    setUser(data.user);
    return data.user;
  };

  // Registration handler (requires name, email, phone, password)
  const register = async ({ name, email, phone, password, workshop_name }) => {
    const res = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, phone, password, workshop_name })
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || 'Registration failed. Please check your details.');
    }
    localStorage.setItem('autotriage_token', data.token);
    setToken(data.token);
    setUser(data.user);
    return data.user;
  };

  // Logout handler
  const logout = () => {
    localStorage.removeItem('autotriage_token');
    setToken(null);
    setUser(null);
  };

  // Developer Sandbox Payment Simulation
  const simulatePayment = async ({ tier, payment_method = 'card', test_card_number, test_card_name, test_cvv, should_fail = false }) => {
    if (!token) throw new Error('Authentication required for checkout.');
    const res = await fetch(`${API_BASE_URL}/api/v1/subscriptions/checkout-simulate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        tier,
        payment_method,
        test_card_number,
        test_card_name,
        test_cvv,
        should_fail
      })
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || 'Payment gateway simulation failed.');
    }
    if (data.success && data.user) {
      setUser(data.user);
    }
    return data;
  };

  // Admin: Fetch all users
  const fetchAdminUsers = async (search = '', tier = '') => {
    if (!token) throw new Error('Admin authorization required.');
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (tier) params.append('tier', tier);
    const res = await fetch(`${API_BASE_URL}/api/v1/admin/users?${params.toString()}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail?.message || data.detail || 'Failed to fetch users');
    return data;
  };

  // Admin: Update user subscription
  const adminUpdateSubscription = async (userId, tier, resetUsage = false) => {
    if (!token) throw new Error('Admin authorization required.');
    const res = await fetch(`${API_BASE_URL}/api/v1/admin/users/${userId}/subscription`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ tier, reset_usage: resetUsage })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to update subscription');
    // If the admin updated their own account, refresh
    if (user?.id === userId) {
      setUser(data);
    }
    return data;
  };

  // Admin: Fetch real-time metrics
  const fetchAdminMetrics = async () => {
    if (!token) throw new Error('Admin authorization required.');
    const res = await fetch(`${API_BASE_URL}/api/v1/admin/metrics`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail?.message || data.detail || 'Failed to fetch metrics');
    return data;
  };

  // Admin: Update tier pricing & quota limits
  const adminUpdateTier = async (tierId, updates) => {
    if (!token) throw new Error('Admin authorization required.');
    const res = await fetch(`${API_BASE_URL}/api/v1/admin/tiers/${tierId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(updates)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to update subscription tier.');
    await fetchTiers();
    await refreshUser();
    return data;
  };

  const value = {
    user,
    token,
    loading,
    isAuthenticated: Boolean(user),
    isAdmin: user?.role === 'admin',
    quota: user?.quota || null,
    tiers,
    fetchTiers,
    adminUpdateTier,
    login,
    register,
    logout,
    refreshUser,
    simulatePayment,
    fetchAdminUsers,
    adminUpdateSubscription,
    fetchAdminMetrics,
    API_BASE_URL
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
