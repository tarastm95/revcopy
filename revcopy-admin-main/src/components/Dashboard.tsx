/**
 * Dashboard Component for RevCopy Admin Panel
 * 
 * Provides overview of system statistics and analytics including:
 * - User metrics and growth
 * - Content generation statistics  
 * - System performance indicators
 * - Recent activity overview
 */

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Users, FileText, Target, TrendingUp, Activity, Clock } from 'lucide-react';
import { apiClient } from '@/lib/api';

/**
 * Main Dashboard Component
 */
const Dashboard: React.FC = () => {
  /**
   * Fetch dashboard statistics
   */
  const {
    data: dashboardStats,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const response = await apiClient.getDashboardStats();
      if (!response.success) {
        throw new Error(response.message || 'Failed to fetch dashboard statistics');
      }
      return response.data;
    },
    refetchInterval: 30000, // Refresh every 30 seconds
    retry: 3,
  });

  /**
   * Handle refresh button click
   */
  const handleRefresh = (): void => {
    refetch();
  };

  /**
   * Render loading state
   */
  if (isLoading) {
    return (
      <div className="p-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-600 mt-2">Overview of your RevCopy system</p>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {[...Array(4)].map((_, index) => (
            <div key={index} className="bg-white rounded-xl border border-gray-200 p-6 animate-pulse">
              <div className="flex items-center">
                <div className="p-2 bg-gray-200 rounded-lg w-12 h-12"></div>
                <div className="ml-4 flex-1">
                  <div className="h-4 bg-gray-200 rounded w-20 mb-2"></div>
                  <div className="h-6 bg-gray-200 rounded w-16"></div>
                </div>
              </div>
            </div>
          ))}
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
            <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-600 mt-2">Overview of your RevCopy system</p>
          </div>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <Activity className="mx-auto h-12 w-12 text-red-400 mb-4" />
          <h3 className="text-lg font-medium text-red-800 mb-2">Failed to load dashboard data</h3>
          <p className="text-red-600 mb-4">
            {error instanceof Error ? error.message : 'An unexpected error occurred'}
          </p>
          <button
            onClick={handleRefresh}
            className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  /**
   * Format growth percentage from backend data
   */
  const formatGrowthPercentage = (growthData?: { percentage?: number; trend?: 'up' | 'down' | 'stable' }): string => {
    if (!growthData || growthData.percentage === undefined) {
      return '—';
    }
    const percentage = growthData.percentage;
    return `${percentage >= 0 ? '+' : ''}${percentage.toFixed(1)}%`;
  };

  /**
   * Get growth trend type
   */
  const getGrowthType = (growthData?: { percentage?: number; trend?: 'up' | 'down' | 'stable' }): 'positive' | 'negative' | 'neutral' => {
    if (!growthData || growthData.percentage === undefined) {
      return 'neutral';
    }
    return growthData.percentage >= 0 ? 'positive' : 'negative';
  };

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-2">Overview of your RevCopy system</p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-sm text-gray-500">
            Last updated: {dashboardStats?.last_updated ? 
              new Date(dashboardStats.last_updated).toLocaleTimeString() : 
              'Unknown'
            }
          </div>
          <button
            onClick={handleRefresh}
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg transition-colors flex items-center space-x-2"
          >
            <Activity className="w-4 h-4" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {/* Total Users */}
        <StatCard
          title="Total Users"
          value={dashboardStats?.users?.total?.toLocaleString() || '0'}
          change={formatGrowthPercentage(dashboardStats?.users?.growth)}
          changeType={getGrowthType(dashboardStats?.users?.growth)}
          icon={<Users className="w-8 h-8 text-blue-600" />}
          bgColor="bg-blue-50"
          subtitle={`${dashboardStats?.users?.active_30d || 0} active this month`}
        />

        {/* Products Analyzed */}
        <StatCard
          title="Products Analyzed"
          value={dashboardStats?.products?.total?.toLocaleString() || '0'}
          change={formatGrowthPercentage(dashboardStats?.products?.growth)}
          changeType={getGrowthType(dashboardStats?.products?.growth)}
          icon={<Target className="w-8 h-8 text-green-600" />}
          bgColor="bg-green-50"
          subtitle={`${dashboardStats?.products?.analyzed_30d || 0} this month`}
        />

        {/* Content Generated */}
        <StatCard
          title="Content Generated"
          value={dashboardStats?.content?.total?.toLocaleString() || '0'}
          change={formatGrowthPercentage(dashboardStats?.content?.growth)}
          changeType={getGrowthType(dashboardStats?.content?.growth)}
          icon={<FileText className="w-8 h-8 text-purple-600" />}
          bgColor="bg-purple-50"
          subtitle={`${dashboardStats?.content?.generated_30d || 0} this month`}
        />

        {/* Active Templates */}
        <StatCard
          title="Active Templates"
          value={dashboardStats?.templates?.active?.toString() || '0'}
          change={formatGrowthPercentage(dashboardStats?.templates?.growth)}
          changeType={getGrowthType(dashboardStats?.templates?.growth)}
          icon={<TrendingUp className="w-8 h-8 text-orange-600" />}
          bgColor="bg-orange-50"
          subtitle="AI prompt templates"
        />
      </div>

      {/* Recent Activity Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Quick Actions */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="space-y-4">
            <QuickActionCard
              title="Manage Prompt Templates"
              description="Create, edit, and organize AI prompt templates"
              icon={<FileText className="w-6 h-6 text-indigo-600" />}
              buttonText="Manage Templates"
              onClick={() => {/* Handle navigation to prompts */}}
            />
            <QuickActionCard
              title="View User Analytics"
              description="Monitor user activity and system usage"
              icon={<Users className="w-6 h-6 text-blue-600" />}
              buttonText="View Users"
              onClick={() => {/* Handle navigation to users */}}
            />
            <QuickActionCard
              title="System Settings"
              description="Configure system parameters and AI providers"
              icon={<Activity className="w-6 h-6 text-green-600" />}
              buttonText="Open Settings"
              onClick={() => {/* Handle navigation to settings */}}
            />
          </div>
        </div>

        {/* System Status */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">System Status</h2>
          <div className="space-y-4">
            <StatusItem
              label="API Server"
              status="operational"
              lastCheck="1 minute ago"
            />
            <StatusItem
              label="Database"
              status="operational"
              lastCheck="2 minutes ago"
            />
            <StatusItem
              label="AI Provider (DeepSeek)"
              status="operational"
              lastCheck="30 seconds ago"
            />
            <StatusItem
              label="Content Generation"
              status="operational"
              lastCheck="1 minute ago"
            />
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * Stat Card Component
 */
interface StatCardProps {
  title: string;
  value: string;
  change: string;
  changeType: 'positive' | 'negative' | 'neutral';
  icon: React.ReactNode;
  bgColor: string;
  subtitle?: string;
}

const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  change,
  changeType,
  icon,
  bgColor,
  subtitle,
}) => {
  const getChangeColor = (type: string): string => {
    switch (type) {
      case 'positive':
        return 'text-green-600';
      case 'negative':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-center justify-between mb-4">
        <div className={`p-3 rounded-lg ${bgColor}`}>
          {icon}
        </div>
        <span className={`text-sm font-medium ${getChangeColor(changeType)}`}>
          {change}
        </span>
      </div>
      <div>
        <h3 className="text-2xl font-bold text-gray-900 mb-1">{value}</h3>
        <p className="text-sm font-medium text-gray-700 mb-1">{title}</p>
        {subtitle && (
          <p className="text-xs text-gray-500">{subtitle}</p>
        )}
      </div>
    </div>
  );
};

/**
 * Quick Action Card Component
 */
interface QuickActionCardProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  buttonText: string;
  onClick: () => void;
}

const QuickActionCard: React.FC<QuickActionCardProps> = ({
  title,
  description,
  icon,
  buttonText,
  onClick,
}) => {
  return (
    <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
      <div className="flex items-center space-x-3">
        <div className="p-2 bg-white rounded-lg shadow-sm">
          {icon}
        </div>
        <div>
          <h4 className="text-sm font-medium text-gray-900">{title}</h4>
          <p className="text-xs text-gray-600">{description}</p>
        </div>
      </div>
      <button
        onClick={onClick}
        className="text-sm bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-1 rounded-lg transition-colors"
      >
        {buttonText}
      </button>
    </div>
  );
};

/**
 * Status Item Component
 */
interface StatusItemProps {
  label: string;
  status: 'operational' | 'degraded' | 'down';
  lastCheck: string;
}

const StatusItem: React.FC<StatusItemProps> = ({ label, status, lastCheck }) => {
  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'operational':
        return {
          color: 'bg-green-500',
          text: 'Operational',
          textColor: 'text-green-700',
        };
      case 'degraded':
        return {
          color: 'bg-yellow-500',
          text: 'Degraded',
          textColor: 'text-yellow-700',
        };
      case 'down':
        return {
          color: 'bg-red-500',
          text: 'Down',
          textColor: 'text-red-700',
        };
      default:
        return {
          color: 'bg-gray-500',
          text: 'Unknown',
          textColor: 'text-gray-700',
        };
    }
  };

  const statusConfig = getStatusConfig(status);

  return (
    <div className="flex items-center justify-between py-2">
      <div className="flex items-center space-x-3">
        <div className={`w-3 h-3 rounded-full ${statusConfig.color}`}></div>
        <span className="text-sm font-medium text-gray-900">{label}</span>
      </div>
      <div className="text-right">
        <div className={`text-sm font-medium ${statusConfig.textColor}`}>
          {statusConfig.text}
        </div>
        <div className="text-xs text-gray-500 flex items-center">
          <Clock className="w-3 h-3 mr-1" />
          {lastCheck}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
