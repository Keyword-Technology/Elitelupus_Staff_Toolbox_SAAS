'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import toast from 'react-hot-toast';

const registerSchema = z
  .object({
    username: z.string().min(3, 'Username must be at least 3 characters'),
    email: z.string().email('Invalid email address'),
    password: z.string().min(8, 'Password must be at least 8 characters'),
    passwordConfirm: z.string(),
  })
  .refine((data) => data.password === data.passwordConfirm, {
    message: 'Passwords do not match',
    path: ['passwordConfirm'],
  });

type RegisterForm = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const { register: registerUser } = useAuth();
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (data: RegisterForm) => {
    setIsLoading(true);
    try {
      await registerUser(data.username, data.email, data.password, data.passwordConfirm);
      toast.success('Account created successfully!');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-dark-bg px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white">Create Account</h1>
          <p className="text-gray-400 mt-2">Join the Elitelupus Staff Toolbox</p>
        </div>

        <div className="bg-dark-card rounded-lg p-6 border border-dark-border">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Username
              </label>
              <input
                {...register('username')}
                type="text"
                className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg 
                         text-white placeholder-gray-500 focus:outline-none focus:ring-2 
                         focus:ring-primary-500 focus:border-transparent"
                placeholder="Choose a username"
              />
              {errors.username && (
                <p className="text-red-500 text-sm mt-1">{errors.username.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Email
              </label>
              <input
                {...register('email')}
                type="email"
                className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg 
                         text-white placeholder-gray-500 focus:outline-none focus:ring-2 
                         focus:ring-primary-500 focus:border-transparent"
                placeholder="Enter your email"
              />
              {errors.email && (
                <p className="text-red-500 text-sm mt-1">{errors.email.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Password
              </label>
              <input
                {...register('password')}
                type="password"
                className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg 
                         text-white placeholder-gray-500 focus:outline-none focus:ring-2 
                         focus:ring-primary-500 focus:border-transparent"
                placeholder="Create a password"
              />
              {errors.password && (
                <p className="text-red-500 text-sm mt-1">{errors.password.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Confirm Password
              </label>
              <input
                {...register('passwordConfirm')}
                type="password"
                className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg 
                         text-white placeholder-gray-500 focus:outline-none focus:ring-2 
                         focus:ring-primary-500 focus:border-transparent"
                placeholder="Confirm your password"
              />
              {errors.passwordConfirm && (
                <p className="text-red-500 text-sm mt-1">{errors.passwordConfirm.message}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2 px-4 bg-primary-600 hover:bg-primary-700 
                       text-white font-medium rounded-lg transition-colors
                       disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Creating account...' : 'Create Account'}
            </button>
          </form>

          <p className="text-center text-gray-400 text-sm mt-6">
            Already have an account?{' '}
            <Link href="/login" className="text-primary-500 hover:text-primary-400">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
