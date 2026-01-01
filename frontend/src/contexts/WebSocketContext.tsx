'use client';

import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react';
import { useAuth } from './AuthContext';
import Cookies from 'js-cookie';

// WebSocket connection configuration
const RECONNECT_INTERVAL = 3000; // 3 seconds
const MAX_RECONNECT_ATTEMPTS = 10;
const HEARTBEAT_INTERVAL = 30000; // 30 seconds

interface WebSocketContextType {
  counterSocket: WebSocket | null;
  serverSocket: WebSocket | null;
  staffSocket: WebSocket | null;
  isConnected: boolean;
  connectionStatus: 'connected' | 'connecting' | 'disconnected' | 'reconnecting';
  sendCounterUpdate: (type: string, action: string, value?: number) => void;
  onCounterUpdate: (callback: (data: CounterUpdate) => void) => () => void;
  onLeaderboardUpdate: (callback: (data: LeaderboardUpdate) => void) => () => void;
  onServerUpdate: (callback: (data: ServerUpdate) => void) => () => void;
  onStaffUpdate: (callback: (data: StaffUpdate) => void) => () => void;
  onStaffOnlineChange: (callback: (data: StaffOnlineChange) => void) => () => void;
  onStaffDiscordStatus: (callback: (data: StaffDiscordStatus) => void) => () => void;
  onRosterSync: (callback: (data: RosterSyncEvent) => void) => () => void;
  refreshStaffData: () => void;
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

interface ServerUpdate {
  type: string;
  data: any;
  server_id?: number;
  status?: any;
}

interface StaffUpdate {
  type: string;
  data: any;
}

interface StaffOnlineChange {
  type: string;
  staff_id: number;
  is_online: boolean;
  server_name?: string;
  server_id?: number;
}

interface StaffDiscordStatus {
  type: string;
  staff_id: number;
  discord_status: string;
  discord_custom_status?: string;
  discord_activity?: string;
}

interface RosterSyncEvent {
  type: string;
  records_updated: number;
  status: string;
}

// Reconnecting WebSocket wrapper
class ReconnectingWebSocket {
  private url: string;
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private shouldReconnect = true;
  
  public onopen: ((ev: Event) => void) | null = null;
  public onmessage: ((ev: MessageEvent) => void) | null = null;
  public onclose: ((ev: CloseEvent) => void) | null = null;
  public onerror: ((ev: Event) => void) | null = null;
  public onreconnecting: ((attempt: number) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    this.connect();
  }

  private connect() {
    if (!this.shouldReconnect) return;

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = (ev) => {
        console.log(`WebSocket connected: ${this.url.split('?')[0]}`);
        this.reconnectAttempts = 0;
        this.startHeartbeat();
        this.onopen?.(ev);
      };

      this.ws.onmessage = (ev) => {
        this.onmessage?.(ev);
      };

      this.ws.onclose = (ev) => {
        console.log(`WebSocket closed: ${this.url.split('?')[0]}`, ev.code, ev.reason);
        this.stopHeartbeat();
        this.onclose?.(ev);
        
        // Only reconnect on abnormal closure and if we should reconnect
        if (this.shouldReconnect && ev.code !== 1000 && ev.code !== 1001) {
          this.scheduleReconnect();
        }
      };

      this.ws.onerror = (ev) => {
        console.error(`WebSocket error: ${this.url.split('?')[0]}`, ev);
        this.onerror?.(ev);
      };
    } catch (error) {
      console.error('WebSocket connection error:', error);
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect() {
    if (!this.shouldReconnect) return;
    if (this.reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
      console.log('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = RECONNECT_INTERVAL * Math.min(this.reconnectAttempts, 5); // Exponential backoff with cap
    
    console.log(`Scheduling reconnect attempt ${this.reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS} in ${delay}ms`);
    this.onreconnecting?.(this.reconnectAttempts);
    
    this.reconnectTimeout = setTimeout(() => {
      console.log(`Attempting reconnection ${this.reconnectAttempts}...`);
      this.connect();
    }, delay);
  }

  private startHeartbeat() {
    this.stopHeartbeat();
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        try {
          this.ws.send(JSON.stringify({ action: 'ping' }));
        } catch {
          // Ignore ping errors
        }
      }
    }, HEARTBEAT_INTERVAL);
  }

