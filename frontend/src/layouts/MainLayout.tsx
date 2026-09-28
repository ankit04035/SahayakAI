import React, { useState, useEffect } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  MessageSquare,
  Award,
  GraduationCap,
  Compass,
  Menu,
  X,
  User as UserIcon,
  Sparkles,
  ExternalLink,
  ArrowRight,
  LogIn,
  LogOut,
  UserRoundPlus,
} from 'lucide-react';
import { useUser } from '../context/UserContext';
import { getHealth } from '../api/health';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { Modal } from '../components/common/Modal';

export const MainLayout: React.FC = () => {
  const { userId, user, loading: authLoading, register, login, logout } = useUser();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [backendStatus, setBackendStatus] = useState<'checking' | 'healthy' | 'offline'>('checking');
  const [activeProvider, setActiveProvider] = useState<string>('demo');
  const [authMode, setAuthMode] = useState<'register' | 'login' | null>(null);
  const [authName, setAuthName] = useState('');
  const [authEmail, setAuthEmail] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [authError, setAuthError] = useState<string | null>(null);
  const [authSubmitting, setAuthSubmitting] = useState(false);
  const location = useLocation();

  // Close mobile menu upon navigation
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  // Periodic health check
  useEffect(() => {
    let isMounted = true;
    const checkHealth = async () => {
      try {
        const res = await getHealth();
        if (isMounted) {
          setBackendStatus(res.status === 'ok' ? 'healthy' : 'offline');
          setActiveProvider(res.ai_provider || 'demo');
        }
      } catch {
        if (isMounted) {
          setBackendStatus('offline');
        }
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const navItems = [
    { label: 'Dashboard', path: '/', icon: LayoutDashboard },
    { label: 'Study Documents', path: '/documents', icon: FileText },
    { label: 'Study Assistant', path: '/chat', icon: MessageSquare },
    { label: 'Resume Analyzer', path: '/resumes', icon: Award },
    { label: 'Career Profile', path: '/career/profile', icon: GraduationCap },
    { label: 'Career Roadmap', path: '/career/roadmap', icon: Compass },
  ];

  const handleAuthSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!authMode) return;
    setAuthSubmitting(true);
    setAuthError(null);
    try {
      if (authMode === 'register') {
        await register({ name: authName.trim(), email: authEmail.trim(), password: authPassword });
      } else {
        await login({ email: authEmail.trim(), password: authPassword });
      }
      setAuthMode(null);
      setAuthPassword('');
      setAuthName('');
    } catch (error) {
      setAuthError(error instanceof Error ? error.message : 'Unable to sign in. Please try again.');
    } finally {
      setAuthSubmitting(false);
    }
  };

  return (
    <div className="app-shell min-h-screen flex flex-col md:flex-row">
      {/* Sidebar for Desktop */}
      {user && (
      <aside className="app-sidebar hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0 border-r z-30">
        <div className="flex flex-col flex-1 min-h-0">
          {/* Logo / Header */}
          <div className="brand-row flex items-center gap-3 px-6 h-16 border-b">
            <div className="brand-mark shadow-sm">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <span className="brand-name">Sahayak<span>AI</span></span>
              <p className="brand-subtitle">Student Assistant</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="app-nav flex-1 px-3 py-4 space-y-1 overflow-y-auto">
            <div className="sidebar-label">Workspace</div>
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  end={item.path === '/'}
                  className={({ isActive }) =>
                    `app-nav-link flex items-center gap-3 px-3.5 py-2.5 text-sm font-medium transition-all ${
                      isActive
                        ? 'is-active font-semibold'
                        : ''
                    }`
                  }
                >
                  <Icon className="w-4 h-4 shrink-0" />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </nav>

          {/* Footer / System Status */}
          <div className="sidebar-foot p-4 border-t space-y-3">
            <div className="sidebar-health text-xs space-y-2">
              <div className="flex items-center justify-between">
                <span className="sidebar-status flex items-center gap-2 font-medium">
                  <span className={`health-dot ${backendStatus === 'healthy' ? 'is-healthy' : ''}`} />
                  API connection
                </span>
                <Badge
                  variant={backendStatus === 'healthy' ? 'success' : backendStatus === 'checking' ? 'warning' : 'danger'}
                  size="sm"
                >
                  {backendStatus === 'healthy' ? 'Connected' : backendStatus === 'checking' ? 'Checking' : 'Offline'}
                </Badge>
              </div>

              <div className="flex items-center justify-between text-2xs text-gray-300 pt-1 border-t border-white/10">
                <span>AI Provider:</span>
                <span className="font-semibold text-white uppercase">{activeProvider}</span>
              </div>
            </div>

            <div className="text-2xs text-gray-400 text-center">
              SahayakAI v1.0 • Enterprise Edition
            </div>
          </div>
        </div>
      </aside>
      )}

      {/* Main Container */}
      <div className={`app-main flex-1 ${user ? 'md:pl-64' : ''} flex flex-col min-w-0`}>
        {/* Top Navbar */}
        <header className="topbar sticky top-0 z-20 backdrop-blur-md border-b flex items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-3">
            {user && (
              <button
                type="button"
                className="icon-button md:hidden"
                onClick={() => setMobileMenuOpen(true)}
                aria-label="Open sidebar"
              >
                <Menu className="w-5 h-5" />
              </button>
            )}
            <div className="hidden sm:block">
              <div className="topbar-kicker">SahayakAI workspace</div>
              <h2 className="topbar-title">
                {user ? navItems.find((item) => item.path === location.pathname)?.label || 'Your workspace' : 'Study and career companion'}
              </h2>
            </div>
          </div>

          {/* User selector & Controls */}
          <div className="flex items-center gap-2 sm:gap-3">
            {user ? (
              <>
                <div className="account-chip hidden sm:flex items-center gap-2">
                  <UserIcon className="w-4 h-4" />
                  <span className="account-chip-name">{user.name}</span>
                </div>
                <Button variant="ghost" size="sm" onClick={() => void logout()} leftIcon={<LogOut className="w-4 h-4" />}>
                  <span className="hidden sm:inline">Sign out</span>
                </Button>
              </>
            ) : (
              <>
                <button type="button" className="account-link" onClick={() => { setAuthMode('login'); setAuthError(null); }}>
                  <LogIn className="w-4 h-4" /> <span>Sign in</span>
                </button>
                <button type="button" className="account-register" onClick={() => { setAuthMode('register'); setAuthError(null); }}>
                  <UserRoundPlus className="w-4 h-4" /> <span>Register</span>
                </button>
              </>
            )}

            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="hidden lg:flex items-center gap-1 text-xs font-medium text-gray-500 hover:text-primary-600 transition"
              title="FastAPI Swagger Documentation"
            >
              <span>Swagger</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </header>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && user && (
          <div className="fixed inset-0 z-40 md:hidden flex">
            <div
              className="fixed inset-0 bg-gray-600 bg-opacity-50 backdrop-blur-xs transition-opacity"
              onClick={() => setMobileMenuOpen(false)}
            />
            <div className="app-mobile-menu relative flex-1 flex flex-col max-w-xs w-full shadow-xl">
              <div className="flex items-center justify-between px-6 h-16 border-b border-gray-100">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-lime-300" />
                  <span className="font-bold text-white text-lg">SahayakAI</span>
                </div>
                <button
                  type="button"
                  className="p-1 rounded-md text-gray-400 hover:text-gray-500"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

              <nav className="app-nav flex-1 px-3 py-4 space-y-1 overflow-y-auto">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  return (
                    <NavLink
                      key={item.path}
                      to={item.path}
                      end={item.path === '/'}
                      className={({ isActive }) =>
                        `app-nav-link flex items-center gap-3 px-3.5 py-2.5 text-sm font-medium ${
                          isActive
                            ? 'is-active font-semibold'
                            : ''
                        }`
                      }
                    >
                      <Icon className="w-4 h-4 shrink-0" />
                      <span>{item.label}</span>
                    </NavLink>
                  );
                })}
              </nav>

              <div className="sidebar-foot p-4 border-t">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-500">API Status:</span>
                  <Badge variant={backendStatus === 'healthy' ? 'success' : 'danger'} size="sm">
                    {backendStatus}
                  </Badge>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Page Content */}
        {authLoading ? (
          <main className="page-content auth-loading flex-1 w-full mx-auto" aria-live="polite">Checking your account…</main>
        ) : user ? (
          <main className="page-content flex-1 max-w-7xl w-full mx-auto">
            <Outlet />
          </main>
        ) : (
          <main className="auth-gate flex-1 w-full">
            <section className="auth-gate-content">
              <div className="auth-kicker"><span className="dashboard-context-mark" /> YOUR LEARNING WORKSPACE</div>
              <h1>Make room for your next big idea.</h1>
              <p>Create an account to keep your study materials, chats, resume reviews, and career plans together.</p>
              <div className="auth-gate-actions">
                <button type="button" className="account-register" onClick={() => { setAuthMode('register'); setAuthError(null); }}>
                  <UserRoundPlus className="w-4 h-4" /> Create account
                </button>
                <button type="button" className="auth-gate-secondary" onClick={() => { setAuthMode('login'); setAuthError(null); }}>
                  I already have an account <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </section>
            <aside className="auth-gate-aside">
              <span>YOUR SPACE, IN ONE PLACE</span>
              <strong>Study smarter.<br />Build what’s next.</strong>
              <p>Documents · Assistant · Resume · Roadmap</p>
            </aside>
          </main>
        )}
      </div>

      <Modal
        isOpen={authMode !== null}
        onClose={() => !authSubmitting && setAuthMode(null)}
        title={authMode === 'register' ? 'Create your account' : 'Welcome back'}
        description={authMode === 'register' ? 'Your learning workspace starts here.' : 'Sign in to continue to your workspace.'}
        maxWidth="sm"
      >
        <form className="auth-form" onSubmit={handleAuthSubmit}>
          {authError && <div className="auth-error" role="alert">{authError}</div>}
          {authMode === 'register' && (
            <label className="auth-field">
              <span>Full name</span>
              <input autoComplete="name" value={authName} onChange={(event) => setAuthName(event.target.value)} required maxLength={255} />
            </label>
          )}
          <label className="auth-field">
            <span>Email address</span>
            <input type="email" autoComplete="email" value={authEmail} onChange={(event) => setAuthEmail(event.target.value)} required />
          </label>
          <label className="auth-field">
            <span>Password</span>
            <input
              type="password"
              autoComplete={authMode === 'register' ? 'new-password' : 'current-password'}
              value={authPassword}
              onChange={(event) => setAuthPassword(event.target.value)}
              minLength={authMode === 'register' ? 12 : 1}
              maxLength={128}
              required
            />
            {authMode === 'register' && <small>Use at least 12 characters.</small>}
          </label>
          <div className="auth-form-footer">
            <button type="button" className="auth-switch" onClick={() => { setAuthMode(authMode === 'register' ? 'login' : 'register'); setAuthError(null); }}>
              {authMode === 'register' ? 'Already registered? Sign in' : 'New here? Create an account'}
            </button>
            <Button type="submit" isLoading={authSubmitting}>
              {authMode === 'register' ? 'Create account' : 'Sign in'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
