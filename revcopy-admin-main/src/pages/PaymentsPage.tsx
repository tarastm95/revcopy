import React from 'react';
import Sidebar from '@/components/Sidebar';
import PaymentsManagement from '@/components/PaymentsManagement';

const PaymentsPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar activeSection="payments" onSectionChange={() => {}} />
      <div className="flex-1 overflow-auto">
        <PaymentsManagement />
      </div>
    </div>
  );
};

export default PaymentsPage; 