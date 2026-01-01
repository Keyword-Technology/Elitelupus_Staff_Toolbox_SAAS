'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import {
  HomeIcon,
  ChartBarIcon,
  ServerIcon,
  DocumentTextIcon,
  BookOpenIcon,
  UserGroupIcon,
  ArrowRightOnRectangleIcon,
  TrophyIcon,
  MagnifyingGlassIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';
import { useState } from 'react';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
  { name: 'Sit Counter', href: '/dashboard/counters', icon: ChartBarIcon },
  { name: 'Server Status', href: '/dashboard/servers', icon: ServerIcon },
  { name: 'Steam Lookup', href: '/dashboard/templates', icon: MagnifyingGlassIcon },
  { name: 'Rules', href: '/dashboard/rules', icon: BookOpenIcon },
  { name: 'Staff Roster', href: '/dashboard/staff', icon: UserGroupIcon },
  { name: 'Leaderboard', href: '/dashboard/leaderboard', icon: TrophyIcon },
  { name: 'Server Time', href: '/dashboard/leaderboard/server-time', icon: ClockIcon },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  return (
    <>
      {/* Mobile menu button */}
      <button
        className="md:hidden fixed top-4 left-4 z-50 p-2 bg-dark-card rounded-lg border border-dark-border"
        onClick={() => setIsMobileOpen(!isMobileOpen)}
      >
        <svg
          className="w-6 h-6 text-white"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          {isMobileOpen ? (
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          ) : (
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 6h16M4 12h16M4 18h16"
            />
          )}
        </svg>
      </button>

      {/* Overlay */}
      {isMobileOpen && (
        <div
          className="md:hidden fixed inset-0 bg-black/50 z-30"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-64 bg-dark-card border-r border-dark-border 
                   transform transition-transform duration-200 ease-in-out
                   ${isMobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}`}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="p-6 border-b border-dark-border">
            <h1 className="text-xl font-bold text-white">Staff Toolbox</h1>
            <p className="text-sm text-gray-400">Elitelupus</p>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
            {navigation.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  onClick={() => setIsMobileOpen(false)}
                  className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors
                            ${
                              isActive
                                ? 'bg-primary-600 text-white'
                                : 'text-gray-400 hover:bg-dark-bg hover:text-white'
                            }`}
                >
                  <item.icon className="w-5 h-5" />
                  {item.name}
                </Link>
              );
            })}
          </nav>

          {/* User Section */}
          <div className="p-4 border-t border-dark-border">
            <div className="flex items-center gap-3 mb-3">
              {user?.avatar_url ? (
                <img
                  src={user.avatar_url}
                  alt={user.display_name || user.username}
                  className="w-10 h-10 rounded-full"
                />
              ) : (
                <div className="w-10 h-10 rounded-full bg-primary-600 flex items-center justify-center">
                  <span className="text-white font-medium">
                    {(user?.display_name || user?.username || '?')[0].toUpperCase()}
                  </span>
                </div>
              )}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">
                  {user?.display_name || user?.username}
                </p>
                <p
                  className="text-xs truncate"
                  style={{ color: user?.role_color }}
                >
                  {user?.role}
                </p>
              </div>
            </div>
            <button
              onClick={logout}
              className="flex items-center gap-2 w-full px-3 py-2 text-gray-400 
                       hover:bg-dark-bg hover:text-white rounded-lg transition-colors"
            >
              <ArrowRightOnRectangleIcon className="w-5 h-5" />
              Sign Out
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}
