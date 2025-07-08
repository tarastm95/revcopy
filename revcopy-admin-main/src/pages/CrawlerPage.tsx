import React from 'react';
import Sidebar from '@/components/Sidebar';
import CrawlerSettings from '@/components/CrawlerSettings';

const CrawlerPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar activeSection="crawlers" onSectionChange={() => {}} />
      <div className="flex-1 overflow-auto">
        <CrawlerSettings />
      </div>
    </div>
  );
};

export default CrawlerPage; 