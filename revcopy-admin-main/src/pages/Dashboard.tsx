import React from 'react';
import Sidebar from '@/components/Sidebar';
import Dashboard from '@/components/Dashboard';

const DashboardPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar activeSection="dashboard" onSectionChange={() => {}} />
      <div className="flex-1 overflow-auto">
        <Dashboard />
      </div>
    </div>
  );
};

export default DashboardPage; 