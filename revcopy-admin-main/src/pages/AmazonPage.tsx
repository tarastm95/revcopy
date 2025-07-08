import React from 'react';
import Sidebar from '@/components/Sidebar';
import AmazonSettings from '@/components/AmazonSettings';

const AmazonPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar activeSection="amazon" onSectionChange={() => {}} />
      <div className="flex-1 overflow-auto">
        <AmazonSettings />
      </div>
    </div>
  );
};

export default AmazonPage; 