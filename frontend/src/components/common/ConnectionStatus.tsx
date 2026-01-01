'use client';

import { useWebSocket } from '@/contexts/WebSocketContext';
import { WifiIcon, ArrowPathIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

interface ConnectionStatusProps {
  showLabel?: boolean;
  className?: string;
}

export function ConnectionStatus({ showLabel = true, className = '' }: ConnectionStatusProps) {
  const { connectionStatus } = useWebSocket();

  const statusConfig = {
    connected: {
      icon: WifiIcon,
      color: 'text-green-400',
      bgColor: 'bg-green-400/20',
      label: 'Live',
      dotColor: 'bg-green-400',
      animate: false,
    },
    connecting: {
      icon: ArrowPathIcon,
      color: 'text-blue-400',
      bgColor: 'bg-blue-400/20',
      label: 'Connecting...',
      dotColor: 'bg-blue-400',
      animate: true,
    },
    reconnecting: {
      icon: ArrowPathIcon,
      color: 'text-yellow-400',
      bgColor: 'bg-yellow-400/20',
      label: 'Reconnecting...',
      dotColor: 'bg-yellow-400',
      animate: true,
    },
    disconnected: {
      icon: ExclamationTriangleIcon,
      color: 'text-red-400',
      bgColor: 'bg-red-400/20',
      label: 'Offline',
      dotColor: 'bg-red-400',
      animate: false,
    },
  };

  const config = statusConfig[connectionStatus];
  const Icon = config.icon;

  return (
    <div className={`flex items-center gap-1.5 px-2 py-1 rounded-lg ${config.bgColor} ${className}`}>
      <span className={`w-2 h-2 rounded-full ${config.dotColor} ${config.animate ? 'animate-pulse' : ''}`} />
      {showLabel && (
        <span className={`text-xs font-medium ${config.color}`}>
          {config.label}
        </span>
      )}
    </div>
  );
}

export default ConnectionStatus;
