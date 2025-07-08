import React from 'react';
import Sidebar from '@/components/Sidebar';
import { Eye, CheckCircle, AlertCircle, XCircle } from 'lucide-react';

const MonitoringHealth: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar activeSection="monitoring" onSectionChange={() => {}} />
      <div className="flex-1 overflow-auto">
        <div className="p-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 flex items-center">
              <Eye className="w-8 h-8 mr-3 text-blue-600" />
              Health Monitoring
            </h1>
            <p className="text-gray-600 mt-2">Real-time system health and service status</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            <div className="bg-white rounded-xl p-6 border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">API Server</p>
                  <p className="text-lg font-semibold text-green-600">Healthy</p>
                </div>
                <CheckCircle className="w-8 h-8 text-green-500" />
              </div>
            </div>
            
            <div className="bg-white rounded-xl p-6 border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Database</p>
                  <p className="text-lg font-semibold text-green-600">Healthy</p>
                </div>
                <CheckCircle className="w-8 h-8 text-green-500" />
              </div>
            </div>
            
            <div className="bg-white rounded-xl p-6 border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Cache</p>
                  <p className="text-lg font-semibold text-yellow-600">Warning</p>
                </div>
                <AlertCircle className="w-8 h-8 text-yellow-500" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Service Status</h2>
            <p className="text-gray-600">Comprehensive health monitoring dashboard coming soon...</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MonitoringHealth; 