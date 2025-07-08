import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Bot, Play, Pause, Square, Settings, RefreshCw, Loader2, AlertCircle, Plus, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';
import { apiClient } from '@/lib/api';

/**
 * Crawler type enumeration matching backend
 */
const CRAWLER_TYPES = [
  { value: 'product_scraper', label: 'Product Scraper' },
  { value: 'price_monitor', label: 'Price Monitor' },
  { value: 'review_collector', label: 'Review Collector' },
  { value: 'general_crawler', label: 'General Crawler' },
];

/**
 * Crawler status colors
 */
const getStatusColor = (status: string) => {
  switch (status) {
    case 'running': return 'bg-green-100 text-green-800';
    case 'paused': return 'bg-yellow-100 text-yellow-800';
    case 'stopped': return 'bg-red-100 text-red-800';
    case 'error': return 'bg-red-100 text-red-800';
    default: return 'bg-gray-100 text-gray-800';
  }
};

/**
 * Crawler status icon
 */
const getStatusIcon = (status: string) => {
  switch (status) {
    case 'running': return <Play className="w-4 h-4" />;
    case 'paused': return <Pause className="w-4 h-4" />;
    case 'stopped': return <Square className="w-4 h-4" />;
    case 'error': return <AlertCircle className="w-4 h-4" />;
    default: return <Settings className="w-4 h-4" />;
  }
};

/**
 * Format last run time
 */
