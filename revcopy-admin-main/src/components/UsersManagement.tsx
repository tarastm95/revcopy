/**
 * Users Management Component for RevCopy Admin Panel
 * 
 * Provides comprehensive user management with:
 * - Real-time data from backend API
 * - User search and filtering
 * - Status management (active/inactive)
 * - Pagination for large datasets
 * - User details and activity tracking
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Search, Plus, Edit, Trash2, Mail, Calendar, Users, AlertCircle, Loader2, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { apiClient } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

interface User {
  id: number;
  email: string;
  username: string;
  role: string;
  status: string;
  created_at: string;
  last_login_at: string | null;
}

interface UsersResponse {
  users: User[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

/**
 * Main Users Management Component
 */
const UsersManagement: React.FC = () => {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(20);

  /**
   * Fetch users from backend with pagination
   */
  const {
    data: usersData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['users', currentPage, pageSize, searchTerm],
    queryFn: async () => {
      const response = await apiClient.getUsers(currentPage, pageSize);
      if (!response.success) {
        throw new Error(response.message || 'Failed to fetch users');
      }
      return response.data as UsersResponse;
    },
    retry: 3,
    refetchInterval: 60000, // Refresh every minute
  });

  /**
   * Update user status mutation
   */
  const updateUserStatusMutation = useMutation({
    mutationFn: async ({ userId, status }: { userId: number; status: string }) => {
      const response = await apiClient.updateUserStatus(userId, status);
      if (!response.success) {
        throw new Error(response.message || 'Failed to update user status');
      }
      return response.data;
    },
    onSuccess: (_, { status }) => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      toast({
        title: 'Success',
        description: `User status updated to ${status}`,
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
   * Handle status toggle
   */
  const handleStatusToggle = async (user: User): Promise<void> => {
    const newStatus = user.status === 'active' ? 'inactive' : 'active';
    const confirmMessage = `Are you sure you want to ${newStatus === 'active' ? 'activate' : 'deactivate'} user "${user.username}"?`;
    
    if (window.confirm(confirmMessage)) {
      updateUserStatusMutation.mutate({ userId: user.id, status: newStatus });
    }
  };

  /**
   * Handle refresh
   */
  const handleRefresh = (): void => {
    refetch();
  };

  /**
   * Filter users based on search term
   */
  const filteredUsers = usersData?.users?.filter(user =>
    user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  /**
   * Format date for display
   */
  const formatDate = (dateString: string): string => {
    try {
      return new Date(dateString).toLocaleDateString();
    } catch {
      return 'Unknown';
    }
  };

  /**
   * Format last login for display
   */
  const formatLastLogin = (lastLogin: string | null): string => {
    if (!lastLogin) return 'Never';
    
    try {
      const date = new Date(lastLogin);
      const now = new Date();
      const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
      
      if (diffInHours < 1) return 'Less than 1 hour ago';
      if (diffInHours < 24) return `${diffInHours} hours ago`;
      if (diffInHours < 168) return `${Math.floor(diffInHours / 24)} days ago`;
      return date.toLocaleDateString();
    } catch {
      return 'Unknown';
    }
  };

  /**
   * Get status badge color
   */
  const getStatusBadge = (status: string): string => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'inactive':
        return 'bg-gray-100 text-gray-800';
      case 'pending_verification':
        return 'bg-yellow-100 text-yellow-800';
      case 'suspended':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  /**
   * Render loading state
   */
  if (isLoading) {
    return (
      <div className="p-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Users Management</h1>
            <p className="text-gray-600 mt-2">Manage registered users and their accounts</p>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-8">
          <div className="flex items-center justify-center">
            <Loader2 className="w-8 h-8 animate-spin text-indigo-600 mr-3" />
            <span className="text-gray-600">Loading users...</span>
          </div>
        </div>
      </div>
    );
  }

  /**
   * Render error state
   */
  if (error) {
    return (
      <div className="p-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Users Management</h1>
            <p className="text-gray-600 mt-2">Manage registered users and their accounts</p>
          </div>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <AlertCircle className="mx-auto h-12 w-12 text-red-400 mb-4" />
          <h3 className="text-lg font-medium text-red-800 mb-2">Failed to load users</h3>
          <p className="text-red-600 mb-4">
            {error instanceof Error ? error.message : 'An unexpected error occurred'}
          </p>
          <Button
            onClick={handleRefresh}
            className="bg-red-600 hover:bg-red-700 text-white"
          >
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Users Management</h1>
          <p className="text-gray-600 mt-2">
            Manage registered users and their accounts
            {usersData?.pagination && (
              <span className="ml-2 text-sm">
                ({usersData.pagination.total} total users)
              </span>
            )}
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <Button
            onClick={handleRefresh}
            variant="outline"
            className="flex items-center space-x-2"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Refresh</span>
          </Button>
          <Button className="bg-indigo-600 hover:bg-indigo-700">
            <Plus className="w-4 h-4 mr-2" />
            Add User
          </Button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Search users by username or email..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Users Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {filteredUsers.length === 0 ? (
          <div className="p-8 text-center">
            <Users className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No users found</h3>
            <p className="text-gray-600">
              {searchTerm ? 'Try adjusting your search criteria.' : 'No users have been registered yet.'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left py-4 px-6 text-sm font-semibold text-gray-900">User</th>
                  <th className="text-left py-4 px-6 text-sm font-semibold text-gray-900">Role</th>
                  <th className="text-left py-4 px-6 text-sm font-semibold text-gray-900">Registration Date</th>
                  <th className="text-left py-4 px-6 text-sm font-semibold text-gray-900">Status</th>
                  <th className="text-left py-4 px-6 text-sm font-semibold text-gray-900">Last Login</th>
                  <th className="text-left py-4 px-6 text-sm font-semibold text-gray-900">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredUsers.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-50">
                    <td className="py-4 px-6">
                      <div className="flex items-center">
                        <div className="w-10 h-10 bg-indigo-100 rounded-full flex items-center justify-center">
                          <span className="text-sm font-medium text-indigo-700">
                            {user.username.charAt(0).toUpperCase()}
                          </span>
                        </div>
                        <div className="ml-3">
                          <p className="text-sm font-medium text-gray-900">{user.username}</p>
                          <p className="text-sm text-gray-500 flex items-center">
                            <Mail className="w-3 h-3 mr-1" />
                            {user.email}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="py-4 px-6">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        user.role === 'admin' 
                          ? 'bg-purple-100 text-purple-800' 
                          : 'bg-blue-100 text-blue-800'
                      }`}>
                        {user.role}
                      </span>
                    </td>
                    <td className="py-4 px-6">
                      <div className="flex items-center text-sm text-gray-600">
                        <Calendar className="w-4 h-4 mr-2" />
                        {formatDate(user.created_at)}
                      </div>
                    </td>
                    <td className="py-4 px-6">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadge(user.status)}`}>
                        {user.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="py-4 px-6 text-sm text-gray-600">
                      {formatLastLogin(user.last_login_at)}
                    </td>
                    <td className="py-4 px-6">
                      <div className="flex items-center space-x-3">
                        <button 
                          className="text-indigo-600 hover:text-indigo-800 transition-colors"
                          title="Edit user"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                        <button 
                          onClick={() => handleStatusToggle(user)}
                          disabled={updateUserStatusMutation.isPending}
                          className={`transition-colors ${
                            user.status === 'active' 
                              ? 'text-red-600 hover:text-red-800' 
                              : 'text-green-600 hover:text-green-800'
                          } disabled:opacity-50`}
                          title={user.status === 'active' ? 'Deactivate user' : 'Activate user'}
                        >
                          {updateUserStatusMutation.isPending ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <Trash2 className="w-4 h-4" />
                          )}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination */}
      {usersData?.pagination && usersData.pagination.total_pages > 1 && (
        <div className="mt-6 flex items-center justify-between">
          <div className="text-sm text-gray-600">
            Showing {((currentPage - 1) * pageSize) + 1} to{' '}
            {Math.min(currentPage * pageSize, usersData.pagination.total)} of{' '}
            {usersData.pagination.total} results
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              onClick={() => setCurrentPage(currentPage - 1)}
              disabled={!usersData.pagination.has_prev}
            >
              Previous
            </Button>
            <span className="px-4 py-2 text-sm text-gray-600">
              Page {currentPage} of {usersData.pagination.total_pages}
            </span>
            <Button
              variant="outline"
              onClick={() => setCurrentPage(currentPage + 1)}
              disabled={!usersData.pagination.has_next}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default UsersManagement;
