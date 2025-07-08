import React from 'react';
import Sidebar from '@/components/Sidebar';
import PromptsManagement from '@/components/PromptsManagement';

const PromptsPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar activeSection="prompts" onSectionChange={() => {}} />
      <div className="flex-1 overflow-auto">
        <PromptsManagement />
      </div>
    </div>
  );
};

export default PromptsPage; 