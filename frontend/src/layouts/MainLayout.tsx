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
  Activity,
  User as UserIcon,
  ChevronDown,
  Sparkles,
  ExternalLink,
} from 'lucide-react';
import { useUser } from '../context/UserContext';
import { getHealth } from '../api/health';
import { Badge } from '../components/common/Badge';

export const MainLayout: React.FC = () => {
  const { userId, setUserId } = useUser();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [backendStatus, setBackendStatus] = useState<'checking' | 'healthy' | 'offline'>('checking');
  const [demoMode, setDemoMode] = useState<boolean>(true);
  const [activeProvider, setActiveProvider] = useState<string>('demo');
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
          setDemoMode(res.demo_mode ?? true);
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

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col md:flex-row">
      {/* Sidebar for Desktop */}
      <aside className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0 bg-white border-r border-gray-200 z-30">
        <div className="flex flex-col flex-1 min-h-0">
          {/* Logo / Header */}
          <div className="flex items-center gap-3 px-6 h-16 border-b border-gray-100">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-primary-600 to-indigo-500 flex items-center justify-center text-white shadow-sm shadow-primary-200">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <span className="font-bold text-gray-900 tracking-tight text-lg">Sahayak<span className="text-primary-600">AI</span></span>
              <p className="text-2xs text-gray-400 font-medium leading-none">Student Assistant</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  end={item.path === '/'}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                      isActive
                        ? 'bg-primary-50 text-primary-700 font-semibold shadow-2xs'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100/70'
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
          <div className="p-4 border-t border-gray-100 bg-gray-50/50 space-y-3">
            <div className="bg-white p-3 rounded-lg border border-gray-200 shadow-2xs text-xs space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-gray-500 flex items-center gap-1.5 font-medium">
                  <Activity className="w-3.5 h-3.5 text-gray-400" />
                  API Status:
                </span>
                <Badge
                  variant={backendStatus === 'healthy' ? 'success' : backendStatus === 'checking' ? 'warning' : 'danger'}
                  size="sm"
                >
                  {backendStatus === 'healthy' ? 'Connected' : backendStatus === 'checking' ? 'Checking' : 'Offline'}
                </Badge>
              </div>

              <div className="flex items-center justify-between text-2xs text-gray-500 pt-1 border-t border-gray-100">
                <span>AI Provider:</span>
                <span className="font-semibold text-gray-700 uppercase tracking-wider">{activeProvider}</span>
              </div>
            </div>

            <div className="text-2xs text-gray-400 text-center">
              SahayakAI v1.0 • Enterprise Edition
            </div>
          </div>
        </div>
      </aside>

      {/* Main Container */}
      <div className="flex-1 md:pl-64 flex flex-col min-w-0">
        {/* Top Navbar */}
        <header className="sticky top-0 z-20 bg-white/90 backdrop-blur-md border-b border-gray-200 h-16 flex items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-3">
            <button
              type="button"
              className="md:hidden p-2 rounded-lg text-gray-500 hover:bg-gray-100 focus:outline-none"
              onClick={() => setMobileMenuOpen(true)}
              aria-label="Open sidebar"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div className="hidden sm:block">
              <h2 className="text-sm font-semibold text-gray-800">
                Unified Student Learning & Career Platform
              </h2>
            </div>
          </div>

          {/* User selector & Controls */}
          <div className="flex items-center gap-3">
            {/* Dev Mode User Switcher */}
            <div className="flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-lg px-2.5 py-1.5 shadow-2xs">
              <UserIcon className="w-3.5 h-3.5 text-gray-500" />
              <label htmlFor="user-select" className="text-xs text-gray-500 font-medium hidden sm:inline">
                Dev User:
              </label>
              <select
                id="user-select"
                value={userId}
                onChange={(e) => setUserId(Number(e.target.value))}
                className="bg-transparent text-xs font-semibold text-gray-800 border-none focus:outline-none cursor-pointer pr-1"
              >
                <option value={1}>User #1 (Default)</option>
                <option value={2}>User #2 (Student B)</option>
                <option value={3}>User #3 (Recruiter)</option>
                <option value={42}>User #42 (Testing)</option>
              </select>
            </div>

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
        {mobileMenuOpen && (
          <div className="fixed inset-0 z-40 md:hidden flex">
            <div
              className="fixed inset-0 bg-gray-600 bg-opacity-50 backdrop-blur-xs transition-opacity"
              onClick={() => setMobileMenuOpen(false)}
            />
            <div className="relative flex-1 flex flex-col max-w-xs w-full bg-white shadow-xl">
              <div className="flex items-center justify-between px-6 h-16 border-b border-gray-100">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-primary-600" />
                  <span className="font-bold text-gray-900 text-lg">SahayakAI</span>
                </div>
                <button
                  type="button"
                  className="p-1 rounded-md text-gray-400 hover:text-gray-500"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

              <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  return (
                    <NavLink
                      key={item.path}
                      to={item.path}
                      end={item.path === '/'}
                      className={({ isActive }) =>
                        `flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium ${
                          isActive
                            ? 'bg-primary-50 text-primary-700 font-semibold'
                            : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100/70'
                        }`
                      }
                    >
                      <Icon className="w-4 h-4 shrink-0" />
                      <span>{item.label}</span>
                    </NavLink>
                  );
                })}
              </nav>

              <div className="p-4 border-t border-gray-100 bg-gray-50">
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
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
