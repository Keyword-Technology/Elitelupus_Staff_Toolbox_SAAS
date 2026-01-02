'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { SetupWizard } from '@/components/auth/SetupWizard';

export default function SetupPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    // Redirect if not authenticated
    if (!loading && !user) {
      router.push('/login');
      return;
    }

    // Redirect to dashboard if setup already completed
    if (!loading && user?.setup_completed) {
      router.push('/dashboard');
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <div className="min-h-screen bg-dark-bg flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  if (!user || user.setup_completed) {
    return null;
  }

  return <SetupWizard />;
}
