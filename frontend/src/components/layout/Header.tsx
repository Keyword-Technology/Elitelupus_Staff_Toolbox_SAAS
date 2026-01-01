'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { useWebSocket } from '@/contexts/WebSocketContext';
import { usePageActions } from '@/contexts/PageActionsContext';
import {
  BellIcon,
  Cog6ToothIcon,
  ArrowRightOnRectangleIcon,
  UserCircleIcon,
  WrenchScrewdriverIcon,
} from '@heroicons/react/24/outline';

export function Header() {
  const { user, logout, hasMinRole } = useAuth();
  const { isConnected } = useWebSocket();
  const { actions } = usePageActions();
  const pathname = usePathname();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Get page title based on pathname
  const getPageInfo = () => {
    if (pathname === '/dashboard') return { title: 'Dashboard', subtitle: 'Overview of your staff activity' };
    if (pathname === '/dashboard/counters') return { title: 'Counter Manager', subtitle: 'Manage your sit and ticket counters' };
    if (pathname === '/dashboard/servers') return { title: 'Server Status', subtitle: 'Monitor game servers and player activity' };
    if (pathname?.startsWith('/dashboard/servers/')) return { title: 'Server Statistics', subtitle: 'Detailed server analytics' };
    if (pathname === '/dashboard/templates') return { title: 'Steam Lookup & Actions', subtitle: 'Look up Steam profiles, check bans, and manage templates' };
    if (pathname === '/dashboard/rules') return { title: 'Server Rules', subtitle: 'Browse and search server rules' };
    if (pathname === '/dashboard/staff') return { title: 'Staff Roster', subtitle: 'Manage staff members and roles' };
    if (pathname === '/dashboard/staff/legacy') return { title: 'Legacy Staff', subtitle: 'View inactive staff members' };
    if (pathname === '/dashboard/leaderboard/server-time') return { title: 'Server Time Leaderboard', subtitle: 'Top staff by time on server' };
    if (pathname === '/dashboard/leaderboard') return { title: 'Leaderboard', subtitle: 'Top performing staff members' };
    if (pathname === '/dashboard/settings') return { title: 'Profile Settings', subtitle: 'Manage your account settings' };
    if (pathname === '/dashboard/system-settings') return { title: 'System Settings', subtitle: 'Configure application settings' };
    return { title: 'Dashboard', subtitle: '' };
  };

  const pageInfo = getPageInfo();

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="bg-dark-card border-b border-dark-border px-4 md:px-6 py-4">
      <div className="flex items-center justify-between">
        {/* Page Title */}
        <div className="md:ml-0 ml-12">
          <h1 className="text-xl font-bold text-white">{pageInfo.title}</h1>
          {pageInfo.subtitle && (
            <p className="text-sm text-gray-400 mt-0.5">{pageInfo.subtitle}</p>
          )}
        </div>

        <div className="flex items-center gap-4">
          {/* Connection Status */}
          <div className="flex items-center gap-2">
            <div
              className={`w-2 h-2 rounded-full ${
                isConnected ? 'bg-green-500' : 'bg-red-500'
              }`}
            />
            <span className="text-sm text-gray-400 hidden sm:inline">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>

          {/* Page-specific actions */}
          {actions && <div className="flex items-center gap-3">{actions}</div>}

          {/* Notifications */}
          <button className="p-2 text-gray-400 hover:text-white transition-colors">
            <BellIcon className="w-6 h-6" />
          </button>

          {/* User Profile Dropdown */}
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="flex items-center gap-3 hover:opacity-80 transition-opacity"
            >
              <div className="text-right hidden sm:block">
                <p className="text-sm font-medium text-white">
                  {user?.display_name || user?.username}
                </p>
                <p className="text-xs" style={{ color: user?.role_color }}>
                  {user?.role}
                </p>
              </div>
              {user?.avatar_url ? (
                <img
                  src={user.avatar_url}
                  alt={user.display_name || user.username}
                  className="w-10 h-10 rounded-full ring-2 ring-transparent hover:ring-primary-500 transition-all"
                />
              ) : (
                <div className="w-10 h-10 rounded-full bg-primary-600 flex items-center justify-center ring-2 ring-transparent hover:ring-primary-500 transition-all">
                  <span className="text-white font-medium">
                    {(user?.display_name || user?.username || '?')[0].toUpperCase()}
                  </span>
                </div>
              )}
            </button>

            {/* Dropdown Menu */}
            {dropdownOpen && (
              <div className="absolute right-0 mt-2 w-56 bg-dark-card border border-dark-border rounded-lg shadow-lg py-1 z-50">
                {/* User info header */}
                <div className="px-4 py-3 border-b border-dark-border">
                  <p className="text-sm font-medium text-white truncate">
                    {user?.display_name || user?.username}
                  </p>
                  <p className="text-xs text-gray-400 truncate">
                    {user?.email}
                  </p>
                </div>

                {/* Menu Items */}
                <div className="py-1">
                  <Link
                    href="/dashboard/settings"
                    onClick={() => setDropdownOpen(false)}
                    className="flex items-center gap-3 px-4 py-2 text-sm text-gray-300 hover:bg-dark-bg hover:text-white transition-colors"
                  >
                    <UserCircleIcon className="w-5 h-5" />
                    Profile Settings
                  </Link>

                  {/* Admin-only: System Settings */}
                  {hasMinRole(70) && (
                    <Link
                      href="/dashboard/system-settings"
                      onClick={() => setDropdownOpen(false)}
                      className="flex items-center gap-3 px-4 py-2 text-sm text-gray-300 hover:bg-dark-bg hover:text-white transition-colors"
                    >
                      <WrenchScrewdriverIcon className="w-5 h-5" />
                      System Settings
                    </Link>
                  )}
                </div>

                {/* Logout */}
                <div className="border-t border-dark-border py-1">
                  <button
                    onClick={() => {
                      setDropdownOpen(false);
                      logout();
                    }}
                    className="flex items-center gap-3 px-4 py-2 text-sm text-red-400 hover:bg-dark-bg hover:text-red-300 w-full transition-colors"
                  >
                    <ArrowRightOnRectangleIcon className="w-5 h-5" />
                    Sign Out
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
