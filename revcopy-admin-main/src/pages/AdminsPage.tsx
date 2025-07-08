import React from 'react';
import Sidebar from '@/components/Sidebar';
import AdminsManagement from '@/components/AdminsManagement';

const AdminsPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar activeSection="admins" onSectionChange={() => {}} />
      <div className="flex-1 overflow-auto">
        <AdminsManagement />
      </div>
    </div>
  );
};

export default AdminsPage; 