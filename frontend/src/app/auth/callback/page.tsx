'use client';

import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Cookies from 'js-cookie';
import { useAuth } from '@/contexts/AuthContext';

export default function AuthCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { refreshUser } = useAuth();

  useEffect(() => {
    const handleCallback = async () => {
      const access = searchParams.get('access');
      const refresh = searchParams.get('refresh');
      const error = searchParams.get('error');

      if (error) {
        router.push(`/login?error=${error}`);
        return;
      }

      if (access && refresh) {
        Cookies.set('access_token', access, { expires: 1 });
        Cookies.set('refresh_token', refresh, { expires: 7 });
        await refreshUser();
        router.push('/dashboard');
      } else {
        router.push('/login?error=auth_failed');
      }
    };

    handleCallback();
  }, [searchParams, router, refreshUser]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-dark-bg">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500 mx-auto mb-4"></div>
        <p className="text-gray-400">Completing authentication...</p>
      </div>
    </div>
  );
}
