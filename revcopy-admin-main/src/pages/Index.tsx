
import React, { useState } from 'react';
import Sidebar from '@/components/Sidebar';
import Dashboard from '@/components/Dashboard';
import UsersManagement from '@/components/UsersManagement';
import PaymentsManagement from '@/components/PaymentsManagement';
import PromptsManagement from '@/components/PromptsManagement';
import AdminsManagement from '@/components/AdminsManagement';
import CrawlerSettings from '@/components/CrawlerSettings';
import AmazonSettings from '@/components/AmazonSettings';

const Index = () => {
  const [activeSection, setActiveSection] = useState('dashboard');

  const renderContent = () => {
    switch (activeSection) {
      case 'dashboard':
        return <Dashboard />;
      case 'users':
        return <UsersManagement />;
      case 'payments':
        return <PaymentsManagement />;
      case 'prompts':
        return <PromptsManagement />;
      case 'admins':
        return <AdminsManagement />;
      case 'crawlers':
        return <CrawlerSettings />;
      case 'amazon':
        return <AmazonSettings />;
      case 'settings':
        return (
          <div className="p-8">
            <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
            <p className="text-gray-600 mt-2">General application settings and configurations</p>
            <div className="mt-8 bg-white rounded-xl border border-gray-200 p-6">
              <p className="text-gray-500">Settings panel coming soon...</p>
            </div>
          </div>
        );
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar activeSection={activeSection} onSectionChange={setActiveSection} />
      <div className="flex-1 overflow-auto">
        {renderContent()}
      </div>
    </div>
  );
};

export default Index;
