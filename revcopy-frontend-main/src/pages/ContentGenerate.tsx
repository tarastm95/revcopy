import React, { useState, useEffect } from 'react';
import Sidebar from '../components/Sidebar';
import ProductInsights from '../components/content-generate/ProductInsights';
import ContentTypeSelector from '../components/content-generate/ContentTypeSelector';
import CustomizationPanel from '../components/content-generate/CustomizationPanel';
import { Copy, Loader2, RefreshCw, Settings, FileText } from 'lucide-react';
import { api, handleApiError, type ProductAnalysisResponse } from '../lib/api';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';
import './ContentGenerate.css';

interface AnalysisData {
  product: ProductAnalysisResponse;
  analysisId?: number;
  url: string;
}

interface RealAnalysisData {
  benefits?: string[];
  pain_points?: string[];
  key_insights?: string[];
  overall_sentiment?: string;
  total_reviews_processed?: number;
}

interface ContentVersion {
  id: number;
  title: string;
  content: string;
  style: string;
}

const ContentGenerate = () => {
  const [selectedType, setSelectedType] = useState('facebook_ad');
  const [selectedText, setSelectedText] = useState('');
  const [selectedRange, setSelectedRange] = useState<Range | null>(null);
  const [showTextDropdown, setShowTextDropdown] = useState(false);
  const [showParameterControls, setShowParameterControls] = useState(false);
  const [popupPosition, setPopupPosition] = useState({ top: 0, left: 0 });
  const [isRegeneratingSelection, setIsRegeneratingSelection] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [selectionParameters, setSelectionParameters] = useState({
    style: 'professional',
    tone: 'friendly',
    length: 'same'
  });
  const [customization, setCustomization] = useState({
    style: 'professional',
    length: 'medium',
    language: 'en',
    tone: 'friendly',
    audience: 'general',
    urgency: 'medium',
    output: 'single'
  });
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);
  const [realAnalysisData, setRealAnalysisData] = useState<RealAnalysisData | null>(null);
  
  // Updated state for multiple content versions
  const [contentVersions, setContentVersions] = useState<ContentVersion[]>([]);
  const [currentVersionIndex, setCurrentVersionIndex] = useState(0);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [isLoadingAnalysis, setIsLoadingAnalysis] = useState(false);
  
  const navigate = useNavigate();

  // Map frontend content types to backend format
  const mapContentType = (frontendType: string): string => {
    const typeMap: Record<string, string> = {
      'facebook_ad': 'facebook_ad',
      'video_ad_script': 'product_description', // Video scripts use product description template
      'google_ad': 'google_ad',
      'instagram_caption': 'instagram_caption',
      'blog_article': 'blog_article',
      'product_description': 'product_description',
      'upsell_crosssell': 'product_comparison',
      'faqs': 'faq',
      'abandoned_cart_email': 'email_campaign',
      'newsletter_email': 'email_campaign',
      'flash_sales_email': 'email_campaign',
      'back_in_stock_email': 'email_campaign',
      'customer_avatars': 'product_description',
      'pain_benefit_points': 'product_description',
      'swot_analysis': 'product_comparison',
      'seasonal_strategies': 'product_description'
    };
    
    return typeMap[frontendType] || 'product_description';
  };

  // Map frontend tone to backend format
  const mapTone = (frontendTone: string): string => {
    const toneMap: Record<string, string> = {
      'storytelling': 'emotional',
      'attention-grabbing': 'authoritative',
      'feature-focused': 'professional',
      'friendly': 'friendly',
      'scarcity': 'authoritative',
      'special-promotion': 'emotional',
      'funny': 'playful',
      'controversial': 'authoritative',
      'before-after': 'professional',
      'problem-solution': 'professional',
      'mix-5-styles': 'friendly',
      'professional': 'professional',
      'casual': 'casual',
      'luxury': 'luxurious',
      'authoritative': 'authoritative',
      'emotional': 'emotional',
      'minimal': 'minimalist',
      'playful': 'playful'
    };
    
    return toneMap[frontendTone] || 'professional';
  };

  // Map frontend language to backend ISO code
  const mapLanguage = (frontendLanguage: string): string => {
    const languageMap: Record<string, string> = {
      'english': 'en',
      'spanish': 'es',
      'french': 'fr',
      'chinese': 'zh',
      'hindi': 'hi',
      'japanese': 'ja',
      'german': 'de',
      'swahili': 'sw',
      'pidgin': 'en', // Fallback to English for pidgin
      'en': 'en',
      'es': 'es',
      'fr': 'fr',
      'he': 'he'
    };
    
    return languageMap[frontendLanguage] || 'en';
  };

  // Map frontend length to backend max_tokens
  const mapLength = (frontendLength: string): number => {
    const lengthMap: Record<string, number> = {
      'short': 300,
      'medium': 800,
      'long': 1500
    };
    
    return lengthMap[frontendLength] || 800;
  };

  useEffect(() => {
    // Load analysis data from localStorage
    const storedAnalysis = localStorage.getItem('currentAnalysis');
    if (storedAnalysis) {
      try {
        const data = JSON.parse(storedAnalysis) as AnalysisData;
        setAnalysisData(data);
        
        // Fetch real analysis data from backend if we have an analysis ID
        if (data.analysisId) {
          fetchAnalysisData(data.analysisId);
        }
        
        // Auto-generate initial content
        generateContent(data);
      } catch (error) {
        console.error('Failed to parse stored analysis:', error);
        toast.error('Failed to load analysis data');
        navigate('/');
      }
    } else {
      toast.error('No analysis data found. Please start from the homepage.');
      navigate('/');
    }
  }, [navigate]);

  /**
   * Fetch real analysis data from backend API
   */
  const fetchAnalysisData = async (analysisId: number) => {
    try {
      setIsLoadingAnalysis(true);
      console.log('Fetching analysis data:', analysisId);
      
      const response = await api.analysis.getAnalysisResults(analysisId);
      
      if (response.success && response.data) {
        const analysisResult = response.data;
        console.log('Raw analysis result:', analysisResult);
        
        // Extract data from nested structure
        const results = analysisResult.results || {};
        const metadata = analysisResult.metadata || {};
        const sentimentAnalysis = results.sentiment_analysis || {};
        
        setRealAnalysisData({
          benefits: results.key_insights || [],
          pain_points: results.pain_points || [],
          key_insights: results.key_insights || [],
          overall_sentiment: sentimentAnalysis.overall_sentiment || 'neutral',
          total_reviews_processed: metadata.reviews_analyzed || 0
        });
        
        console.log('Analysis data loaded successfully:', results);
      } else {
        console.warn('No analysis data available:', response.error);
        // Don't show error toast, just continue without analysis data
      }
    } catch (error) {
      console.error('Failed to fetch analysis data:', error);
      // Don't show error toast, just continue without analysis data
    } finally {
      setIsLoadingAnalysis(false);
    }
  };

  /**
   * Generate content based on user selections and prompt configuration
   */
  const generateContent = async (data?: AnalysisData, regenerate: boolean = false) => {
    if (!data && !analysisData) {
      toast.error('No analysis data available');
      return;
    }

    const targetData = data || analysisData;
    if (!targetData) return;

    try {
      setIsGenerating(true);
      
      // Clear existing versions if regenerating
      if (regenerate) {
        setContentVersions([]);
        setCurrentVersionIndex(0);
      }

      console.log('Starting content generation with user selections:', {
        selectedType,
        customization,
        selectionParameters
      });
      
      // Build comprehensive custom_variables with ALL product data from crawler
      const custom_variables = {
        // User selection parameters (4 modular prompts)
        style: customization.style || 'professional',
        length: customization.length || 'medium',
        language: customization.language || 'en',
        
        // Product information from crawler
        product_name: targetData.product.title || 'the product',
        product_description: targetData.product.description || '',
        brand: targetData.product.brand || '',
        price: targetData.product.price ? `$${targetData.product.price}` : '',
        category: targetData.product.category || '',
        platform: targetData.product.platform || '',
        
        // Reviews and ratings from crawler
        average_rating: targetData.product.rating || 0,
        review_count: targetData.product.review_count || 0,
        
        // Analysis insights from backend (if available)
        positive_reviews: realAnalysisData?.benefits || [],
        negative_reviews: realAnalysisData?.pain_points || [],
        key_insights: realAnalysisData?.key_insights || [],
        overall_sentiment: realAnalysisData?.overall_sentiment || 'positive',
        
        // Additional product details
        in_stock: targetData.product.in_stock,
        tags: targetData.product.tags || [],
        crawl_metadata: targetData.product.crawl_metadata || {},
        
        // Generation parameters
        temperature: 0.7,
        max_tokens: mapLength(customization.length),
        personalization_level: 'standard'
      };
      
      console.log('📦 Comprehensive product data being sent:', {
        product_name: custom_variables.product_name,
        positive_reviews: custom_variables.positive_reviews,
        negative_reviews: custom_variables.negative_reviews,
        style: custom_variables.style,
        length: custom_variables.length,
        language: custom_variables.language
      });
      
      // Generate single version based on user's actual selections
      const requestPayload = {
        product_url: targetData.url,
        content_type: mapContentType(selectedType),
        language: mapLanguage(customization.language),
        cultural_region: mapLanguage(customization.language) === 'he' ? 'middle_east' : 'north_america',
        target_audience: customization.audience || 'general',
        tone: mapTone(customization.tone),
        urgency_level: customization.urgency || 'medium',
        brand_personality: targetData.product.brand || undefined,
        price_range: targetData.product.price ? (targetData.product.price > 100 ? 'premium' : 'affordable') : undefined,
        product_category: targetData.product.category || undefined,
        custom_variables: custom_variables  // Send ALL product data
      };

      console.log('🚀 Generating content with comprehensive payload:', requestPayload);

      const response = await api.generation.generateIntelligentContent(requestPayload);
      
      if (response.success && response.data) {
        const newVersion: ContentVersion = {
          id: Date.now(),
          title: `${selectedType} Content`,
          content: response.data.content,
          style: customization.style || 'professional'
        };
        
        setContentVersions([newVersion]);
        setCurrentVersionIndex(0);
        toast.success('Content generated successfully!');
        console.log('✅ Content generated successfully with full product data');
      } else {
        console.error('Failed to generate content:', response.error);
        throw new Error(response.error || 'Failed to generate content');
      }

    } catch (error) {
      console.error('Content generation failed:', error);
      const errorMessage = handleApiError(error);
      toast.error(`Content generation failed: ${errorMessage}`);
    } finally {
      setIsGenerating(false);
    }
  };

  /**
   * Handle regenerating all content versions
   */
  const handleRegenerateContent = () => {
    if (!analysisData) {
      toast.error('No analysis data available');
      return;
    }
    generateContent(analysisData, true);
  };

  /**
   * Generate 3 additional versions without clearing existing ones
   */
  const generateMoreVersions = async () => {
    if (!analysisData) {
      toast.error('No analysis data available');
      return;
    }

    try {
      setIsGenerating(true);
      
      // Generate a single additional version using current selections with slight variation
      const currentCount = contentVersions.length;
      
      const requestPayload = {
        product_url: analysisData.url,
        content_type: mapContentType(selectedType),
        language: mapLanguage(customization.language),
        cultural_region: mapLanguage(customization.language) === 'he' ? 'middle_east' : 'north_america',
        target_audience: customization.audience || 'general',
        tone: mapTone(customization.tone),
        urgency_level: customization.urgency || 'medium',
        brand_personality: analysisData.product.brand || undefined,
        price_range: analysisData.product.price ? (analysisData.product.price > 100 ? 'premium' : 'affordable') : undefined,
        product_category: analysisData.product.category || undefined,
        custom_variables: {
          style: customization.style || 'professional',
          temperature: 0.8, // Slightly higher for variation
          max_tokens: mapLength(customization.length),
          personalization_level: 'standard'
        }
      };

      const response = await api.generation.generateIntelligentContent(requestPayload);
      
      if (response.success && response.data) {
        const newVersion: ContentVersion = {
          id: Date.now() + currentCount,
          title: `${selectedType} Content (Version ${currentCount + 1})`,
          content: response.data.content,
          style: customization.style || 'professional'
        };
        
        setContentVersions(prev => [...prev, newVersion]);
        toast.success('Generated additional version!');
      } else {
        throw new Error(response.error || 'Failed to generate additional version');
      }

    } catch (error) {
      console.error('Additional content generation failed:', error);
      const errorMessage = handleApiError(error);
      toast.error(`Failed to generate additional version: ${errorMessage}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const regenerateSelectedText = async () => {
    if (!selectedText || !analysisData || !selectedRange) {
      toast.error('No text selected for regeneration');
      return;
    }

    setIsRegeneratingSelection(true);

    try {
      // Create a prompt for regenerating the specific text with new parameters
      const regenerationPrompt = `
        Rewrite this text: "${selectedText}"
        
        With these parameters:
        - Style: ${selectionParameters.style}
        - Tone: ${selectionParameters.tone}
        - Length: ${selectionParameters.length === 'shorter' ? 'make it shorter' : selectionParameters.length === 'longer' ? 'make it longer' : 'keep same length'}
        
        Product context: ${analysisData.product.title}
        Content type: ${selectedType}
        
        Return only the rewritten text, no explanations.
      `;

      const response = await api.generation.generateIntelligentContent({
        product_url: analysisData.url,
        content_type: mapContentType(selectedType),
        language: mapLanguage(customization.language),
        cultural_region: mapLanguage(customization.language) === 'he' ? 'middle_east' : 'north_america',
        target_audience: 'general',
        tone: selectionParameters.tone,
        urgency_level: 'medium',
        brand_personality: analysisData.product.brand || undefined,
        price_range: analysisData.product.price ? (analysisData.product.price > 100 ? 'premium' : 'affordable') : undefined,
        product_category: analysisData.product.category || undefined,
        custom_variables: { 
          regeneration_prompt: regenerationPrompt,
          style: selectionParameters.style,
          temperature: 0.7,
          max_tokens: mapLength(selectionParameters.length),
          personalization_level: 'standard'
        }
      });
      
      if (response.success && response.data) {
        // Replace the selected text with the new generated content
        const newContent = response.data.content.trim();
        const currentContent = contentVersions[currentVersionIndex].content;
        const updatedContent = currentContent.replace(selectedText, newContent);
        
        // Update the current version content
        setContentVersions(prevVersions => prevVersions.map((version, index) =>
          index === currentVersionIndex ? { ...version, content: updatedContent } : version
        ));
        toast.success('Text regenerated successfully!');
        
        // Clear selection
        setShowTextDropdown(false);
        setShowParameterControls(false);
        setSelectedText('');
        setSelectedRange(null);
        
        // Clear browser selection
        window.getSelection()?.removeAllRanges();
      } else {
        throw new Error(response.error || 'Failed to regenerate text');
      }
    } catch (error) {
      console.error('Text regeneration failed:', error);
      const errorMessage = handleApiError(error);
      toast.error(`Regeneration failed: ${errorMessage}`);
    } finally {
      setIsRegeneratingSelection(false);
    }
  };

  const handleTypeChange = (newType: string) => {
    setSelectedType(newType);
    // Auto-regenerate content when type changes
    if (analysisData && contentVersions.length > 0) {
      setTimeout(() => generateContent(undefined, true), 100);
    }
  };

  const handleTextSelection = () => {
    const selection = window.getSelection();
    if (selection && selection.toString().trim()) {
      const selectedText = selection.toString().trim();
      const range = selection.getRangeAt(0);
      const rect = range.getBoundingClientRect();
      
      setSelectedText(selectedText);
      setSelectedRange(range);
      setPopupPosition({
        top: rect.bottom + window.scrollY + 10,
        left: Math.max(10, rect.left + window.scrollX - 150)
      });
      setShowTextDropdown(true);
    }
  };

  const handleCustomizationChange = (field: keyof typeof customization, value: string) => {
    setCustomization(prev => ({ ...prev, [field]: value }));
    
    // Auto-regenerate when certain fields change
    if (['style', 'language'].includes(field) && analysisData && contentVersions.length > 0) {
      setTimeout(() => generateContent(undefined, true), 500);
    }
  };

  const handleSelectionParameterChange = (field: keyof typeof selectionParameters, value: string) => {
    setSelectionParameters(prev => ({ ...prev, [field]: value }));
  };

  const copyToClipboard = async (text: string) => {
    if (!text) {
      toast.error('No content to copy');
      return;
    }

    try {
      // Try to save to campaign first
      const campaignData = {
        title: `${analysisData?.product.title || 'Product'} - ${selectedType}`,
        content: text,
        content_type: selectedType,
        product_url: analysisData?.url || '',
        metadata: {
          generated_at: new Date().toISOString(),
          customization: customization,
          version: contentVersions[currentVersionIndex]?.title || 'Current Version'
        }
      };

      const response = await api.campaigns.createCampaign(campaignData);
      
      if (response.success) {
        toast.success('Content saved to campaigns!');
      } else {
        throw new Error(response.error || 'Failed to save campaign');
      }
      
      // Also copy to clipboard as backup
      await navigator.clipboard.writeText(text);
    } catch (error) {
      console.error('Failed to save to campaign:', error);
      const errorMessage = handleApiError(error);
      toast.error(`Failed to save: ${errorMessage}`);
      
      // Fallback to just copying to clipboard
      try {
        await navigator.clipboard.writeText(text);
        toast.info('Content copied to clipboard instead');
      } catch (clipboardError) {
        toast.error('Failed to copy to clipboard');
      }
    }
  };

  const copyAllVersions = async () => {
    if (contentVersions.length === 0) {
      toast.error('No content to copy');
      return;
    }

    const allContent = contentVersions.map((version, index) => 
      `=== ${version.title} (${version.style}) ===\n\n${version.content}`
    ).join('\n\n' + '='.repeat(50) + '\n\n');

    try {
      await navigator.clipboard.writeText(allContent);
      toast.success('All versions copied to clipboard!');
    } catch (error) {
      toast.error('Failed to copy all versions');
    }
  };

  const textOptions = [
    { value: 'customize', label: 'Customize & Regenerate', icon: '⚙️' },
    { value: 'improve-writing', label: 'Improve writing', icon: '≡' },
    { value: 'change-tone', label: 'Change tone', icon: '📈' },
    { value: 'make-longer', label: 'Make longer', icon: '≡' },
    { value: 'make-shorter', label: 'Make shorter', icon: '≡' },
    { value: 'repurpose-content', label: 'Repurpose content', icon: '↗' }
  ];

  // Close popup when clicking outside
  React.useEffect(() => {
    const handleClickOutside = () => {
      setShowTextDropdown(false);
      setShowParameterControls(false);
    };
    
    if (showTextDropdown || showParameterControls) {
      document.addEventListener('click', handleClickOutside);
    }
    
    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  }, [showTextDropdown, showParameterControls]);

  return (
    <div className="app-container">
      <Sidebar />
      
      <main className="main-content-wrapper">
        <div className="content-panel insights-panel">
          <ProductInsights 
            productData={analysisData?.product} 
            analysisData={realAnalysisData || undefined}
          />
          
          <div className="content-type-selector-wrapper">
            <h2 className="header">Choose Content Type</h2>
            <ContentTypeSelector
              selectedType={selectedType}
              onTypeSelect={handleTypeChange}
            />
          </div>
        </div>
        
        <div className="editor-card">
          <div className="customization-panel-wrapper">
            <CustomizationPanel
              customization={customization}
              onCustomizationChange={handleCustomizationChange}
            />
          </div>
          
          <div className="content-body-wrapper">
            <div className="content-block" onMouseUp={handleTextSelection}>
              {isGenerating ? (
                <div className="loading-content">
                  <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
                  <h3>Generating your content...</h3>
                  <p>This may take a few moments while we analyze your product.</p>
                </div>
              ) : contentVersions.length > 0 ? (
                <div className="content-versions-simple">
                  {contentVersions.map((version, index) => (
                    <div key={version.id} className="version-block">
                      <div className="version-header">
                        <h4 className="version-title">{version.title}</h4>
                        <span className="version-style">({version.style})</span>
                      </div>
                      <div 
                        className="generated-text"
                        dangerouslySetInnerHTML={{ 
                          __html: version.content
                            .replace(/\n\n/g, '<p>')
                            .replace(/\n/g, '<br/>')
                            .replace(/\*\*(.*?)\*\*/g, '<h3>$1</h3>')
                        }}
                      />
                      {index < contentVersions.length - 1 && (
                        <div className="version-separator"></div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="no-content">
                  <h3>No content generated yet</h3>
                  <p>Your generated content will appear here.</p>
                </div>
              )}
            </div>
            
            <div className="content-actions-sticky">
              <div className="action-buttons-simple">
                <button 
                  className="action-btn secondary" 
                  onClick={handleRegenerateContent}
                  disabled={isGenerating}
                >
                  {isGenerating ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <RefreshCw className="w-4 h-4" />
                  )}
                  {isGenerating ? 'Generating...' : 'Regenerate 3 Versions'}
                </button>
                
                <button 
                  className="action-btn secondary" 
                  onClick={generateMoreVersions}
                  disabled={isGenerating || contentVersions.length === 0}
                >
                  <FileText className="w-4 h-4" />
                  +3 More
                </button>
                
                <button 
                  className="action-btn primary" 
                  onClick={copyAllVersions}
                  disabled={contentVersions.length === 0 || isGenerating}
                >
                  <Copy className="w-4 h-4" />
                  Copy All Versions
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Enhanced popup for text selection */}
      {showTextDropdown && selectedText && (
        <div 
          className="text-selection-popup enhanced"
          style={{
            position: 'fixed',
            top: `${popupPosition.top}px`,
            left: `${popupPosition.left}px`,
            zIndex: 1000
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <div className="popup-header">
            <span>✨ Edit selected text</span>
            <span className="selected-preview">"{selectedText.substring(0, 50)}..."</span>
          </div>
          
          {!showParameterControls ? (
            <div className="popup-menu">
              <button
                className="popup-item primary"
                onClick={() => setShowParameterControls(true)}
              >
                <span className="item-icon">⚙️</span>
                <span>Customize & Regenerate</span>
                <span className="item-arrow">❯</span>
              </button>
              {textOptions.slice(1).map((option) => (
                <button
                  key={option.value}
                  className="popup-item"
                  onClick={() => {
                    if (option.value === 'make-longer') {
                      setSelectionParameters(prev => ({ ...prev, length: 'longer' }));
                      regenerateSelectedText();
                    } else if (option.value === 'make-shorter') {
                      setSelectionParameters(prev => ({ ...prev, length: 'shorter' }));
                      regenerateSelectedText();
                    } else {
                      toast.info(`${option.label} feature coming soon!`);
                    }
                    setShowTextDropdown(false);
                  }}
                >
                  <span className="item-icon">{option.icon}</span>
                  <span>{option.label}</span>
                  <span className="item-arrow">❯</span>
                </button>
              ))}
            </div>
          ) : (
            <div className="parameter-controls">
              <div className="parameter-grid">
                <div className="parameter-group">
                  <label>Style</label>
                  <select 
                    value={selectionParameters.style}
                    onChange={(e) => handleSelectionParameterChange('style', e.target.value)}
                  >
                    <option value="professional">Professional</option>
                    <option value="casual">Casual</option>
                    <option value="emotional">Emotional</option>
                    <option value="authoritative">Authoritative</option>
                    <option value="playful">Playful</option>
                  </select>
                </div>
                
                <div className="parameter-group">
                  <label>Tone</label>
                  <select 
                    value={selectionParameters.tone}
                    onChange={(e) => handleSelectionParameterChange('tone', e.target.value)}
                  >
                    <option value="friendly">Friendly</option>
                    <option value="professional">Professional</option>
                    <option value="exciting">Exciting</option>
                    <option value="urgent">Urgent</option>
                    <option value="calm">Calm</option>
                  </select>
                </div>
                
                <div className="parameter-group">
                  <label>Length</label>
                  <select 
                    value={selectionParameters.length}
                    onChange={(e) => handleSelectionParameterChange('length', e.target.value)}
                  >
                    <option value="shorter">Shorter</option>
                    <option value="same">Same Length</option>
                    <option value="longer">Longer</option>
                  </select>
                </div>
              </div>
              
              <div className="parameter-actions">
                <button 
                  className="param-btn secondary"
                  onClick={() => setShowParameterControls(false)}
                >
                  Back
                </button>
                <button 
                  className="param-btn primary"
                  onClick={regenerateSelectedText}
                  disabled={isRegeneratingSelection}
                >
                  {isRegeneratingSelection ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Regenerating...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="w-4 h-4" />
                      Regenerate
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ContentGenerate;
