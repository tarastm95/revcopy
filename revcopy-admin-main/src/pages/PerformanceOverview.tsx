import React from 'react';
import Sidebar from '@/components/Sidebar';
import { Activity, TrendingUp, Database, Zap } from 'lucide-react';

const PerformanceOverview: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar activeSection="performance" onSectionChange={() => {}} />
      <div className="flex-1 overflow-auto">
        <div className="p-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 flex items-center">
              <Activity className="w-8 h-8 mr-3 text-blue-600" />
              Performance Overview
            </h1>
            <p className="text-gray-600 mt-2">Enterprise-grade system performance monitoring</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-xl p-6 border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">API Response Time</p>
                  <p className="text-2xl font-bold text-gray-900">45ms</p>
                </div>
                <TrendingUp className="w-8 h-8 text-green-500" />
              </div>
            </div>
            
            <div className="bg-white rounded-xl p-6 border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Database Queries</p>
                  <p className="text-2xl font-bold text-gray-900">1,234</p>
                </div>
                <Database className="w-8 h-8 text-blue-500" />
              </div>
            </div>
            
            <div className="bg-white rounded-xl p-6 border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Cache Hit Rate</p>
                  <p className="text-2xl font-bold text-gray-900">94%</p>
                </div>
                <Zap className="w-8 h-8 text-yellow-500" />
              </div>
            </div>
            
            <div className="bg-white rounded-xl p-6 border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Active Users</p>
                  <p className="text-2xl font-bold text-gray-900">156</p>
                </div>
                <Activity className="w-8 h-8 text-purple-500" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">System Performance</h2>
            <p className="text-gray-600">Enterprise performance monitoring dashboard coming soon...</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PerformanceOverview; 