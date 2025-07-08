/**
 * Amazon Settings Component for RevCopy Admin Panel
 * 
 * Provides comprehensive Amazon integration management with:
 * - Real-time data from backend API
 * - Amazon account management with security
 * - Proxy server configuration and monitoring
 * - Connection testing and validation
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Edit, Trash2, Eye, EyeOff, Globe, Loader2, AlertCircle, RefreshCw, Shield } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { apiClient } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

interface AmazonAccount {
  id: number;
  username: string;
  password_masked: string;
  status: string;
  last_used_at: string | null;
  avatar_url?: string;
  created_at: string;
}

interface ProxyServer {
  id: number;
  name: string;
  address: string;
  status: string;
  location: string;
  last_used_at: string | null;
  created_at: string;
}

interface NewAccountData {
  username: string;
  password: string;
  avatar_url?: string;
}

interface NewProxyData {
  name: string;
  address: string;
  location: string;
}

/**
 * Main Amazon Settings Component
 */
const AmazonSettings: React.FC = () => {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  
  const [showAccountForm, setShowAccountForm] = useState(false);
  const [showProxyForm, setShowProxyForm] = useState(false);
  const [showPasswords, setShowPasswords] = useState<Record<number, boolean>>({});
  const [newAccount, setNewAccount] = useState<NewAccountData>({ 
    username: '', 
    password: '', 
    avatar_url: '' 
  });
  const [newProxy, setNewProxy] = useState<NewProxyData>({ 
    name: '', 
    address: '', 
    location: '' 
  });

  /**
   * Fetch Amazon accounts from backend
   */
  const {
    data: accounts = [],
    isLoading: isLoadingAccounts,
    error: accountsError,
    refetch: refetchAccounts,
  } = useQuery({
    queryKey: ['amazon-accounts'],
    queryFn: async () => {
      const response = await apiClient.getAmazonAccounts();
      if (!response.success) {
        throw new Error(response.message || 'Failed to fetch Amazon accounts');
      }
      return response.data || [];
    },
    retry: 3,
    refetchInterval: 60000,
  });

  /**
   * Fetch proxy servers from backend
   */
  const {
    data: proxies = [],
    isLoading: isLoadingProxies,
    error: proxiesError,
    refetch: refetchProxies,
  } = useQuery({
    queryKey: ['proxy-servers'],
    queryFn: async () => {
      const response = await apiClient.getProxyServers();
      if (!response.success) {
        throw new Error(response.message || 'Failed to fetch proxy servers');
      }
      return response.data || [];
    },
    retry: 3,
    refetchInterval: 60000,
  });

  /**
   * Create Amazon account mutation
   */
  const createAccountMutation = useMutation({
    mutationFn: async (accountData: NewAccountData) => {
      const response = await apiClient.createAmazonAccount(accountData);
      if (!response.success) {
        throw new Error(response.message || 'Failed to create Amazon account');
      }
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['amazon-accounts'] });
      setNewAccount({ username: '', password: '', avatar_url: '' });
      setShowAccountForm(false);
      toast({
        title: 'Success',
        description: 'Amazon account created successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message,
        variant: 'destructive',
      });
    },
  });

  /**
   * Create proxy server mutation
   */
  const createProxyMutation = useMutation({
    mutationFn: async (proxyData: NewProxyData) => {
      const response = await apiClient.createProxyServer(proxyData);
      if (!response.success) {
        throw new Error(response.message || 'Failed to create proxy server');
      }
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proxy-servers'] });
      setNewProxy({ name: '', address: '', location: '' });
      setShowProxyForm(false);
      toast({
        title: 'Success',
        description: 'Proxy server created successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message,
        variant: 'destructive',
      });
    },
  });

  /**
   * Delete account mutation
   */
  const deleteAccountMutation = useMutation({
    mutationFn: async (accountId: number) => {
      const response = await apiClient.deleteAmazonAccount(accountId);
      if (!response.success) {
        throw new Error(response.message || 'Failed to delete Amazon account');
      }
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['amazon-accounts'] });
      toast({
        title: 'Success',
        description: 'Amazon account deleted successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message,
        variant: 'destructive',
      });
    },
  });

  /**
   * Delete proxy mutation
   */
  const deleteProxyMutation = useMutation({
    mutationFn: async (proxyId: number) => {
      const response = await apiClient.deleteProxyServer(proxyId);
      if (!response.success) {
        throw new Error(response.message || 'Failed to delete proxy server');
      }
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proxy-servers'] });
      toast({
        title: 'Success',
        description: 'Proxy server deleted successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message,
        variant: 'destructive',
      });
    },
  });

  /**
   * Handle form submissions
   */
  const handleAddAccount = (): void => {
    if (!newAccount.username || !newAccount.password) {
      toast({
        title: 'Validation Error',
        description: 'Please fill in username and password',
        variant: 'destructive',
      });
      return;
    }
    createAccountMutation.mutate(newAccount);
  };

  const handleAddProxy = (): void => {
    if (!newProxy.name || !newProxy.address || !newProxy.location) {
      toast({
        title: 'Validation Error',
        description: 'Please fill in all proxy server fields',
        variant: 'destructive',
      });
      return;
    }
    createProxyMutation.mutate(newProxy);
  };

  /**
   * Handle deletions
   */
  const handleDeleteAccount = (accountId: number): void => {
    if (window.confirm('Are you sure you want to delete this Amazon account? This action cannot be undone.')) {
      deleteAccountMutation.mutate(accountId);
    }
  };

  const handleDeleteProxy = (proxyId: number): void => {
    if (window.confirm('Are you sure you want to delete this proxy server? This action cannot be undone.')) {
      deleteProxyMutation.mutate(proxyId);
    }
  };

  /**
   * Toggle password visibility
   */
  const togglePasswordVisibility = (accountId: number): void => {
    setShowPasswords(prev => ({
      ...prev,
      [accountId]: !prev[accountId]
    }));
  };

  /**
   * Handle refresh
   */
  const handleRefresh = (): void => {
    refetchAccounts();
    refetchProxies();
  };

  /**
   * Format last used time
   */
  const formatLastUsed = (lastUsed: string | null): string => {
    if (!lastUsed) return 'Never';
    
    const date = new Date(lastUsed);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffHours < 1) return 'Just now';
    if (diffHours < 24) return `${diffHours} hours ago`;
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  };

  /**
   * Get status styling
   */
  const getStatusColor = (status: string): string => {
    switch (status.toLowerCase()) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'inactive':
        return 'bg-red-100 text-red-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  /**
   * Render error state
   */
  if (accountsError || proxiesError) {
    return (
      <div className="p-8">
        <div className="text-center">
          <AlertCircle className="mx-auto h-12 w-12 text-red-500" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">Error loading Amazon settings</h3>
          <p className="mt-1 text-sm text-gray-500">
            {(accountsError || proxiesError) instanceof Error 
              ? (accountsError || proxiesError)?.message 
              : 'An unknown error occurred'
            }
          </p>
          <div className="mt-6">
            <Button onClick={handleRefresh}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Try Again
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Amazon Integration Settings</h1>
          <p className="text-gray-600 mt-2">Manage Amazon accounts and proxy configurations for data crawling</p>
        </div>
        <Button
          onClick={handleRefresh}
          variant="outline"
          disabled={isLoadingAccounts || isLoadingProxies}
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${(isLoadingAccounts || isLoadingProxies) ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Amazon Accounts Section */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Amazon Accounts</h2>
            <p className="text-gray-600 mt-1">Manage Amazon accounts for data scraping</p>
          </div>
          <Button 
            onClick={() => setShowAccountForm(true)}
            className="bg-indigo-600 hover:bg-indigo-700"
            disabled={showAccountForm}
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Account
          </Button>
        </div>

        {/* Add Account Form */}
        {showAccountForm && (
          <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Add New Amazon Account</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Username *</label>
                <input
                  type="text"
                  value={newAccount.username}
                  onChange={(e) => setNewAccount({ ...newAccount, username: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  placeholder="Enter Amazon username..."
                  disabled={createAccountMutation.isPending}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Password *</label>
                <input
                  type="password"
                  value={newAccount.password}
                  onChange={(e) => setNewAccount({ ...newAccount, password: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  placeholder="Enter secure password..."
                  disabled={createAccountMutation.isPending}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Avatar URL (Optional)</label>
                <input
                  type="url"
                  value={newAccount.avatar_url}
                  onChange={(e) => setNewAccount({ ...newAccount, avatar_url: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  placeholder="https://example.com/avatar.jpg"
                  disabled={createAccountMutation.isPending}
                />
              </div>
            </div>
            <div className="flex space-x-3">
              <Button 
                onClick={handleAddAccount} 
                className="bg-green-600 hover:bg-green-700"
                disabled={createAccountMutation.isPending}
              >
                {createAccountMutation.isPending ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Plus className="w-4 h-4 mr-2" />
                )}
                {createAccountMutation.isPending ? 'Adding...' : 'Add Account'}
              </Button>
              <Button 
                onClick={() => setShowAccountForm(false)} 
                variant="outline"
                disabled={createAccountMutation.isPending}
              >
                Cancel
              </Button>
            </div>
          </div>
        )}

        {/* Accounts Table */}
        {isLoadingAccounts ? (
          <div className="bg-white rounded-xl border border-gray-200 p-8">
            <div className="text-center">
              <Loader2 className="mx-auto h-8 w-8 animate-spin text-indigo-600" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">Loading accounts...</h3>
            </div>
          </div>
        ) : accounts.length === 0 ? (
          <div className="bg-white rounded-xl border border-gray-200 p-8">
            <div className="text-center">
              <Shield className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No Amazon accounts</h3>
              <p className="mt-1 text-sm text-gray-500">Add your first Amazon account to get started.</p>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="text-left py-4 px-6 text-sm font-semibold text-gray-900">Account</th>
                    <th className="text-left py-4 px-6 text-sm font-semibold text-gray-900">Password</th>
                    <th className="text-left py-4 px-6 text-sm font-semibold text-gray-900">Status</th>
                    <th className="text-left py-4 px-6 text-sm font-semibold text-gray-900">Last Used</th>
                    <th className="text-left py-4 px-6 text-sm font-semibold text-gray-900">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {accounts.map((account: AmazonAccount) => (
                    <tr key={account.id} className="hover:bg-gray-50">
                      <td className="py-4 px-6">
                        <div className="flex items-center">
                          <div className="w-10 h-10 bg-orange-100 rounded-full flex items-center justify-center">
                            <Shield className="w-5 h-5 text-orange-600" />
                          </div>
                          <div className="ml-3">
                            <p className="text-sm font-medium text-gray-900">{account.username}</p>
                            <p className="text-sm text-gray-500">Amazon Account</p>
                          </div>
                        </div>
                      </td>
                      <td className="py-4 px-6">
                        <div className="flex items-center">
                          <span className="text-sm text-gray-600 mr-2">
                            {showPasswords[account.id] ? account.password_masked : '••••••••'}
                          </span>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => togglePasswordVisibility(account.id)}
                          >
                            {showPasswords[account.id] ? (
                              <EyeOff className="w-4 h-4" />
                            ) : (
                              <Eye className="w-4 h-4" />
                            )}
                          </Button>
                        </div>
                      </td>
                      <td className="py-4 px-6">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(account.status)}`}>
                          {account.status.toUpperCase()}
                        </span>
                      </td>
                      <td className="py-4 px-6 text-sm text-gray-600">
                        {formatLastUsed(account.last_used_at)}
                      </td>
                      <td className="py-4 px-6">
                        <div className="flex space-x-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {/* TODO: Implement edit functionality */}}
                          >
                            <Edit className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDeleteAccount(account.id)}
                            disabled={deleteAccountMutation.isPending}
                            className="text-red-600 hover:text-red-700"
                          >
                            {deleteAccountMutation.isPending ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                              <Trash2 className="w-4 h-4" />
                            )}
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Proxy Servers Section */}
      <div>
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Proxy Servers</h2>
            <p className="text-gray-600 mt-1">Configure proxy servers for secure data access</p>
          </div>
          <Button 
            onClick={() => setShowProxyForm(true)}
            className="bg-purple-600 hover:bg-purple-700"
            disabled={showProxyForm}
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Proxy
          </Button>
        </div>

        {/* Add Proxy Form */}
        {showProxyForm && (
          <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Add New Proxy Server</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Proxy Name *</label>
                <input
                  type="text"
                  value={newProxy.name}
                  onChange={(e) => setNewProxy({ ...newProxy, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="Enter proxy name..."
                  disabled={createProxyMutation.isPending}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Location *</label>
                <input
                  type="text"
                  value={newProxy.location}
                  onChange={(e) => setNewProxy({ ...newProxy, location: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="US East, EU West, etc."
                  disabled={createProxyMutation.isPending}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Proxy Address *</label>
                <input
                  type="text"
                  value={newProxy.address}
                  onChange={(e) => setNewProxy({ ...newProxy, address: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="anvitop:C29UaLSZPx@74.124.222.120:50100"
                  disabled={createProxyMutation.isPending}
                />
              </div>
            </div>
            <div className="flex space-x-3">
              <Button 
                onClick={handleAddProxy} 
                className="bg-green-600 hover:bg-green-700"
                disabled={createProxyMutation.isPending}
              >
                {createProxyMutation.isPending ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Plus className="w-4 h-4 mr-2" />
                )}
                {createProxyMutation.isPending ? 'Adding...' : 'Add Proxy'}
              </Button>
              <Button 
                onClick={() => setShowProxyForm(false)} 
                variant="outline"
                disabled={createProxyMutation.isPending}
              >
                Cancel
              </Button>
            </div>
          </div>
        )}

        {/* Proxies Table */}
        {isLoadingProxies ? (
          <div className="bg-white rounded-xl border border-gray-200 p-8">
            <div className="text-center">
              <Loader2 className="mx-auto h-8 w-8 animate-spin text-purple-600" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">Loading proxies...</h3>
            </div>
          </div>
        ) : proxies.length === 0 ? (
          <div className="bg-white rounded-xl border border-gray-200 p-8">
            <div className="text-center">
              <Globe className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No proxy servers</h3>
              <p className="mt-1 text-sm text-gray-500">Add your first proxy server to get started.</p>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="text-left py-4 px-6 text-sm font-semibold text-gray-900">Proxy Server</th>
                    <th className="text-left py-4 px-6 text-sm font-semibold text-gray-900">Address</th>
                    <th className="text-left py-4 px-6 text-sm font-semibold text-gray-900">Location</th>
                    <th className="text-left py-4 px-6 text-sm font-semibold text-gray-900">Status</th>
                    <th className="text-left py-4 px-6 text-sm font-semibold text-gray-900">Last Used</th>
                    <th className="text-left py-4 px-6 text-sm font-semibold text-gray-900">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {proxies.map((proxy: ProxyServer) => (
                    <tr key={proxy.id} className="hover:bg-gray-50">
                      <td className="py-4 px-6">
                        <div className="flex items-center">
                          <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center">
                            <Globe className="w-5 h-5 text-purple-600" />
                          </div>
                          <div className="ml-3">
                            <p className="text-sm font-medium text-gray-900">{proxy.name}</p>
                            <p className="text-sm text-gray-500">Proxy Server</p>
                          </div>
                        </div>
                      </td>
                      <td className="py-4 px-6">
                        <code className="text-sm font-mono text-gray-600 bg-gray-50 px-2 py-1 rounded">
                          {proxy.address}
                        </code>
                      </td>
                      <td className="py-4 px-6 text-sm text-gray-600">
                        {proxy.location}
                      </td>
                      <td className="py-4 px-6">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(proxy.status)}`}>
                          {proxy.status.toUpperCase()}
                        </span>
                      </td>
                      <td className="py-4 px-6 text-sm text-gray-600">
                        {formatLastUsed(proxy.last_used_at)}
                      </td>
                      <td className="py-4 px-6">
                        <div className="flex space-x-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {/* TODO: Implement edit functionality */}}
                          >
                            <Edit className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDeleteProxy(proxy.id)}
                            disabled={deleteProxyMutation.isPending}
                            className="text-red-600 hover:text-red-700"
                          >
                            {deleteProxyMutation.isPending ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                              <Trash2 className="w-4 h-4" />
                            )}
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AmazonSettings;
