/**
 * Admins Management Component for RevCopy Admin Panel
 * 
 * Provides comprehensive admin user management with:
 * - Real-time data from backend API
 * - Admin creation and role management
 * - Status tracking and permissions
 * - Security-focused admin operations
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Edit, Trash2, Shield, Mail, Loader2, AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { apiClient } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

interface Admin {
  id: number;
  name: string;
  email: string;
  role: string;
  status: string;
  last_login_at: string | null;
  created_at: string;
}

interface NewAdminData {
  name: string;
  email: string;
  role: string;
  password: string;
}

/**
 * Main Admins Management Component
 */
const AdminsManagement: React.FC = () => {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  
  const [showAddForm, setShowAddForm] = useState(false);
  const [newAdmin, setNewAdmin] = useState<NewAdminData>({
    name: '',
    email: '',
    role: 'admin',
    password: ''
  });

  /**
   * Fetch administrators from backend
   */
  const {
    data: admins = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['admins'],
    queryFn: async () => {
      const response = await apiClient.getAdmins();
      if (!response.success) {
        throw new Error(response.message || 'Failed to fetch administrators');
      }
      return response.data || [];
    },
    retry: 3,
    refetchInterval: 60000, // Refresh every minute
  });

  /**
   * Create new admin mutation
   */
  const createAdminMutation = useMutation({
    mutationFn: async (adminData: NewAdminData) => {
      const response = await apiClient.createAdmin(adminData);
      if (!response.success) {
        throw new Error(response.message || 'Failed to create administrator');
      }
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admins'] });
      setNewAdmin({ name: '', email: '', role: 'admin', password: '' });
      setShowAddForm(false);
      toast({
        title: 'Success',
        description: 'Administrator created successfully',
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
   * Delete admin mutation
   */
  const deleteAdminMutation = useMutation({
    mutationFn: async (adminId: number) => {
      const response = await apiClient.deleteAdmin(adminId);
      if (!response.success) {
        throw new Error(response.message || 'Failed to delete administrator');
      }
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admins'] });
      toast({
        title: 'Success',
        description: 'Administrator deleted successfully',
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
   * Handle form submission
   */
  const handleAddAdmin = (): void => {
    if (!newAdmin.name || !newAdmin.email || !newAdmin.password) {
      toast({
        title: 'Validation Error',
        description: 'Please fill in all required fields',
        variant: 'destructive',
      });
      return;
    }

    if (!newAdmin.email.includes('@')) {
      toast({
        title: 'Validation Error',
        description: 'Please enter a valid email address',
        variant: 'destructive',
      });
      return;
    }

    createAdminMutation.mutate(newAdmin);
  };

  /**
   * Handle admin deletion
   */
  const handleDeleteAdmin = (adminId: number): void => {
    if (window.confirm('Are you sure you want to delete this administrator? This action cannot be undone.')) {
      deleteAdminMutation.mutate(adminId);
    }
  };

  /**
   * Handle refresh
   */
  const handleRefresh = (): void => {
    refetch();
  };

  /**
   * Format last login time
   */
  const formatLastLogin = (lastLogin: string | null): string => {
    if (!lastLogin) return 'Never';
    
    const date = new Date(lastLogin);
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
   * Get role styling
   */
  const getRoleColor = (role: string): string => {
    switch (role.toLowerCase()) {
      case 'super_admin': return 'bg-red-100 text-red-800';
      case 'admin': return 'bg-blue-100 text-blue-800';
      case 'moderator': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  /**
   * Render error state
   */
  if (error) {
    return (
      <div className="p-8">
        <div className="text-center">
          <AlertCircle className="mx-auto h-12 w-12 text-red-500" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">Error loading administrators</h3>
          <p className="mt-1 text-sm text-gray-500">
            {error instanceof Error ? error.message : 'An unknown error occurred'}
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
          <h1 className="text-3xl font-bold text-gray-900">Admins & Users Management</h1>
          <p className="text-gray-600 mt-2">
            Manage administrators and user permissions
            {admins.length > 0 && (
              <span className="ml-2 text-sm">({admins.length} total administrators)</span>
            )}
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <Button
            onClick={handleRefresh}
            variant="outline"
            disabled={isLoading}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button 
            onClick={() => setShowAddForm(true)}
            className="bg-indigo-600 hover:bg-indigo-700"
            disabled={showAddForm}
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Admin
          </Button>
        </div>
      </div>

      {/* Add Admin Form */}
      {showAddForm && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Add New Administrator</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Full Name *</label>
              <input
                type="text"
                value={newAdmin.name}
                onChange={(e) => setNewAdmin({ ...newAdmin, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                placeholder="Enter full name..."
                disabled={createAdminMutation.isPending}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Email *</label>
              <input
                type="email"
                value={newAdmin.email}
                onChange={(e) => setNewAdmin({ ...newAdmin, email: e.target.value })}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                placeholder="Enter email address..."
                disabled={createAdminMutation.isPending}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Role</label>
              <select
                value={newAdmin.role}
                onChange={(e) => setNewAdmin({ ...newAdmin, role: e.target.value })}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                disabled={createAdminMutation.isPending}
              >
                <option value="admin">Admin</option>
                <option value="moderator">Moderator</option>
                <option value="super_admin">Super Admin</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Password *</label>
              <input
                type="password"
                value={newAdmin.password}
                onChange={(e) => setNewAdmin({ ...newAdmin, password: e.target.value })}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                placeholder="Enter secure password..."
                disabled={createAdminMutation.isPending}
              />
            </div>
          </div>
          <div className="flex space-x-3">
            <Button 
              onClick={handleAddAdmin} 
              className="bg-green-600 hover:bg-green-700"
              disabled={createAdminMutation.isPending}
            >
              {createAdminMutation.isPending ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Plus className="w-4 h-4 mr-2" />
              )}
              {createAdminMutation.isPending ? 'Creating...' : 'Add Admin'}
            </Button>
            <Button 
              onClick={() => setShowAddForm(false)} 
              variant="outline"
              disabled={createAdminMutation.isPending}
            >
              Cancel
            </Button>
          </div>
        </div>
      )}

      {/* Loading State */}
      {isLoading && !admins.length && (
        <div className="bg-white rounded-xl border border-gray-200 p-8">
          <div className="text-center">
            <Loader2 className="mx-auto h-8 w-8 animate-spin text-indigo-600" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">Loading administrators...</h3>
            <p className="mt-1 text-sm text-gray-500">Please wait while we fetch the data.</p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && admins.length === 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-8">
          <div className="text-center">
            <Shield className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No administrators found</h3>
            <p className="mt-1 text-sm text-gray-500">Get started by adding your first administrator.</p>
            <div className="mt-6">
              <Button onClick={() => setShowAddForm(true)} className="bg-indigo-600 hover:bg-indigo-700">
                <Plus className="w-4 h-4 mr-2" />
                Add First Admin
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Admins Table */}
      {admins.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left py-4 px-6 text-sm font-semibold text-gray-900">Administrator</th>
                  <th className="text-left py-4 px-6 text-sm font-semibold text-gray-900">Role</th>
                  <th className="text-left py-4 px-6 text-sm font-semibold text-gray-900">Status</th>
                  <th className="text-left py-4 px-6 text-sm font-semibold text-gray-900">Last Login</th>
                  <th className="text-left py-4 px-6 text-sm font-semibold text-gray-900">Created</th>
                  <th className="text-left py-4 px-6 text-sm font-semibold text-gray-900">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {admins.map((admin: Admin) => (
                  <tr key={admin.id} className="hover:bg-gray-50">
                    <td className="py-4 px-6">
                      <div className="flex items-center">
                        <div className="w-10 h-10 bg-indigo-100 rounded-full flex items-center justify-center">
                          <Shield className="w-5 h-5 text-indigo-600" />
                        </div>
                        <div className="ml-3">
                          <p className="text-sm font-medium text-gray-900">{admin.name}</p>
                          <p className="text-sm text-gray-500 flex items-center">
                            <Mail className="w-3 h-3 mr-1" />
                            {admin.email}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="py-4 px-6">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getRoleColor(admin.role)}`}>
                        {admin.role.replace('_', ' ').toUpperCase()}
                      </span>
                    </td>
                    <td className="py-4 px-6">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        admin.status === 'active' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {admin.status.toUpperCase()}
                      </span>
                    </td>
                    <td className="py-4 px-6 text-sm text-gray-600">
                      {formatLastLogin(admin.last_login_at)}
                    </td>
                    <td className="py-4 px-6 text-sm text-gray-600">
                      {new Date(admin.created_at).toLocaleDateString()}
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
                          onClick={() => handleDeleteAdmin(admin.id)}
                          disabled={deleteAdminMutation.isPending}
                          className="text-red-600 hover:text-red-700"
                        >
                          {deleteAdminMutation.isPending ? (
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
  );
};

export default AdminsManagement;
