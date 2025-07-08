import React, { useState, useEffect } from 'react';
import { api, handleApiError } from '../lib/api';
import { toast } from 'sonner';
import { Copy, Loader2, Calendar, Type, Globe, Hash } from 'lucide-react';
import Sidebar from '../components/Sidebar';

interface Campaign {
  id: number;
  name: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  content: Array<{
    id: number;
    content_type: string;
    title: string;
    content: string;
    word_count: number;
    character_count: number;
    language: string;
    created_at: string;
  }>;
}

const Campaigns = () => {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadCampaigns();
  }, []);

  const loadCampaigns = async () => {
    try {
      setIsLoading(true);
      const response = await api.campaigns.getCampaigns();
      
      if (response.success && response.data) {
        setCampaigns(response.data);
      } else {
        console.log('No campaigns found or error:', response.error);
        setCampaigns([]);
      }
    } catch (error) {
      console.error('Failed to load campaigns:', error);
      setCampaigns([]);
    } finally {
      setIsLoading(false);
    }
  };

  const copyContent = async (content: string) => {
    try {
      await navigator.clipboard.writeText(content);
      toast.success('Content copied to clipboard!');
    } catch (error) {
      toast.error('Failed to copy content');
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch {
      return 'Unknown date';
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#FDFDFD] flex">
        <Sidebar />
        <main className="flex-1 p-8">
          <div className="max-w-7xl mx-auto">
            <div className="flex items-center justify-center h-64">
              <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
              <span className="ml-2 text-gray-600">Loading campaigns...</span>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#FDFDFD] flex">
      <Sidebar />
      <main className="flex-1 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between mb-8">
            <h1 className="text-3xl font-bold text-gray-900">Campaigns</h1>
            <div className="text-sm text-gray-500">
              {campaigns.length} campaigns found
            </div>
          </div>

          {campaigns.length === 0 ? (
            <div className="bg-white rounded-lg shadow-sm border p-12 text-center">
              <Hash className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No campaigns yet</h3>
              <p className="text-gray-600 mb-4">
                Your saved campaigns will appear here. Start by generating content and saving it to a campaign.
              </p>
              <a 
                href="/" 
                className="inline-flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
              >
                Create Your First Campaign
              </a>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {campaigns.map((campaign) => (
                <div
                  key={campaign.id}
                  className="bg-white rounded-lg shadow-sm border hover:shadow-md transition-shadow"
                >
                  <div className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-1">
                          {campaign.name}
                        </h3>
                        {campaign.description && (
                          <p className="text-sm text-gray-600">{campaign.description}</p>
                        )}
                      </div>
                      <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                        campaign.is_active 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {campaign.is_active ? 'Active' : 'Inactive'}
                      </div>
                    </div>

                    <div className="flex items-center space-x-4 text-sm text-gray-500 mb-4">
                      <div className="flex items-center">
                        <Calendar className="w-4 h-4 mr-1" />
                        Created {formatDate(campaign.created_at)}
                      </div>
                      <div className="flex items-center">
                        <Type className="w-4 h-4 mr-1" />
                        {campaign.content.length} content pieces
                      </div>
                    </div>

                    {campaign.content.length > 0 && (
                      <div className="border-t pt-4">
                        <h4 className="text-sm font-medium text-gray-900 mb-3">Content</h4>
                        <div className="space-y-3">
                          {campaign.content.slice(0, 2).map((content) => (
                            <div
                              key={content.id}
                              className="border rounded-lg p-3 hover:bg-gray-50 transition-colors"
                            >
                              <div className="flex items-start justify-between mb-2">
                                <div className="flex items-center space-x-2">
                                  <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs font-medium">
                                    {content.content_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                  </span>
                                  <span className="text-xs text-gray-500">
                                    {content.word_count} words
                                  </span>
                                </div>
                                <button
                                  onClick={() => copyContent(content.content)}
                                  className="text-gray-400 hover:text-gray-600 transition-colors"
                                  title="Copy content"
                                >
                                  <Copy className="w-4 h-4" />
                                </button>
                              </div>
                              <p className="text-sm text-gray-700 line-clamp-2">
                                {content.content.substring(0, 150)}...
                              </p>
                              <div className="flex items-center justify-between mt-2">
                                <div className="flex items-center space-x-2 text-xs text-gray-500">
                                  <Globe className="w-3 h-3" />
                                  <span>{content.language.toUpperCase()}</span>
                                </div>
                                <span className="text-xs text-gray-500">
                                  {formatDate(content.created_at)}
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default Campaigns; 