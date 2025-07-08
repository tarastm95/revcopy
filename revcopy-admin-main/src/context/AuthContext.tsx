/**
 * Authentication Context for RevCopy Admin Panel
 * 
 * Provides authentication state management throughout the application including:
 * - User authentication status
 * - Login/logout functionality  
 * - Automatic token refresh
 * - Protected route handling
 */

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { apiClient, TokenManager, AuthResponse, LoginCredentials } from '../lib/api';

interface User {
  id: number;
  email: string;
  username: string;
  role: string;
  is_verified: boolean;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<{ success: boolean; message?: string }>;
  logout: () => Promise<void>;
  refreshAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

/**
 * Authentication Provider Component
 * 
 * Wraps the application to provide authentication state and methods
 */
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  /**
   * Initialize authentication state on component mount
   */
  useEffect(() => {
    initializeAuth();
  }, []);

  /**
   * Initialize authentication by checking stored tokens
   */
  const initializeAuth = async (): Promise<void> => {
    try {
      if (TokenManager.isAuthenticated()) {
        // Validate token by fetching user profile
        await refreshAuth();
      } else {
        setIsAuthenticated(false);
        setUser(null);
      }
    } catch (error) {
      console.error('Auth initialization failed:', error);
      handleAuthError();
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handle authentication errors by clearing state and tokens
   */
  const handleAuthError = (): void => {
    setIsAuthenticated(false);
    setUser(null);
    TokenManager.clearTokens();
  };

  /**
   * Login user with email and password
   */
  const login = async (credentials: LoginCredentials): Promise<{ success: boolean; message?: string }> => {
    try {
      setIsLoading(true);
      
      const response = await apiClient.login(credentials);
      
      if (response.success && response.data) {
        const authData = response.data as AuthResponse;
        
        // Store tokens
        TokenManager.setTokens(authData);
        
        // Fetch user profile with the new token
        try {
          const profileResponse = await apiClient.getUserProfile();
          if (profileResponse.success && profileResponse.data) {
            setUser(profileResponse.data);
            setIsAuthenticated(true);
            return { success: true };
          } else {
            // If profile fetch fails, clear tokens and return error
            TokenManager.clearTokens();
            return { 
              success: false, 
              message: 'Failed to fetch user profile after login.' 
            };
          }
        } catch (profileError) {
          console.error('Profile fetch error:', profileError);
          TokenManager.clearTokens();
          return { 
            success: false, 
            message: 'Failed to fetch user profile after login.' 
          };
        }
      } else {
        return { 
          success: false, 
          message: response.message || 'Login failed. Please check your credentials.' 
        };
      }
    } catch (error) {
      console.error('Login error:', error);
      return { 
        success: false, 
        message: error instanceof Error ? error.message : 'An unexpected error occurred during login.' 
      };
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Logout user and clear authentication state
   */
  const logout = async (): Promise<void> => {
    try {
      setIsLoading(true);
      
      // Call backend logout endpoint
      await apiClient.logout();
      
      // Clear local state
      handleAuthError();
    } catch (error) {
      console.error('Logout error:', error);
      // Clear local state even if backend call fails
      handleAuthError();
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Refresh authentication by validating current token
   */
  const refreshAuth = async (): Promise<void> => {
    try {
      if (TokenManager.isAuthenticated()) {
        // Validate token by fetching user profile from backend
        const response = await apiClient.getUserProfile();
        
        if (response.success && response.data) {
          setUser(response.data);
          setIsAuthenticated(true);
        } else {
          // Token is invalid or user not found
          handleAuthError();
        }
      } else {
        handleAuthError();
      }
    } catch (error) {
      console.error('Auth refresh failed:', error);
      handleAuthError();
    }
  };

  /**
   * Context value provided to consuming components
   */
  const contextValue: AuthContextType = {
    user,
    isAuthenticated,
    isLoading,
    login,
    logout,
    refreshAuth,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

/**
 * Custom hook to use authentication context
 * 
 * @throws Error if used outside of AuthProvider
 */
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  
  return context;
};

/**
 * Higher-order component for protecting routes that require authentication
 */
export interface ProtectedRouteProps {
  children: ReactNode;
  fallback?: ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  fallback = <div>Redirecting to login...</div> 
}) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}; 