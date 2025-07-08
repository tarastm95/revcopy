import React from 'react';
import Sidebar from '@/components/Sidebar';
import UsersManagement from '@/components/UsersManagement';

const UsersPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar activeSection="users" onSectionChange={() => {}} />
      <div className="flex-1 overflow-auto">
        <UsersManagement />
      </div>
    </div>
  );
};

export default UsersPage; 