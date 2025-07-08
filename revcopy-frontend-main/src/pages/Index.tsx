import Sidebar from '../components/Sidebar';
import { useState, useEffect } from 'react';
import { Search, Plus, Sparkles, FileText, Share2, PenTool, BarChart3, Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { api, handleApiError } from '../lib/api';
import { toast } from 'sonner';

const Index = () => {
  const [url, setUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleAnalyze = async () => {
    if (!url.trim()) {
      toast.error('Please enter a product URL');
      return;
    }

    // Basic URL validation
    try {
      new URL(url);
    } catch {
      toast.error('Please enter a valid URL');
      return;
    }

    setIsLoading(true);

    try {
      // Call the backend API to analyze the product
      console.log('Analyzing product:', url);
      const response = await api.products.analyzeProduct({
        url: url.trim(),
        analysis_type: 'full_analysis',
        max_reviews: 50
      });

      if (response.success && response.data) {
        toast.success('Product analysis started successfully!');
        
        // Store the analysis result in localStorage for the content generation page
        localStorage.setItem('currentAnalysis', JSON.stringify({
          product: response.data,
          analysisId: response.data.analysis_id,
          url: url.trim()
        }));
        
        // Navigate to content generation page
        navigate('/content-generate');
      } else {
        throw new Error(response.error || 'Failed to analyze product');
      }
    } catch (error) {
      console.error('Product analysis failed:', error);
      const errorMessage = handleApiError(error);
      toast.error(`Analysis failed: ${errorMessage}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Real campaigns state
  const [recentContent, setRecentContent] = useState([]);
  const [isLoadingCampaigns, setIsLoadingCampaigns] = useState(true);

  const contentTypes = [
    { icon: FileText, label: 'General Content', active: true },
    { icon: Share2, label: 'Social Content' },
    { icon: PenTool, label: 'Blog Content' },
    { icon: BarChart3, label: 'Marketing Content' }
  ];

  // Load real campaigns on component mount
  useEffect(() => {
    const loadCampaigns = async () => {
      try {
        setIsLoadingCampaigns(true);
        const response = await api.campaigns.getCampaigns();
        
        if (response.success && response.data) {
          // Transform campaigns to content format for display
          const contentItems = [];
          
          response.data.forEach((campaign: any) => {
            campaign.content?.forEach((content: any, index: number) => {
              contentItems.push({
                id: `${campaign.id}-${content.id}`,
                name: content.title || `${content.content_type.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}`,
                campaign: campaign.name,
                date: new Date(campaign.created_at).toLocaleDateString('en-GB', {
                  day: '2-digit',
                  month: '2-digit',
                  year: 'numeric'
                }),
                modified: getRelativeTime(content.created_at),
                status: content.status === 'completed' ? 'Completed' : 'In Progress',
                image: null, // No images for now
                content: content.content,
                contentType: content.content_type,
                language: content.language || 'en'
              });
            });
          });
          
          setRecentContent(contentItems.slice(0, 10)); // Show latest 10 items
        } else {
          setRecentContent([]);
        }
      } catch (error) {
        console.error('Failed to load campaigns:', error);
        setRecentContent([]);
      } finally {
        setIsLoadingCampaigns(false);
      }
    };

    loadCampaigns();
  }, []);

  // Helper function to get relative time
  const getRelativeTime = (dateString: string) => {
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      
      const diffMinutes = Math.floor(diffMs / (1000 * 60));
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
      const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
      
      if (diffMinutes < 60) {
        return `${diffMinutes} minute${diffMinutes === 1 ? '' : 's'} ago`;
      } else if (diffHours < 24) {
        return `${diffHours} hour${diffHours === 1 ? '' : 's'} ago`;
      } else if (diffDays < 30) {
        return `${diffDays} day${diffDays === 1 ? '' : 's'} ago`;
      } else {
        return date.toLocaleDateString();
      }
    } catch {
      return 'Recently';
    }
  };

  return (
    <div className="modern-app-container">
      <Sidebar />
      
      <main className="modern-main-content">
        {/* Top Header */}
        <header className="modern-header">
          <div className="header-left">
            <h1 className="page-title">Content Generate</h1>
            <p className="page-subtitle">Crafts high-quality, tailored content in an instant.</p>
          </div>
          <div className="header-right">
            <div className="search-container">
              <Search className="search-icon" />
              <input 
                type="text" 
                placeholder="Search..." 
                className="search-input"
              />
              <span className="search-shortcut">⌘F</span>
            </div>
            <button className="create-btn">
              <Plus className="w-4 h-4" />
              Create Content
            </button>
          </div>
        </header>

        {/* Main Content Area */}
        <div className="content-creation-section">
          <div className="creation-card">
            <h2 className="creation-title">Insert a product URL to generate RevCopy</h2>
            <p className="creation-tip">Tip: Works with any product URL - we'll extract available reviews and product data to generate content</p>
            
            <div className="url-input-container">
              <input 
                type="text" 
                placeholder="Paste your product URL here (Shopify/Amazon/eBay/AliExpress)..."
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="creation-input"
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleAnalyze();
                  }
                }}
              />
              <button 
                className="generate-button"
                onClick={handleAnalyze}
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <div className="loading-spinner"></div>
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Search className="w-5 h-5" />
                    Analyze Reviews
                  </>
                )}
              </button>
            </div>

            {/* Platform Icons */}
            <div className="supported-platforms">
              <span className="platform-label">Supported Platforms:</span>
              <div className="platform-icons">
                <div className="platform-item">
                  <svg className="platform-icon" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M13.582 8.182C11.934 8.062 9.78 8.014 8.238 8.566c-.8.287-1.488.713-2.061 1.357-.573.645-.859 1.39-.859 2.235 0 .688.168 1.286.504 1.794.336.508.8.915 1.392 1.221.592.306 1.277.459 2.055.459.645 0 1.221-.122 1.728-.367.507-.245.906-.588 1.196-1.029.29-.441.435-.952.435-1.533 0-.358-.061-.68-.184-.966-.123-.286-.296-.528-.52-.726-.224-.198-.488-.355-.792-.471-.304-.116-.636-.174-.996-.174-.41 0-.768.072-1.075.216-.307.144-.551.344-.732.6-.181.256-.272.55-.272.882 0 .235.041.447.123.636.082.189.196.338.342.447.146.109.317.164.513.164.155 0 .295-.031.42-.093.125-.062.226-.148.303-.258.077-.11.116-.235.116-.375 0-.119-.029-.226-.087-.322-.058-.096-.138-.171-.24-.225-.102-.054-.218-.081-.348-.081-.09 0-.171.016-.243.048-.072.032-.13.076-.174.132-.044.056-.066.121-.066.195 0 .058.015.11.045.156.03.046.071.083.123.111.052.028.111.042.177.042.048 0 .091-.008.129-.024.038-.016.069-.038.093-.066.024-.028.036-.06.036-.096 0-.032-.009-.061-.027-.087-.018-.026-.043-.047-.075-.063-.032-.016-.069-.024-.111-.024-.035 0-.066.006-.093.018-.027.012-.049.029-.066.051-.017.022-.026.047-.026.075 0 .025.007.047.021.066.014.019.033.034.057.045.024.011.051.017.081.017.025 0 .047-.004.066-.012.019-.008.034-.019.045-.033.011-.014.017-.03.017-.048 0-.015-.004-.029-.012-.042-.008-.013-.019-.023-.033-.03-.014-.007-.03-.011-.048-.011-.013 0-.025.002-.036.006-.011.004-.02.01-.027.018-.007.008-.011.017-.011.027 0 .008.002.015.006.021.004.006.01.011.018.015.008.004.017.006.027.006.007 0 .013-.001.018-.003.005-.002.009-.005.012-.009.003-.004.005-.009.005-.015z"/>
                  </svg>
                  <span>Amazon</span>
                </div>
                <div className="platform-item">
                  <svg className="platform-icon" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M7.021 12.111l-.881 2.842h-1.65L8.364 8.75h1.908l3.273 6.203h-1.713l-.881-2.842H7.021zm2.488-4.233l-.756 2.452h2.547l-.756-2.452-.756 1.887-.279-.887zm8.251.345c-.279-.156-.279-.468 0-.624.756-.468 1.368-.156 1.368.624v4.545c0 .78-.612 1.092-1.368.624-.279-.156-.279-.468 0-.624V8.223z"/>
                  </svg>
                  <span>eBay</span>
                </div>
                <div className="platform-item">
                  <svg className="platform-icon" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M1.714 5.143c0-1.577 1.281-2.857 2.857-2.857h14.857c1.577 0 2.857 1.28 2.857 2.857v13.714c0 1.577-1.28 2.857-2.857 2.857H4.571c-1.576 0-2.857-1.28-2.857-2.857V5.143zM12 6.857c-2.827 0-5.143 2.316-5.143 5.143S9.173 17.143 12 17.143s5.143-2.316 5.143-5.143S14.827 6.857 12 6.857z"/>
                  </svg>
                  <span>AliExpress</span>
                </div>
              </div>
            </div>

            {/* Content Type Categories */}
            <div className="content-types">
              {contentTypes.map((type, index) => (
                <button 
                  key={index}
                  className={`content-type-btn ${type.active ? 'active' : ''}`}
                >
                  <type.icon className="content-type-icon" />
                  {type.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Recent Content Section - Card Grid Style */}
        <div className="recent-content-section">
          <div className="section-header">
            <h3 className="section-title">My Latest Content ({recentContent.length})</h3>
            <div className="section-controls">
              <select className="filter-select">
                <option>All Campaign</option>
                <option>Design Marketing</option>
                <option>Social Media</option>
              </select>
              <select className="filter-select">
                <option>Status</option>
                <option>In Progress</option>
                <option>Completed</option>
                <option>In Review</option>
              </select>
            </div>
          </div>

          {isLoadingCampaigns ? (
            <div className="loading-state">
              <Loader2 className="loading-spinner-large" />
              <h3>Loading your content...</h3>
              <p>Please wait while we fetch your campaigns and content.</p>
            </div>
          ) : recentContent.length === 0 ? (
            <div className="empty-state">
              <FileText className="empty-icon" />
              <h3>No content yet</h3>
              <p>Start by analyzing a product URL above to generate your first content.</p>
              <p className="empty-tip">Your generated content will appear here and be saved to campaigns.</p>
            </div>
          ) : (
            <div className="content-cards-grid">
              {recentContent.map((item: any) => (
                <div key={item.id} className="content-card">
                  <div className="card-image content-placeholder">
                    <div className="content-preview">
                      <FileText className="content-icon" />
                      <span className="content-type">{item.contentType?.replace(/_/g, ' ')}</span>
                    </div>
                  </div>
                  <div className="card-content">
                    <div className="card-header">
                      <h4 className="card-title">{item.name}</h4>
                      <button className="card-menu">⋯</button>
                    </div>
                    <div className="card-campaign">{item.campaign}</div>
                    <div className="card-footer">
                      <div className="card-dates">
                        <div className="card-date">Created: {item.date}</div>
                        <div className="card-modified">Modified: {item.modified}</div>
                      </div>
                      <span className={`status-badge ${item.status.toLowerCase().replace(' ', '-')}`}>
                        {item.status}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
      
      <style>{`
        .modern-app-container {
          display: block;
          min-height: 100vh;
          background-color: #FDFDFD;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }

        .modern-main-content {
          margin-left: 256px;
          padding: 24px;
          gap: 24px;
          display: flex;
          flex-direction: column;
          transition: margin-left 0.3s ease;
        }

        /* When sidebar is collapsed, adjust main content margin */
        @media (min-width: 1024px) {
          .modern-main-content {
            margin-left: 256px;
          }
        }

        /* Header Styles */
        .modern-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 8px;
        }

        .header-left {
          flex: 1;
        }

        .page-title {
          font-size: 36px;
          font-weight: 700;
          color: #1F2937;
          margin: 0 0 8px 0;
          line-height: 1.2;
        }

        .page-subtitle {
          font-size: 16px;
          color: #6B7280;
          margin: 0;
          line-height: 1.4;
        }

        .header-right {
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .search-container {
          position: relative;
          display: flex;
          align-items: center;
        }

        .search-input {
          width: 280px;
          padding: 10px 12px 10px 40px;
          border: 1px solid #E5E7EB;
          border-radius: 8px;
          font-size: 14px;
          color: #374151;
          background-color: white;
          outline: none;
          transition: border-color 0.2s;
        }

        .search-input:focus {
          border-color: #7C3AED;
          box-shadow: 0 0 0 1px #7C3AED;
        }

        .search-icon {
          position: absolute;
          left: 12px;
          width: 16px;
          height: 16px;
          color: #9CA3AF;
          pointer-events: none;
        }

        .search-shortcut {
          position: absolute;
          right: 12px;
          font-size: 12px;
          color: #9CA3AF;
          pointer-events: none;
        }

        .create-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 16px;
          background-color: #7C3AED;
          color: white;
          border: none;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          transition: background-color 0.2s;
        }

        .create-btn:hover {
          background-color: #6D28D9;
        }

        /* Content Creation Section */
        .content-creation-section {
          background-color: white;
          border-radius: 16px;
          padding: 48px;
          text-align: center;
          border: 1px solid #F3F4F6;
        }

        .creation-title {
          font-size: 32px;
          font-weight: 700;
          color: #1F2937;
          margin: 0 0 12px 0;
          line-height: 1.3;
        }

        .creation-tip {
          font-size: 16px;
          color: #6B7280;
          margin: 0 0 32px 0;
          line-height: 1.4;
        }

        .url-input-container {
          display: flex;
          max-width: 600px;
          margin: 0 auto 32px auto;
          gap: 12px;
        }

        .creation-input {
          flex: 1;
          padding: 16px 20px;
          border: 1px solid #E5E7EB;
          border-radius: 12px;
          font-size: 16px;
          color: #374151;
          outline: none;
          transition: border-color 0.2s;
        }

        .creation-input:focus {
          border-color: #7C3AED;
          box-shadow: 0 0 0 1px #7C3AED;
        }

        .creation-input::placeholder {
          color: #9CA3AF;
        }

        .generate-button {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 16px 24px;
          background-color: #7C3AED;
          color: white;
          border: none;
          border-radius: 12px;
          font-size: 16px;
          font-weight: 600;
          cursor: pointer;
          transition: background-color 0.2s;
          min-width: 160px;
          justify-content: center;
        }

        .generate-button:hover:not(:disabled) {
          background-color: #6D28D9;
        }

        .generate-button:disabled {
          opacity: 0.7;
          cursor: not-allowed;
        }

        .loading-spinner {
          width: 20px;
          height: 20px;
          border: 2px solid rgba(255, 255, 255, 0.3);
          border-top: 2px solid white;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        /* Platform Icons */
        .supported-platforms {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 32px;
          margin-bottom: 32px;
        }

        .platform-label {
          font-size: 14px;
          color: #6B7280;
          font-weight: 500;
        }

        .platform-icons {
          display: flex;
          gap: 24px;
        }

        .platform-item {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
          padding: 12px;
          border-radius: 8px;
          transition: background-color 0.2s;
          cursor: pointer;
        }

        .platform-item:hover {
          background-color: #F9FAFB;
        }

        .platform-icon {
          width: 32px;
          height: 32px;
          color: #6B7280;
          transition: color 0.2s;
        }

        .platform-item:hover .platform-icon {
          color: #7C3AED;
        }

        .platform-item span {
          font-size: 12px;
          color: #6B7280;
          font-weight: 500;
        }

        /* Content Types */
        .content-types {
          display: flex;
          justify-content: center;
          gap: 16px;
          flex-wrap: wrap;
        }

        .content-type-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 20px;
          border: 1px solid #E5E7EB;
          border-radius: 12px;
          background-color: white;
          color: #6B7280;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s;
        }

        .content-type-btn:hover {
          border-color: #7C3AED;
          color: #7C3AED;
        }

        .content-type-btn.active {
          border-color: #7C3AED;
          background-color: #F3F4F6;
          color: #7C3AED;
        }

        .content-type-icon {
          width: 16px;
          height: 16px;
        }

        /* Recent Content Section */
        .recent-content-section {
          background-color: white;
          border-radius: 16px;
          border: 1px solid #F3F4F6;
          overflow: hidden;
          margin-bottom: 48px;
        }

        .section-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 24px 24px 16px 24px;
          border-bottom: 1px solid #F3F4F6;
        }

        .section-title {
          font-size: 18px;
          font-weight: 600;
          color: #1F2937;
          margin: 0;
        }

        .section-controls {
          display: flex;
          gap: 12px;
        }

        .filter-select {
          padding: 8px 12px;
          border: 1px solid #E5E7EB;
          border-radius: 8px;
          font-size: 14px;
          color: #374151;
          background-color: white;
          cursor: pointer;
          outline: none;
        }

        /* Loading and Empty States */
        .loading-state, .empty-state {
          padding: 60px 24px;
          text-align: center;
          color: #6B7280;
        }

        .loading-spinner-large {
          width: 40px;
          height: 40px;
          margin: 0 auto 16px auto;
          animation: spin 1s linear infinite;
          color: #7C3AED;
        }

        .empty-icon {
          width: 64px;
          height: 64px;
          margin: 0 auto 16px auto;
          color: #D1D5DB;
        }

        .loading-state h3, .empty-state h3 {
          font-size: 20px;
          font-weight: 600;
          color: #374151;
          margin: 0 0 8px 0;
        }

        .loading-state p, .empty-state p {
          font-size: 16px;
          color: #6B7280;
          margin: 0 0 8px 0;
          line-height: 1.5;
        }

        .empty-tip {
          font-size: 14px !important;
          color: #9CA3AF !important;
        }

        /* Card Grid Styles */
        .content-cards-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
          gap: 20px;
          padding: 24px;
        }

        .content-card {
          background-color: white;
          border: 1px solid #E5E7EB;
          border-radius: 12px;
          overflow: hidden;
          transition: all 0.2s;
          cursor: pointer;
        }

        .content-card:hover {
          border-color: #7C3AED;
          box-shadow: 0 4px 12px rgba(124, 58, 237, 0.1);
          transform: translateY(-2px);
        }

        .card-image {
          width: 100%;
          height: 160px;
          overflow: hidden;
          background-color: #F3F4F6;
        }

        .product-image {
          width: 100%;
          height: 100%;
          object-fit: cover;
          transition: transform 0.2s;
        }

        .content-card:hover .product-image {
          transform: scale(1.05);
        }

        .content-placeholder {
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 100%);
        }

        .content-preview {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
          color: #64748B;
        }

        .content-icon {
          width: 32px;
          height: 32px;
        }

        .content-type {
          font-size: 12px;
          font-weight: 600;
          text-transform: capitalize;
          background: #E2E8F0;
          padding: 4px 8px;
          border-radius: 4px;
          color: #475569;
        }

        .card-content {
          padding: 20px;
        }

        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 12px;
        }

        .card-title {
          font-size: 16px;
          font-weight: 600;
          color: #1F2937;
          margin: 0;
          line-height: 1.4;
          flex: 1;
          margin-right: 12px;
        }

        .card-menu {
          background: none;
          border: none;
          color: #9CA3AF;
          cursor: pointer;
          font-size: 16px;
          padding: 4px;
          border-radius: 4px;
          transition: all 0.2s;
          flex-shrink: 0;
        }

        .card-menu:hover {
          background-color: #F3F4F6;
          color: #6B7280;
        }

        .card-campaign {
          font-size: 14px;
          color: #6B7280;
          margin-bottom: 16px;
          font-weight: 500;
        }

        .card-footer {
          display: flex;
          justify-content: space-between;
          align-items: flex-end;
          gap: 12px;
        }

        .card-dates {
          flex: 1;
        }

        .card-date, .card-modified {
          font-size: 12px;
          color: #9CA3AF;
          line-height: 1.4;
        }

        .card-modified {
          margin-top: 2px;
        }

        .status-badge {
          padding: 4px 8px;
          border-radius: 6px;
          font-size: 12px;
          font-weight: 500;
          text-transform: capitalize;
          flex-shrink: 0;
        }

        .status-badge.in-progress {
          background-color: #FEF3C7;
          color: #92400E;
        }

        .status-badge.completed {
          background-color: #D1FAE5;
          color: #065F46;
        }

        .status-badge.in-review {
          background-color: #DBEAFE;
          color: #1E40AF;
        }
      `}</style>
    </div>
  );
};

export default Index;
