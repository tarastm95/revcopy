/**
 * API utilities for RevCopy backend communication
 */

// Determine the appropriate API base URL based on the current location
const getApiBaseUrl = () => {
  // If we're running on a network IP, use that same network IP for the backend
  if (window.location.hostname.startsWith('192.168.') || window.location.hostname.startsWith('10.') || window.location.hostname.startsWith('172.')) {
    return `http://${window.location.hostname}:8000`;
  }
  // Otherwise use localhost or environment variable
  return import.meta.env.VITE_API_URL || 'http://localhost:8000';
};

const API_BASE_URL = getApiBaseUrl();
const API_VERSION = import.meta.env.VITE_API_VERSION || 'v1';

export const API_ENDPOINTS = {
  // Products
  PRODUCTS: {
    ANALYZE: `/api/${API_VERSION}/products/analyze`,
    LIST: `/api/${API_VERSION}/products/`,
    DETAIL: (id: number) => `/api/${API_VERSION}/products/${id}`,
    STATS: `/api/${API_VERSION}/products/stats/summary`,
    VALIDATE: `/api/${API_VERSION}/products/validate`,
  },
  // Analysis
  ANALYSIS: {
    STATUS: (id: number) => `/api/${API_VERSION}/analysis/${id}`,
    RESULTS: (id: number) => `/api/${API_VERSION}/analysis/${id}/results`,
  },
  // Content Generation
  GENERATION: {
    GENERATE: `/api/${API_VERSION}/content-generation/generate`,
    INTELLIGENT: `/api/${API_VERSION}/content-generation/intelligent/generate`,
    HISTORY: `/api/${API_VERSION}/content-generation/history`,
    FEEDBACK: `/api/${API_VERSION}/content-generation/feedback`,
    STATUS: `/api/${API_VERSION}/content-generation/status`,
    TEMPLATES: `/api/${API_VERSION}/content-generation/templates`,
  },
  // Campaigns
  CAMPAIGNS: {
    LIST: `/api/${API_VERSION}/campaigns/`,
    CREATE: `/api/${API_VERSION}/campaigns/`,
    DETAIL: (id: number) => `/api/${API_VERSION}/campaigns/${id}`,
  },
};

/**
 * API Response types
 */
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

export interface ProductAnalysisRequest {
  url: string;
  analysis_type?: 'basic' | 'full_analysis';
  max_reviews?: number;
}

export interface ProductAnalysisResponse {
  id: number;
  url: string;
  title: string;
  description?: string;
  brand?: string;
  category?: string;
  price: number;
  currency: string;
  original_price?: number;
  rating?: number;
  review_count: number;
  in_stock: boolean;
  platform: string;
  status: string;
  analysis_id?: number;
  crawl_metadata?: any;
  tags?: string[];
  created_at: string;
  updated_at?: string;
}

export interface IntelligentContentRequest {
  product_url: string;
  content_type: string;
  language?: string;
  cultural_region?: string;
  country_code?: string;
  target_audience?: string;
  tone?: string;
  urgency_level?: string;
  brand_personality?: string;
  price_range?: string;
  product_category?: string;
  custom_variables?: Record<string, any>;
}

export interface IntelligentContentResponse {
  content: string;
  template_id: number;
  template_name: string;
  adaptation_id?: number;
  generation_time_ms: number;
  selection_score: number;
  adaptations_applied: Record<string, any>;
  cultural_notes: string[];
  language_used: string;
  cultural_region_used: string;
  content_quality_score: number;
  cultural_appropriateness_score: number;
}

export interface ContentGenerationResponse {
  id: number;
  analysis_id: number;
  content_type: string;
  generated_text: string;
  status: string;
  tone?: string;
  target_audience?: string;
  platform?: string;
  word_count?: number;
  quality_score?: number;
  created_at: string;
  completed_at?: string;
}

export interface AnalysisResult {
  id: number;
  product_id: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  total_reviews_processed: number;
  overall_sentiment?: string;
  key_insights?: string[];
  pain_points?: string[];
  benefits?: string[];
  error_message?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  review_insights?: Array<{
    id: number;
    review_text: string;
    sentiment?: string;
    insights?: string[];
    created_at: string;
  }>;
}

/**
 * Get authentication token from localStorage
 */
function getAuthToken(): string | null {
  return localStorage.getItem('auth_token');
}

/**
 * Set authentication token in localStorage
 */
export function setAuthToken(token: string): void {
  localStorage.setItem('auth_token', token);
}

/**
 * Remove authentication token from localStorage
 */
export function removeAuthToken(): void {
  localStorage.removeItem('auth_token');
}

/**
 * Create headers for API requests
 */