const formatLastRun = (lastRunAt: string | null): string => {
  if (!lastRunAt) return 'Never';
  
  const now = new Date();
  const lastRun = new Date(lastRunAt);
  const diffMs = now.getTime() - lastRun.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins} minutes ago`;
  
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours} hours ago`;
  
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays} days ago`;
};

/**
 * Add Crawler Form Component
 */
interface AddCrawlerFormProps {
  onSubmit: (data: any) => void;
  onCancel: () => void;
  isLoading: boolean;
}

const AddCrawlerForm: React.FC<AddCrawlerFormProps> = ({ onSubmit, onCancel, isLoading }) => {
  const [formData, setFormData] = useState({
    name: '',
    crawler_type: 'general_crawler',
    target_url: '',
    css_selector: '',
    user_agent: 'Mozilla/5.0 (compatible; RevCopy-Bot/1.0)',
    interval_minutes: 5,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.name && formData.target_url) {
      onSubmit({
        ...formData,
        interval_minutes: Number(formData.interval_minutes),
      });
    }
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Add New Crawler</h3>
      <form onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Crawler Name*</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              placeholder="Enter crawler name..."
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Crawler Type</label>
            <select
              value={formData.crawler_type}
              onChange={(e) => setFormData({ ...formData, crawler_type: e.target.value })}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            >
              {CRAWLER_TYPES.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Target URL*</label>
            <input
              type="url"
              value={formData.target_url}
              onChange={(e) => setFormData({ ...formData, target_url: e.target.value })}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              placeholder="https://example.com"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Interval (minutes)</label>
            <select
              value={formData.interval_minutes}
              onChange={(e) => setFormData({ ...formData, interval_minutes: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            >
              <option value={1}>1 minute</option>
              <option value={5}>5 minutes</option>
              <option value={15}>15 minutes</option>
              <option value={30}>30 minutes</option>
              <option value={60}>1 hour</option>
            </select>
          </div>
        </div>
        
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">CSS Selector (Optional)</label>
          <input
            type="text"
            value={formData.css_selector}
            onChange={(e) => setFormData({ ...formData, css_selector: e.target.value })}
            className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            placeholder=".product-item, #content, etc."
          />
        </div>
        
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">User Agent</label>
          <input
            type="text"
            value={formData.user_agent}
            onChange={(e) => setFormData({ ...formData, user_agent: e.target.value })}
            className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            placeholder="User agent string..."
          />
        </div>
        
        <div className="flex space-x-3">
          <Button type="submit" disabled={isLoading} className="bg-green-600 hover:bg-green-700">
            {isLoading ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Bot className="w-4 h-4 mr-2" />
            )}
            Add Crawler
          </Button>
          <Button type="button" onClick={onCancel} variant="outline">
            Cancel
          </Button>
        </div>
      </form>
    </div>
  );
};

/**
 * Main Crawler Settings Component
 */
const CrawlerSettings: React.FC = () => {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [showAddForm, setShowAddForm] = useState(false);

  /**
   * Fetch crawlers from backend
   */
  const {
    data: crawlers = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['crawlers'],
    queryFn: async () => {
      const response = await apiClient.getCrawlers();
      if (!response.success) {
        throw new Error(response.message || 'Failed to fetch crawlers');
      }
      return response.data || [];
    },
    retry: 3,
  });

  /**
   * Create crawler mutation
   */
  const createCrawlerMutation = useMutation({
    mutationFn: async (crawlerData: any) => {
      const response = await apiClient.createCrawler(crawlerData);
      if (!response.success) {
        throw new Error(response.message || 'Failed to create crawler');
      }
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crawlers'] });
      setShowAddForm(false);
      toast({
        title: 'Success',
        description: 'Crawler created successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message,
        variant: 'destructive',
      });
    },
  });

  /**
   * Update crawler status mutation
   */
  const updateStatusMutation = useMutation({
    mutationFn: async ({ crawlerId, status }: { crawlerId: number; status: string }) => {
      const response = await apiClient.updateCrawlerStatus(crawlerId, status);
      if (!response.success) {
        throw new Error(response.message || 'Failed to update crawler status');
      }
      return response.data;
    },
    onSuccess: (_, { status }) => {
      queryClient.invalidateQueries({ queryKey: ['crawlers'] });
      toast({
        title: 'Success',
        description: `Crawler ${status === 'running' ? 'started' : status === 'paused' ? 'paused' : 'stopped'} successfully`,
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message,
        variant: 'destructive',
      });
    },
  });

  /**
   * Delete crawler mutation
   */
  const deleteCrawlerMutation = useMutation({
    mutationFn: async (crawlerId: number) => {
      const response = await apiClient.deleteCrawler(crawlerId);
      if (!response.success) {
        throw new Error(response.message || 'Failed to delete crawler');
      }
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crawlers'] });
      toast({
        title: 'Success',
        description: 'Crawler deleted successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message,
        variant: 'destructive',
      });
    },
  });

  /**
   * Handle status change
   */
  const handleStatusChange = (crawlerId: number, newStatus: string) => {
    updateStatusMutation.mutate({ crawlerId, status: newStatus });
  };

  /**
   * Handle delete with confirmation
   */
  const handleDelete = (crawlerId: number, crawlerName: string) => {
    if (window.confirm(`Are you sure you want to delete "${crawlerName}"? This action cannot be undone.`)) {
      deleteCrawlerMutation.mutate(crawlerId);
    }
  };

  /**
   * Render loading state
   */
  if (isLoading) {
    return (
      <div className="p-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Crawler Settings</h1>
            <p className="text-gray-600 mt-2">Configure and manage web crawlers and scrapers</p>
          </div>
        </div>
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
          <span className="ml-2 text-gray-600">Loading crawlers...</span>
        </div>
      </div>
    );
  }

  /**
   * Render error state
   */
  if (error) {
    return (
      <div className="p-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Crawler Settings</h1>
            <p className="text-gray-600 mt-2">Configure and manage web crawlers and scrapers</p>
          </div>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-start space-x-3">
            <AlertCircle className="h-5 w-5 text-red-400 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <h3 className="text-sm font-medium text-red-800">Failed to load crawlers</h3>
              <p className="text-sm text-red-600 mt-1">
                {error instanceof Error ? error.message : 'An unexpected error occurred'}
              </p>
              <Button 
                onClick={() => refetch()} 
                variant="outline" 
                size="sm" 
                className="mt-3"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Try Again
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Crawler Settings</h1>
          <p className="text-gray-600 mt-2">Configure and manage web crawlers and scrapers</p>
        </div>
        <Button 
          onClick={() => setShowAddForm(true)}
          className="bg-indigo-600 hover:bg-indigo-700"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Crawler
        </Button>
      </div>

      {/* Add Crawler Form */}
      {showAddForm && (
        <AddCrawlerForm
          onSubmit={(data) => createCrawlerMutation.mutate(data)}
          onCancel={() => setShowAddForm(false)}
          isLoading={createCrawlerMutation.isPending}
        />
      )}

      {/* Crawlers List */}
      {crawlers.length === 0 ? (
        <div className="text-center py-12">
          <Bot className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-semibold text-gray-900">No crawlers</h3>
          <p className="mt-1 text-sm text-gray-500">Get started by creating a new crawler.</p>
          <div className="mt-6">
            <Button
              onClick={() => setShowAddForm(true)}
              className="bg-indigo-600 hover:bg-indigo-700"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Crawler
            </Button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {crawlers.map((crawler: any) => (
            <div key={crawler.id} className="bg-white rounded-xl border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center">
                    <Bot className="w-6 h-6 text-indigo-600" />
                  </div>
                  <div className="ml-4">
                    <h3 className="text-lg font-semibold text-gray-900">{crawler.name}</h3>
                    <p className="text-sm text-gray-600">{crawler.target_url}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      Type: {CRAWLER_TYPES.find(t => t.value === crawler.crawler_type)?.label || crawler.crawler_type} • 
                      Interval: {crawler.interval_minutes} min • 
                      Last run: {formatLastRun(crawler.last_run_at)}
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-4">
                  <div className="text-right">
                    <div className="text-sm font-medium text-gray-900">
                      {crawler.items_collected} items
                    </div>
                    <div className="text-xs text-gray-500">
                      {crawler.successful_runs}/{crawler.total_runs} success
                    </div>
                  </div>
                  
                  <span className={`px-3 py-1 text-sm font-semibold rounded-full flex items-center space-x-1 ${getStatusColor(crawler.status)}`}>
                    {getStatusIcon(crawler.status)}
                    <span className="capitalize">{crawler.status}</span>
                  </span>
                  
                  <div className="flex space-x-2">
                    {crawler.status !== 'running' && (
                      <Button
                        size="sm"
                        onClick={() => handleStatusChange(crawler.id, 'running')}
                        className="bg-green-600 hover:bg-green-700"
                        disabled={updateStatusMutation.isPending}
                      >
                        <Play className="w-4 h-4" />
                      </Button>
                    )}
                    
                    {crawler.status === 'running' && (
                      <Button
                        size="sm"
                        onClick={() => handleStatusChange(crawler.id, 'paused')}
                        className="bg-yellow-600 hover:bg-yellow-700"
                        disabled={updateStatusMutation.isPending}
                      >
                        <Pause className="w-4 h-4" />
                      </Button>
                    )}
                    
                    {crawler.status !== 'stopped' && (
                      <Button
                        size="sm"
                        onClick={() => handleStatusChange(crawler.id, 'stopped')}
                        className="bg-red-600 hover:bg-red-700"
                        disabled={updateStatusMutation.isPending}
                      >
                        <Square className="w-4 h-4" />
                      </Button>
                    )}
                    
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleDelete(crawler.id, crawler.name)}
                      disabled={deleteCrawlerMutation.isPending || crawler.status === 'running'}
                      className="text-red-600 border-red-200 hover:bg-red-50"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>
              
              {crawler.last_error && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                  <div className="flex">
                    <AlertCircle className="h-4 w-4 text-red-400 mt-0.5 flex-shrink-0" />
                    <div className="ml-2">
                      <h4 className="text-sm font-medium text-red-800">Last Error</h4>
                      <p className="text-sm text-red-600 mt-1">{crawler.last_error}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default CrawlerSettings;
