/**
 * Login Page for RevCopy Admin Panel
 * 
 * Provides secure authentication interface with:
 * - Form validation using react-hook-form and zod
 * - Error handling and user feedback
 * - Responsive design
 * - Security best practices
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Eye, EyeOff, Lock, Mail, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/context/AuthContext';
import type { LoginCredentials } from '@/lib/api';

/**
 * Login form validation schema
 */
const loginSchema = z.object({
  email: z
    .string()
    .min(1, 'Email is required')
    .email('Please enter a valid email address'),
  password: z
    .string()
    .min(1, 'Password is required')
    .min(8, 'Password must be at least 8 characters'),
});

type LoginFormData = z.infer<typeof loginSchema>;

/**
 * Login Page Component
 */
const Login: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated, isLoading } = useAuth();

  const [showPassword, setShowPassword] = useState(false);
  const [loginError, setLoginError] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  /**
   * React Hook Form setup with validation
   */
  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
    setFocus,
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    mode: 'onChange',
  });

  /**
   * Redirect authenticated users
   */
  useEffect(() => {
    if (isAuthenticated) {
      const from = (location.state as any)?.from?.pathname || '/';
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, location]);

  /**
   * Focus email field on component mount
   */
  useEffect(() => {
    setFocus('email');
  }, [setFocus]);

  /**
   * Handle form submission
   */
  const onSubmit = async (data: LoginFormData): Promise<void> => {
    try {
      setIsSubmitting(true);
      setLoginError('');

      const credentials: LoginCredentials = {
        email: data.email.trim().toLowerCase(),
        password: data.password,
      };

      const result = await login(credentials);

      if (!result.success) {
        setLoginError(result.message || 'Login failed. Please try again.');
      }
      // Success case is handled by the auth context and useEffect redirect
    } catch (error) {
      console.error('Login submission error:', error);
      setLoginError('An unexpected error occurred. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  /**
   * Toggle password visibility
   */
  const togglePasswordVisibility = (): void => {
    setShowPassword(!showPassword);
  };

  /**
   * Clear login error when user starts typing
   */
  const clearError = (): void => {
    if (loginError) {
      setLoginError('');
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-indigo-100">
            <Lock className="h-6 w-6 text-indigo-600" />
          </div>
          <h2 className="mt-6 text-3xl font-bold text-gray-900">
            RevCopy Admin
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Sign in to access the administration panel
          </p>
        </div>

        {/* Login Form */}
        <div className="bg-white py-8 px-6 shadow-lg rounded-xl border border-gray-200">
          <form className="space-y-6" onSubmit={handleSubmit(onSubmit)}>
            {/* Global Error Message */}
            {loginError && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start space-x-3">
                <AlertCircle className="h-5 w-5 text-red-400 mt-0.5 flex-shrink-0" />
                <div>
                  <h3 className="text-sm font-medium text-red-800">
                    Authentication Failed
                  </h3>
                  <p className="text-sm text-red-600 mt-1">{loginError}</p>
                </div>
              </div>
            )}

            {/* Email Field */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                Email Address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  {...register('email')}
                  type="email"
                  autoComplete="email"
                  className={`
                    block w-full pl-10 pr-3 py-3 border rounded-lg shadow-sm placeholder-gray-400 
                    focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent
                    ${errors.email ? 'border-red-300 bg-red-50' : 'border-gray-300'}
                  `}
                  placeholder="admin@revcopy.com"
                  onChange={clearError}
                />
              </div>
              {errors.email && (
                <p className="mt-2 text-sm text-red-600">{errors.email.message}</p>
              )}
            </div>

            {/* Password Field */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  {...register('password')}
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  className={`
                    block w-full pl-10 pr-10 py-3 border rounded-lg shadow-sm placeholder-gray-400 
                    focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent
                    ${errors.password ? 'border-red-300 bg-red-50' : 'border-gray-300'}
                  `}
                  placeholder="Enter your password"
                  onChange={clearError}
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  onClick={togglePasswordVisibility}
                >
                  {showPassword ? (
                    <EyeOff className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                  ) : (
                    <Eye className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                  )}
                </button>
              </div>
              {errors.password && (
                <p className="mt-2 text-sm text-red-600">{errors.password.message}</p>
              )}
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              disabled={!isValid || isSubmitting}
              className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 py-3 text-base font-medium"
            >
              {isSubmitting ? (
                <div className="flex items-center justify-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Signing in...</span>
                </div>
              ) : (
                'Sign In'
              )}
            </Button>
          </form>


        </div>

        {/* Footer */}
        <div className="text-center">
          <p className="text-xs text-gray-500">
            © 2024 RevCopy. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login; 