  private stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  public send(data: string) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(data);
    }
  }

  public close() {
    this.shouldReconnect = false;
    this.stopHeartbeat();
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    if (this.ws) {
      this.ws.close(1000, 'Client closing');
      this.ws = null;
    }
  }

  public get readyState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED;
  }
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  const [counterSocket, setCounterSocket] = useState<WebSocket | null>(null);
  const [serverSocket, setServerSocket] = useState<WebSocket | null>(null);
  const [staffSocket, setStaffSocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'connecting' | 'disconnected' | 'reconnecting'>('disconnected');
  
  // Use refs for callbacks to prevent unnecessary re-renders
  const counterCallbacksRef = useRef<((data: CounterUpdate) => void)[]>([]);
  const leaderboardCallbacksRef = useRef<((data: LeaderboardUpdate) => void)[]>([]);
  const serverCallbacksRef = useRef<((data: ServerUpdate) => void)[]>([]);
  const staffCallbacksRef = useRef<((data: StaffUpdate) => void)[]>([]);
  const staffOnlineCallbacksRef = useRef<((data: StaffOnlineChange) => void)[]>([]);
  const staffDiscordCallbacksRef = useRef<((data: StaffDiscordStatus) => void)[]>([]);
  const rosterSyncCallbacksRef = useRef<((data: RosterSyncEvent) => void)[]>([]);

  // Keep track of reconnecting websockets
  const socketsRef = useRef<{
    counter: ReconnectingWebSocket | null;
    server: ReconnectingWebSocket | null;
    staff: ReconnectingWebSocket | null;
  }>({ counter: null, server: null, staff: null });

  useEffect(() => {
    if (!isAuthenticated) {
      // Close all sockets
      socketsRef.current.counter?.close();
      socketsRef.current.server?.close();
      socketsRef.current.staff?.close();
      socketsRef.current = { counter: null, server: null, staff: null };
      setCounterSocket(null);
      setServerSocket(null);
      setStaffSocket(null);
      setIsConnected(false);
      setConnectionStatus('disconnected');
      return;
    }

    const token = Cookies.get('access_token');
    if (!token) return;

    setConnectionStatus('connecting');

    // Determine WebSocket URL based on environment or current location
    let wsBaseUrl = process.env.NEXT_PUBLIC_WS_URL;
    
    if (wsBaseUrl) {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      wsBaseUrl = wsBaseUrl.replace(/^(ws|wss):/, protocol);
    } else {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      wsBaseUrl = `${protocol}//${host}`;
    }

    // Track connection state
    let connectedCount = 0;
    const updateConnectionState = () => {
      const allConnected = connectedCount >= 3;
      setIsConnected(allConnected);
      setConnectionStatus(allConnected ? 'connected' : 'connecting');
    };

    // Counter WebSocket
    const counterWs = new ReconnectingWebSocket(`${wsBaseUrl}/ws/counters/?token=${token}`);
    counterWs.onopen = () => {
      connectedCount++;
      updateConnectionState();
    };
    counterWs.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'counter_update') {
          counterCallbacksRef.current.forEach((cb) => cb(data));
        } else if (data.type === 'leaderboard_update') {
          leaderboardCallbacksRef.current.forEach((cb) => cb(data));
        }
      } catch (e) {
        console.error('Error parsing counter message:', e);
      }
    };
    counterWs.onclose = () => {
      connectedCount = Math.max(0, connectedCount - 1);
      updateConnectionState();
    };
    counterWs.onreconnecting = () => {
      setConnectionStatus('reconnecting');
    };
    socketsRef.current.counter = counterWs;
    setCounterSocket(counterWs as unknown as WebSocket);

    // Server WebSocket
    const serverWs = new ReconnectingWebSocket(`${wsBaseUrl}/ws/servers/?token=${token}`);
    serverWs.onopen = () => {
      connectedCount++;
      updateConnectionState();
    };
    serverWs.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        serverCallbacksRef.current.forEach((cb) => cb(data));
      } catch (e) {
        console.error('Error parsing server message:', e);
      }
    };
    serverWs.onclose = () => {
      connectedCount = Math.max(0, connectedCount - 1);
      updateConnectionState();
    };
    serverWs.onreconnecting = () => {
      setConnectionStatus('reconnecting');
    };
    socketsRef.current.server = serverWs;
    setServerSocket(serverWs as unknown as WebSocket);

    // Staff WebSocket
    const staffWs = new ReconnectingWebSocket(`${wsBaseUrl}/ws/staff/?token=${token}`);
    staffWs.onopen = () => {
      connectedCount++;
      updateConnectionState();
    };
    staffWs.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        switch (data.type) {
          case 'initial_data':
          case 'staff_update':
            staffCallbacksRef.current.forEach((cb) => cb(data));
            break;
          case 'staff_online_change':
            staffOnlineCallbacksRef.current.forEach((cb) => cb(data));
            break;
          case 'staff_discord_status':
            staffDiscordCallbacksRef.current.forEach((cb) => cb(data));
            break;
          case 'staff_roster_sync':
            rosterSyncCallbacksRef.current.forEach((cb) => cb(data));
            break;
        }
      } catch (e) {
        console.error('Error parsing staff message:', e);
      }
    };
    staffWs.onclose = () => {
      connectedCount = Math.max(0, connectedCount - 1);
      updateConnectionState();
    };
    staffWs.onreconnecting = () => {
      setConnectionStatus('reconnecting');
    };
    socketsRef.current.staff = staffWs;
    setStaffSocket(staffWs as unknown as WebSocket);

    return () => {
      socketsRef.current.counter?.close();
      socketsRef.current.server?.close();
      socketsRef.current.staff?.close();
      socketsRef.current = { counter: null, server: null, staff: null };
    };
  }, [isAuthenticated]);

  const sendCounterUpdate = useCallback(
    (type: string, action: string, value: number = 1) => {
      socketsRef.current.counter?.send(
        JSON.stringify({
          action: 'update',
          counter_type: type,
          update_action: action,
          value,
        })
      );
    },
    []
  );

  const refreshStaffData = useCallback(() => {
    socketsRef.current.staff?.send(
      JSON.stringify({ action: 'refresh' })
    );
  }, []);

  // Callback registration functions
  const onCounterUpdate = useCallback((callback: (data: CounterUpdate) => void) => {
    counterCallbacksRef.current.push(callback);
    return () => {
      counterCallbacksRef.current = counterCallbacksRef.current.filter((cb) => cb !== callback);
    };
  }, []);

  const onLeaderboardUpdate = useCallback((callback: (data: LeaderboardUpdate) => void) => {
    leaderboardCallbacksRef.current.push(callback);
    return () => {
      leaderboardCallbacksRef.current = leaderboardCallbacksRef.current.filter((cb) => cb !== callback);
    };
  }, []);

  const onServerUpdate = useCallback((callback: (data: ServerUpdate) => void) => {
    serverCallbacksRef.current.push(callback);
    return () => {
      serverCallbacksRef.current = serverCallbacksRef.current.filter((cb) => cb !== callback);
    };
  }, []);

  const onStaffUpdate = useCallback((callback: (data: StaffUpdate) => void) => {
    staffCallbacksRef.current.push(callback);
    return () => {
      staffCallbacksRef.current = staffCallbacksRef.current.filter((cb) => cb !== callback);
    };
  }, []);

  const onStaffOnlineChange = useCallback((callback: (data: StaffOnlineChange) => void) => {
    staffOnlineCallbacksRef.current.push(callback);
    return () => {
      staffOnlineCallbacksRef.current = staffOnlineCallbacksRef.current.filter((cb) => cb !== callback);
    };
  }, []);

  const onStaffDiscordStatus = useCallback((callback: (data: StaffDiscordStatus) => void) => {
    staffDiscordCallbacksRef.current.push(callback);
    return () => {
      staffDiscordCallbacksRef.current = staffDiscordCallbacksRef.current.filter((cb) => cb !== callback);
    };
  }, []);

  const onRosterSync = useCallback((callback: (data: RosterSyncEvent) => void) => {
    rosterSyncCallbacksRef.current.push(callback);
    return () => {
      rosterSyncCallbacksRef.current = rosterSyncCallbacksRef.current.filter((cb) => cb !== callback);
    };
  }, []);

  return (
    <WebSocketContext.Provider
      value={{
        counterSocket,
        serverSocket,
        staffSocket,
        isConnected,
        connectionStatus,
        sendCounterUpdate,
        onCounterUpdate,
        onLeaderboardUpdate,
        onServerUpdate,
        onStaffUpdate,
        onStaffOnlineChange,
        onStaffDiscordStatus,
        onRosterSync,
        refreshStaffData,
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
