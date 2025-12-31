'use client';

import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react';
import { useAuth } from './AuthContext';
import Cookies from 'js-cookie';

interface WebSocketContextType {
  counterSocket: WebSocket | null;
  serverSocket: WebSocket | null;
  isConnected: boolean;
  sendCounterUpdate: (type: string, action: string, value?: number) => void;
  onCounterUpdate: (callback: (data: CounterUpdate) => void) => void;
  onLeaderboardUpdate: (callback: (data: LeaderboardUpdate) => void) => void;
  onServerUpdate: (callback: (data: any) => void) => void;
}

interface CounterUpdate {
  type: string;
  counter_type: string;
  count: number;
  user_id: number;
  username: string;
}

interface LeaderboardUpdate {
  type: string;
  user_id: number;
  username: string;
  display_name: string;
  counter_type: string;
  count: number;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  const [counterSocket, setCounterSocket] = useState<WebSocket | null>(null);
  const [serverSocket, setServerSocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  
  const counterCallbacksRef = useRef<((data: CounterUpdate) => void)[]>([]);
  const leaderboardCallbacksRef = useRef<((data: LeaderboardUpdate) => void)[]>([]);
  const serverCallbacksRef = useRef<((data: any) => void)[]>([]);

  useEffect(() => {
    if (!isAuthenticated) {
      counterSocket?.close();
      serverSocket?.close();
      setCounterSocket(null);
      setServerSocket(null);
      setIsConnected(false);
      return;
    }

    const token = Cookies.get('access_token');
    if (!token) return;

    // Determine WebSocket URL based on environment or current location
    let wsBaseUrl = process.env.NEXT_PUBLIC_WS_URL;
    
    if (!wsBaseUrl) {
      // Auto-detect based on current page protocol and host
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host; // includes port
      wsBaseUrl = `${protocol}//${host}`;
    }

    // Counter WebSocket
    const counterWs = new WebSocket(`${wsBaseUrl}/ws/counters/?token=${token}`);
    
    counterWs.onopen = () => {
      console.log('Counter WebSocket connected');
      setIsConnected(true);
    };
    
    counterWs.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'counter_update') {
        counterCallbacksRef.current.forEach((cb) => cb(data));
      } else if (data.type === 'leaderboard_update') {
        leaderboardCallbacksRef.current.forEach((cb) => cb(data));
      }
    };
    
    counterWs.onclose = () => {
      console.log('Counter WebSocket disconnected');
      setIsConnected(false);
    };
    
    setCounterSocket(counterWs);

    // Server WebSocket
    const serverWs = new WebSocket(`${wsBaseUrl}/ws/servers/?token=${token}`);
    
    serverWs.onmessage = (event) => {
      const data = JSON.parse(event.data);
      serverCallbacksRef.current.forEach((cb) => cb(data));
    };
    
    setServerSocket(serverWs);

    return () => {
      counterWs.close();
      serverWs.close();
    };
  }, [isAuthenticated]);

  const sendCounterUpdate = useCallback(
    (type: string, action: string, value: number = 1) => {
      if (counterSocket?.readyState === WebSocket.OPEN) {
        counterSocket.send(
          JSON.stringify({
            action: 'update',
            counter_type: type,
            update_action: action,
            value,
          })
        );
      }
    },
    [counterSocket]
  );

  const onCounterUpdate = useCallback((callback: (data: CounterUpdate) => void) => {
    counterCallbacksRef.current.push(callback);
    return () => {
      counterCallbacksRef.current = counterCallbacksRef.current.filter(
        (cb) => cb !== callback
      );
    };
  }, []);

  const onLeaderboardUpdate = useCallback((callback: (data: LeaderboardUpdate) => void) => {
    leaderboardCallbacksRef.current.push(callback);
    return () => {
      leaderboardCallbacksRef.current = leaderboardCallbacksRef.current.filter(
        (cb) => cb !== callback
      );
    };
  }, []);

  const onServerUpdate = useCallback((callback: (data: any) => void) => {
    serverCallbacksRef.current.push(callback);
    return () => {
      serverCallbacksRef.current = serverCallbacksRef.current.filter(
        (cb) => cb !== callback
      );
    };
  }, []);

  return (
    <WebSocketContext.Provider
      value={{
        counterSocket,
        serverSocket,
        isConnected,
        sendCounterUpdate,
        onCounterUpdate,
        onLeaderboardUpdate,
        onServerUpdate,
      }}
    >
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocket() {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
}