function createHeaders(includeAuth: boolean = false): HeadersInit {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  if (includeAuth) {
    const token = getAuthToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  return headers;
}

/**
 * Make API request with error handling
 */
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  try {
    const url = `${API_BASE_URL}${endpoint}`;
    
    // Debug logging
    console.log('API Request:', {
      url,
      method: options.method || 'GET',
      apiBaseUrl: API_BASE_URL,
      windowLocation: window.location.href
    });
    
    const response = await fetch(url, {
      ...options,
      headers: {
        ...createHeaders(false), // Temporarily disable auth for testing
        ...options.headers,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    
    return {
      success: true,
      data,
    };
  } catch (error) {
    console.error('API request failed:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
    };
  }
}

/**
 * API methods
 */
export const api = {
  // Product Analysis
  products: {
    async analyzeProduct(request: ProductAnalysisRequest): Promise<ApiResponse<ProductAnalysisResponse>> {
      return apiRequest(API_ENDPOINTS.PRODUCTS.ANALYZE, {
        method: 'POST',
        body: JSON.stringify(request),
      });
    },

    async getProducts() {
      return apiRequest(API_ENDPOINTS.PRODUCTS.LIST);
    },

    async getProduct(id: number) {
      return apiRequest(API_ENDPOINTS.PRODUCTS.DETAIL(id));
    },

    async validateUrl(url: string) {
      return apiRequest(`${API_ENDPOINTS.PRODUCTS.VALIDATE}?url=${encodeURIComponent(url)}`);
    },

    async getStats() {
      return apiRequest(API_ENDPOINTS.PRODUCTS.STATS);
    },
  },

  // Analysis
  analysis: {
    async getAnalysisStatus(analysisId: number): Promise<ApiResponse<AnalysisResult>> {
      return apiRequest(API_ENDPOINTS.ANALYSIS.STATUS(analysisId));
    },

    async getAnalysisResults(analysisId: number): Promise<ApiResponse<AnalysisResult>> {
      return apiRequest(API_ENDPOINTS.ANALYSIS.RESULTS(analysisId));
    },
  },

  // Content Generation
  generation: {
    async generateContent(request: {
      analysis_id: number;
      content_type: string;
      tone?: string;
      target_audience?: string;
      platform?: string;
    }): Promise<ApiResponse<ContentGenerationResponse>> {
      return apiRequest(API_ENDPOINTS.GENERATION.GENERATE, {
        method: 'POST',
        body: JSON.stringify(request),
      });
    },

    async generateIntelligentContent(request: IntelligentContentRequest): Promise<ApiResponse<IntelligentContentResponse>> {
      return apiRequest(API_ENDPOINTS.GENERATION.INTELLIGENT, {
        method: 'POST',
        body: JSON.stringify(request),
      });
    },

    async getGenerationHistory(userId?: string, limit: number = 50) {
      const params = new URLSearchParams();
      if (userId) params.append('user_id', userId);
      params.append('limit', limit.toString());
      
      return apiRequest(`${API_ENDPOINTS.GENERATION.HISTORY}?${params.toString()}`);
    },

    async provideFeedback(generationId: number, rating: number, feedback?: string) {
      return apiRequest(API_ENDPOINTS.GENERATION.FEEDBACK, {
        method: 'POST',
        body: JSON.stringify({
          generation_id: generationId,
          user_rating: rating,
          user_feedback: feedback,
        }),
      });
    },

    async getSystemStatus() {
      return apiRequest(API_ENDPOINTS.GENERATION.STATUS);
    },

    async getTemplates(templateType?: string, activeOnly: boolean = true) {
      const params = new URLSearchParams();
      if (templateType) params.append('template_type', templateType);
      params.append('active_only', activeOnly.toString());
      
      return apiRequest(`${API_ENDPOINTS.GENERATION.TEMPLATES}?${params.toString()}`);
    },
  },

  // Campaigns
  campaigns: {
    async createCampaign(request: {
      name: string;
      description?: string;
    }) {
      return apiRequest<any>(`${API_ENDPOINTS.CAMPAIGNS.CREATE}`, {
        method: 'POST',
        body: JSON.stringify(request),
      });
    },

    async addContentToCampaign(campaignId: number, content: {
      content_type: string;
      title?: string;
      content: string;
      parameters?: Record<string, any>;
      language?: string;
    }) {
      return apiRequest<any>(`/api/${API_VERSION}/campaigns/${campaignId}/content`, {
        method: 'POST',
        body: JSON.stringify(content),
      });
    },

    async getCampaigns() {
      return apiRequest(API_ENDPOINTS.CAMPAIGNS.LIST);
    },

    async getCampaign(id: number) {
      return apiRequest(API_ENDPOINTS.CAMPAIGNS.DETAIL(id));
    },
  },
};

export function isAuthenticated(): boolean {
  return !!getAuthToken();
}

export function handleApiError(error: any): string {
  if (typeof error === 'string') {
    return error;
  }
  if (error?.message) {
    return error.message;
  }
  return 'An unexpected error occurred';
} 