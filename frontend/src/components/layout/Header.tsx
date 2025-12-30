'use client';

import { useAuth } from '@/contexts/AuthContext';
import { useWebSocket } from '@/contexts/WebSocketContext';
import { BellIcon } from '@heroicons/react/24/outline';

export function Header() {
  const { user } = useAuth();
  const { isConnected } = useWebSocket();

  return (
    <header className="bg-dark-card border-b border-dark-border px-4 md:px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4 md:ml-0 ml-12">
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
        </div>

        <div className="flex items-center gap-4">
          {/* Notifications */}
          <button className="p-2 text-gray-400 hover:text-white transition-colors">
            <BellIcon className="w-6 h-6" />
          </button>

          {/* User Info */}
          <div className="flex items-center gap-3">
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
                className="w-10 h-10 rounded-full"
              />
            ) : (
              <div className="w-10 h-10 rounded-full bg-primary-600 flex items-center justify-center">
                <span className="text-white font-medium">
                  {(user?.display_name || user?.username || '?')[0].toUpperCase()}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
