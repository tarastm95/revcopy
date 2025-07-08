/**
 * Payments Management Component for RevCopy Admin Panel
 * 
 * Provides comprehensive payment management with:
 * - Real-time payment data from backend API
 * - Payment status tracking and filtering
 * - Revenue analytics and statistics
 * - Payment method insights
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, DollarSign, TrendingUp, Calendar, Loader2, AlertCircle, RefreshCw, CreditCard } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { apiClient } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

interface Payment {
  id: string;
  user_name: string;
  user_email: string;
  amount: number;
  currency: string;
  status: string;
  payment_method: string;
  created_at: string;
  updated_at: string;
}

interface PaymentStats {
  total_revenue: number;
  monthly_revenue: number;
  average_payment: number;
  success_rate: number;
  total_payments: number;
  monthly_payments: number;
}

/**
 * Main Payments Management Component
 */
const PaymentsManagement: React.FC = () => {
  const { toast } = useToast();
  const [timeFilter, setTimeFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  /**
   * Fetch payments from backend
   */
  const {
    data: paymentsData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['payments', timeFilter],
    queryFn: async () => {
      const response = await apiClient.getPayments(timeFilter);
      if (!response.success) {
        throw new Error(response.message || 'Failed to fetch payments');
      }
      return response.data;
    },
    retry: 3,
    refetchInterval: 60000, // Refresh every minute
  });

  /**
   * Fetch payment statistics
   */
  const {
    data: statsData,
    isLoading: isLoadingStats,
    error: statsError,
  } = useQuery({
    queryKey: ['payment-stats', timeFilter],
    queryFn: async () => {
      const response = await apiClient.getPaymentStats(timeFilter);
      if (!response.success) {
        throw new Error(response.message || 'Failed to fetch payment statistics');
      }
      return response.data;
    },
    retry: 3,
    refetchInterval: 60000,
  });

  /**
   * Handle refresh
   */
  const handleRefresh = (): void => {
    refetch();
  };

  /**
   * Format currency amount
   */
  const formatCurrency = (amount: number, currency: string = 'USD'): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency.toUpperCase(),
    }).format(amount);
  };

  /**
   * Format date
   */
  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  /**
   * Get status styling
   */
  const getStatusColor = (status: string): string => {
    switch (status.toLowerCase()) {
      case 'completed': 
      case 'success':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'failed':
      case 'error':
        return 'bg-red-100 text-red-800';
      case 'cancelled':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-blue-100 text-blue-800';
    }
  };

  /**
   * Filter payments based on search term
   */
  const filteredPayments = React.useMemo(() => {
    if (!paymentsData?.payments) return [];
    
    if (!searchTerm) return paymentsData.payments;
    
    return paymentsData.payments.filter((payment: Payment) =>
      payment.user_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      payment.user_email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      payment.id.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [paymentsData?.payments, searchTerm]);

  /**
   * Render error state
   */
  if (error || statsError) {
    return (
      <div className="p-8">
        <div className="text-center">
          <AlertCircle className="mx-auto h-12 w-12 text-red-500" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">Error loading payments</h3>
          <p className="mt-1 text-sm text-gray-500">
            {(error || statsError) instanceof Error 
              ? (error || statsError)?.message 
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
          <h1 className="text-3xl font-bold text-gray-900">Payments Management</h1>
          <p className="text-gray-600 mt-2">
            Monitor and manage payment transactions
            {paymentsData?.payments && (
              <span className="ml-2 text-sm">
                ({paymentsData.payments.length} total payments)
              </span>
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
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {isLoadingStats ? (
          [...Array(4)].map((_, index) => (
            <div key={index} className="bg-white rounded-xl border border-gray-200 p-6 animate-pulse">
              <div className="flex items-center">
                <div className="p-2 bg-gray-200 rounded-lg w-12 h-12"></div>
                <div className="ml-4 flex-1">
                  <div className="h-4 bg-gray-200 rounded w-20 mb-2"></div>
                  <div className="h-6 bg-gray-200 rounded w-16"></div>
                </div>
              </div>
            </div>
          ))
        ) : (
          <>
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <div className="flex items-center">
                <div className="p-2 bg-green-100 rounded-lg">
                  <DollarSign className="w-6 h-6 text-green-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm text-gray-600">Total Revenue</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {formatCurrency(statsData?.total_revenue || 0)}
                  </p>
                  <p className="text-sm text-green-600">
                    <TrendingUp className="w-3 h-3 inline mr-1" />
                    +{Math.round((statsData?.monthly_revenue || 0) / (statsData?.total_revenue || 1) * 100)}%
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <div className="flex items-center">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Calendar className="w-6 h-6 text-blue-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm text-gray-600">Monthly Revenue</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {formatCurrency(statsData?.monthly_revenue || 0)}
                  </p>
                  <p className="text-sm text-blue-600">
                    {statsData?.monthly_payments || 0} payments
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <div className="flex items-center">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <TrendingUp className="w-6 h-6 text-purple-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm text-gray-600">Average Payment</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {formatCurrency(statsData?.average_payment || 0)}
                  </p>
                  <p className="text-sm text-purple-600">per transaction</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <div className="flex items-center">
                <div className="p-2 bg-orange-100 rounded-lg">
                  <CreditCard className="w-6 h-6 text-orange-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm text-gray-600">Success Rate</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {(statsData?.success_rate || 0).toFixed(1)}%
                  </p>
                  <p className="text-sm text-orange-600">payment success</p>
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-col md:flex-row gap-4 mb-6">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Search payments..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>
        </div>
        <select
          value={timeFilter}
          onChange={(e) => setTimeFilter(e.target.value)}
          className="px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
        >
          <option value="all">All Time</option>
          <option value="today">Today</option>
          <option value="week">This Week</option>
          <option value="month">This Month</option>
          <option value="year">This Year</option>
        </select>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="bg-white rounded-xl border border-gray-200 p-8">
          <div className="text-center">
            <Loader2 className="mx-auto h-8 w-8 animate-spin text-indigo-600" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">Loading payments...</h3>
            <p className="mt-1 text-sm text-gray-500">Please wait while we fetch the data.</p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && filteredPayments.length === 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-8">
          <div className="text-center">
            <CreditCard className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No payments found</h3>
            <p className="mt-1 text-sm text-gray-500">
              {searchTerm ? 'Try adjusting your search criteria.' : 'No payments have been processed yet.'}
            </p>
          </div>
        </div>
      )}

      {/* Payments Table */}
      {filteredPayments.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left py-4 px-6 text-sm font-semibold text-gray-900">Payment ID</th>
                  <th className="text-left py-4 px-6 text-sm font-semibold text-gray-900">Customer</th>
                  <th className="text-left py-4 px-6 text-sm font-semibold text-gray-900">Amount</th>
                  <th className="text-left py-4 px-6 text-sm font-semibold text-gray-900">Status</th>
                  <th className="text-left py-4 px-6 text-sm font-semibold text-gray-900">Method</th>
                  <th className="text-left py-4 px-6 text-sm font-semibold text-gray-900">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredPayments.map((payment: Payment) => (
                  <tr key={payment.id} className="hover:bg-gray-50">
                    <td className="py-4 px-6">
                      <code className="text-sm font-mono text-gray-600">{payment.id}</code>
                    </td>
                    <td className="py-4 px-6">
                      <div>
                        <p className="text-sm font-medium text-gray-900">{payment.user_name}</p>
                        <p className="text-sm text-gray-500">{payment.user_email}</p>
                      </div>
                    </td>
                    <td className="py-4 px-6">
                      <span className="text-sm font-medium text-gray-900">
                        {formatCurrency(payment.amount, payment.currency)}
                      </span>
                    </td>
                    <td className="py-4 px-6">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(payment.status)}`}>
                        {payment.status.toUpperCase()}
                      </span>
                    </td>
                    <td className="py-4 px-6">
                      <span className="text-sm text-gray-600">
                        {payment.payment_method}
                      </span>
                    </td>
                    <td className="py-4 px-6">
                      <span className="text-sm text-gray-600">
                        {formatDate(payment.created_at)}
                      </span>
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

export default PaymentsManagement;
