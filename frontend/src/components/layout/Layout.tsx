// frontend/src/components/layout/Layout.tsx
/**
 * Main Layout Component - Enhanced with Import Navigation
 */

import React, { useState } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import {
  Home,
  Folder,
  FileText,
  Upload,
  Settings,
  Menu,
  X,
  LogOut,
  User,
  Box,
} from 'lucide-react';

// Import auth store with types
import { useAuthStore, type AuthState } from '../../store/authStore';

interface NavItem {
  path: string;
  label: string;
  icon: React.ReactNode;
}

const Layout: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  
  // Get auth state with proper typing
  const user = useAuthStore((state: AuthState) => state.user);
  const logout = useAuthStore((state: AuthState) => state.logout);
  
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems: NavItem[] = [
    { path: '/', label: 'Home', icon: <Home size={20} /> },
    { path: '/workspace', label: 'Workspace', icon: <Folder size={20} /> },
    { path: '/ontology', label: 'Ontology Builder', icon: <Box size={20} /> },
    { path: '/import', label: 'Import Data', icon: <Upload size={20} /> },
    { path: '/settings', label: 'Settings', icon: <Settings size={20} /> },
  ];

  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar - Desktop */}
      <aside
        className={`hidden md:flex flex-col bg-white border-r border-gray-200 transition-all duration-300 ${
          sidebarOpen ? 'w-64' : 'w-20'
        }`}
      >
        {/* Logo */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            {sidebarOpen ? (
              <h1 className="text-xl font-bold text-blue-600">Semantic Architect</h1>
            ) : (
              <span className="text-2xl">🏗️</span>
            )}
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-1 rounded hover:bg-gray-100 transition-colors"
              aria-label={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
            >
              {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4">
          <ul className="space-y-2">
            {navItems.map((item) => (
              <li key={item.path}>
                <Link
                  to={item.path}
                  className={`flex items-center p-3 rounded-lg transition-colors ${
                    isActive(item.path)
                      ? 'bg-blue-50 text-blue-600'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                  title={sidebarOpen ? undefined : item.label}
                >
                  {item.icon}
                  {sidebarOpen && <span className="ml-3">{item.label}</span>}
                </Link>
              </li>
            ))}
          </ul>
        </nav>

        {/* User Section */}
        <div className="p-4 border-t border-gray-200">
          <div className="flex items-center">
            <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center text-white flex-shrink-0">
              <User size={20} />
            </div>
            {sidebarOpen && (
              <div className="ml-3 flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {user?.username || user?.email || 'User'}
                </p>
                <button
                  onClick={handleLogout}
                  className="text-xs text-gray-500 hover:text-gray-700 flex items-center mt-1"
                >
                  <LogOut size={12} className="mr-1" />
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* Mobile Header */}
      <div className="md:hidden fixed top-0 left-0 right-0 bg-white border-b border-gray-200 z-50">
        <div className="flex items-center justify-between p-4">
          <h1 className="text-lg font-bold text-blue-600">Semantic Architect</h1>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 rounded hover:bg-gray-100"
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="border-t border-gray-200 bg-white">
            <nav className="p-4">
              <ul className="space-y-2">
                {navItems.map((item) => (
                  <li key={item.path}>
                    <Link
                      to={item.path}
                      onClick={() => setMobileMenuOpen(false)}
                      className={`flex items-center p-3 rounded-lg transition-colors ${
                        isActive(item.path)
                          ? 'bg-blue-50 text-blue-600'
                          : 'text-gray-700 hover:bg-gray-100'
                      }`}
                    >
                      {item.icon}
                      <span className="ml-3">{item.label}</span>
                    </Link>
                  </li>
                ))}
                <li>
                  <button
                    onClick={() => {
                      setMobileMenuOpen(false);
                      handleLogout();
                    }}
                    className="flex items-center w-full p-3 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
                  >
                    <LogOut size={20} />
                    <span className="ml-3">Logout</span>
                  </button>
                </li>
              </ul>
            </nav>
          </div>
        )}
      </div>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <div className="md:p-0 pt-16 md:pt-0">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default Layout;