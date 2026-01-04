'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { useState, useEffect } from 'react';
import { sitAPI } from '@/lib/api';
import { Disclosure } from '@headlessui/react';
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
  VideoCameraIcon,
  EyeIcon,
  SparklesIcon,
  ChevronDownIcon,
  LightBulbIcon,
} from '@heroicons/react/24/outline';

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  requiresOCR?: boolean;
}

interface NavGroup {
  name: string;
  icon: React.ComponentType<{ className?: string }>;
  items: NavItem[];
}

type NavigationItem = NavItem | NavGroup;

function isNavGroup(item: NavigationItem): item is NavGroup {
  return 'items' in item;
}

const navigation: NavigationItem[] = [
  { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
  {
    name: 'Sit Tracking',
    icon: ChartBarIcon,
    items: [
      { name: 'Sit Counter', href: '/dashboard/counters', icon: ChartBarIcon },
      { name: 'OCR Sits', href: '/dashboard/ocr-sits', icon: EyeIcon, requiresOCR: true },
      { name: 'Sit History', href: '/dashboard/sits', icon: VideoCameraIcon },
    ],
  },
  {
    name: 'Statistics',
    icon: TrophyIcon,
    items: [
      { name: 'Leaderboard', href: '/dashboard/leaderboard', icon: TrophyIcon },
      { name: 'Server Time', href: '/dashboard/leaderboard/server-time', icon: ClockIcon },
      { name: 'Recent Promotions', href: '/dashboard/recent-promotions', icon: SparklesIcon },
    ],
  },
  { name: 'Server Status', href: '/dashboard/servers', icon: ServerIcon },
  { name: 'Steam Lookup', href: '/dashboard/templates', icon: MagnifyingGlassIcon },
  { name: 'Rules', href: '/dashboard/rules', icon: BookOpenIcon },
  { name: 'Staff Roster', href: '/dashboard/staff', icon: UserGroupIcon },
  { name: 'Future Features', href: '/dashboard/features', icon: LightBulbIcon },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const [ocrEnabled, setOcrEnabled] = useState(false);

  // Check if OCR feature is enabled system-wide
  useEffect(() => {
    const checkOCREnabled = async () => {
      try {
        const response = await sitAPI.isEnabled();
        setOcrEnabled(response.data?.system_enabled && response.data?.ocr_system_enabled);
      } catch {
        setOcrEnabled(false);
      }
    };
    checkOCREnabled();
  }, []);

  // Filter navigation based on feature flags
  const filteredNavigation = navigation.map(item => {
    if (isNavGroup(item)) {
      // Filter items within groups
      const filteredItems = item.items.filter(subItem => {
        if (subItem.requiresOCR && !ocrEnabled) {
          return false;
        }
        return true;
      });
      return { ...item, items: filteredItems };
    }
    return item;
  }).filter(item => {
    if (isNavGroup(item)) {
      // Only show group if it has items
      return item.items.length > 0;
    }
    if (item.requiresOCR && !ocrEnabled) {
      return false;
    }
    return true;
  });

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
            {filteredNavigation.map((item) => {
              if (isNavGroup(item)) {
                // Render as dropdown group
                const isAnyChildActive = item.items.some(subItem => pathname === subItem.href);
                return (
                  <Disclosure key={item.name} defaultOpen={isAnyChildActive}>
                    {({ open }) => (
                      <>
                        <Disclosure.Button
                          className={`flex items-center justify-between w-full gap-3 px-3 py-2 rounded-lg transition-colors
                            ${
                              isAnyChildActive
                                ? 'bg-dark-bg text-white'
                                : 'text-gray-400 hover:bg-dark-bg hover:text-white'
                            }`}
                        >
                          <div className="flex items-center gap-3">
                            <item.icon className="w-5 h-5" />
                            {item.name}
                          </div>
                          <ChevronDownIcon 
                            className={`w-4 h-4 transition-transform ${open ? 'rotate-180' : ''}`}
                          />
                        </Disclosure.Button>
                        <Disclosure.Panel className="ml-6 mt-1 space-y-1">
                          {item.items.map((subItem) => {
                            const isActive = pathname === subItem.href;
                            return (
                              <Link
                                key={subItem.name}
                                href={subItem.href}
                                onClick={() => setIsMobileOpen(false)}
                                className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors
                                  ${
                                    isActive
                                      ? 'bg-primary-600 text-white'
                                      : 'text-gray-400 hover:bg-dark-bg hover:text-white'
                                  }`}
                              >
                                <subItem.icon className="w-4 h-4" />
                                {subItem.name}
                              </Link>
                            );
                          })}
                        </Disclosure.Panel>
                      </>
                    )}
                  </Disclosure>
                );
              } else {
                // Render as regular link
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
              }
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
