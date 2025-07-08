import React from 'react';
import Sidebar from '@/components/Sidebar';
import { Server, Settings, AlertTriangle } from 'lucide-react';

const SystemMaintenance: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar activeSection="maintenance" onSectionChange={() => {}} />
      <div className="flex-1 overflow-auto">
        <div className="p-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 flex items-center">
              <Server className="w-8 h-8 mr-3 text-blue-600" />
              System Maintenance
            </h1>
            <p className="text-gray-600 mt-2">Enterprise system maintenance and management</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <div className="bg-white rounded-xl p-6 border border-gray-200">
              <div className="flex items-center mb-4">
                <Settings className="w-6 h-6 text-blue-500 mr-2" />
                <h3 className="text-lg font-semibold text-gray-900">System Status</h3>
              </div>
              <p className="text-gray-600 mb-4">All systems operational</p>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Last Backup</span>
                  <span className="text-sm font-medium text-green-600">2 hours ago</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Uptime</span>
                  <span className="text-sm font-medium text-green-600">99.9%</span>
                </div>
              </div>
            </div>
            
            <div className="bg-white rounded-xl p-6 border border-gray-200">
              <div className="flex items-center mb-4">
                <AlertTriangle className="w-6 h-6 text-yellow-500 mr-2" />
                <h3 className="text-lg font-semibold text-gray-900">Maintenance Tasks</h3>
              </div>
              <p className="text-gray-600 mb-4">0 pending tasks</p>
              <button className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700">
                Schedule Maintenance
              </button>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Maintenance Console</h2>
            <p className="text-gray-600">Advanced maintenance tools and system management coming soon...</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemMaintenance; 