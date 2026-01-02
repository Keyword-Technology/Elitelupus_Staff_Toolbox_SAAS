'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Cookies from 'js-cookie';
import { api } from '@/lib/api';

interface User {
  id: number;
  username: string;
  email: string | null;
  display_name: string;
  avatar_url: string | null;
  role: string;
  role_priority: number;
  role_color: string;
  steam_id: string | null;
  discord_id: string | null;
  timezone: string;
  use_24_hour_time: boolean;
  is_active_staff: boolean;
  setup_completed: boolean;
  setup_completed_at: string | null;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  isAuthenticated: boolean;
  hasMinRole: (rolePriority: number) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const refreshUser = useCallback(async () => {
    try {
      const token = Cookies.get('access_token');
      if (!token) {
        setUser(null);
        setLoading(false);
        return;
      }

      const response = await api.get('/auth/profile/');
      setUser(response.data);
    } catch (error: any) {
      // Only log errors that aren't network connection failures
      // (Network errors are expected when backend is starting up)
      if (error?.code !== 'ERR_NETWORK' || Cookies.get('access_token')) {
        console.error('Error refreshing user:', error);
      }
      setUser(null);
      Cookies.remove('access_token');
      Cookies.remove('refresh_token');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const login = async (username: string, password: string) => {
    const response = await api.post('/auth/token/', { username, password });
    const { access, refresh } = response.data;
    
    Cookies.set('access_token', access, { expires: 1 });
    Cookies.set('refresh_token', refresh, { expires: 7 });
    
    await refreshUser();
    
    // Check if setup is needed
    const userResponse = await api.get('/auth/profile/');
    if (!userResponse.data.setup_completed) {
      router.push('/setup');
    } else {
      router.push('/dashboard');
    }
  };

  const logout = () => {
    const refreshToken = Cookies.get('refresh_token');
    if (refreshToken) {
      api.post('/auth/logout/', { refresh: refreshToken }).catch(() => {});
    }
    
    Cookies.remove('access_token');
    Cookies.remove('refresh_token');
    setUser(null);
    router.push('/login');
  };

  const hasMinRole = (rolePriority: number) => {
    if (!user) return false;
    return user.role_priority <= rolePriority;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        logout,
        refreshUser,
        isAuthenticated: !!user,
        hasMinRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
