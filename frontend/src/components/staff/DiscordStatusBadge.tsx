import React from 'react';

interface DiscordStatusBadgeProps {
  status?: 'online' | 'idle' | 'dnd' | 'offline' | null;
  customStatus?: string | null;
  activity?: string | null;
  showText?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const statusConfig = {
  online: {
    color: 'bg-green-500',
    text: 'Online',
    textColor: 'text-green-400',
  },
  idle: {
    color: 'bg-yellow-500',
    text: 'Idle',
    textColor: 'text-yellow-400',
  },
  dnd: {
    color: 'bg-red-500',
    text: 'Do Not Disturb',
    textColor: 'text-red-400',
  },
  offline: {
    color: 'bg-gray-600',
    text: 'Offline',
    textColor: 'text-gray-500',
  },
};

const sizeConfig = {
  sm: 'w-2 h-2',
  md: 'w-3 h-3',
  lg: 'w-4 h-4',
};

export default function DiscordStatusBadge({
  status,
  customStatus,
  activity,
  showText = true,
  size = 'md',
}: DiscordStatusBadgeProps) {
  const currentStatus = status || 'offline';
  const config = statusConfig[currentStatus];

  return (
    <div className="flex items-center gap-2">
      <div className="relative">
        <span
          className={`${sizeConfig[size]} rounded-full ${config.color} block`}
          title={config.text}
        />
      </div>
      {showText && (
        <div className="flex flex-col">
          <span className={`text-sm font-medium ${config.textColor}`}>
            {config.text}
          </span>
          {(customStatus || activity) && (
            <span className="text-xs text-gray-500 truncate max-w-xs">
              {customStatus || activity}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
