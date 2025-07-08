import React, { useState, useEffect } from 'react';

interface ContentTypeSelectorProps {
  selectedType: string;
  onTypeSelect: (type: string) => void;
  isDocked?: boolean; // New prop to control dock mode
}

const ContentTypeSelector: React.FC<ContentTypeSelectorProps> = ({
  selectedType,
  onTypeSelect,
  isDocked = false
}) => {
  const [openCategory, setOpenCategory] = useState<string | null>('ADS & SOCIALS');
  const [isExpanded, setIsExpanded] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  const contentCategories = [
    {
      name: 'ADS & SOCIALS',
      types: [
        { id: 'facebook_ad', label: 'Facebook/IG Ads' },
        { id: 'video_ad_script', label: 'Video Ad Script' },
        { id: 'google_ad', label: 'Google Ads' },
        { id: 'instagram_caption', label: 'Instagram Captions' }
      ]
    },
    {
      name: 'ONLINE STORE',
      types: [
        { id: 'blog_article', label: 'Blog Article' },
        { id: 'product_description', label: 'Product Description' },
        { id: 'upsell_crosssell', label: 'Upsell & Cross-sell' },
        { id: 'faqs', label: 'FAQs' }
      ]
    },
    {
      name: 'EMAIL',
      types: [
        { id: 'abandoned_cart_email', label: 'Abandonment Cart' },
        { id: 'newsletter_email', label: 'Newsletter' },
        { id: 'flash_sales_email', label: 'Flash Sales' },
        { id: 'back_in_stock_email', label: 'Back-in-Stock' }
      ]
    },
    {
      name: 'STRATEGY',
      types: [
        { id: 'customer_avatars', label: 'Avatars' },
        { id: 'pain_benefit_points', label: 'Pain/Benefit point' },
        { id: 'swot_analysis', label: 'SWOT' },
        { id: 'seasonal_strategies', label: 'Seasonal Strategies' }
      ]
    }
  ];

  // Find current selected type info
  const getCurrentTypeInfo = () => {
    for (const category of contentCategories) {
      const type = category.types.find(t => t.id === selectedType);
      if (type) {
        return { category: category.name, type: type.label };
      }
    }
    return { category: 'ADS & SOCIALS', type: 'Facebook/IG Ads' };
  };

  const currentTypeInfo = getCurrentTypeInfo();

  const handleToggleCategory = (categoryName: string) => {
    if (openCategory === categoryName) {
      setOpenCategory(null);
    } else {
      setOpenCategory(categoryName);
    }
  };

  const handleTypeSelect = (typeId: string) => {
    onTypeSelect(typeId);
    if (isDocked) {
      setIsExpanded(false);
    }
  };

  // Auto-expand/collapse on hover for docked mode
  useEffect(() => {
    if (isDocked) {
      const timer = setTimeout(() => {
        setIsExpanded(isHovered);
      }, isHovered ? 200 : 500);
      return () => clearTimeout(timer);
    }
  }, [isHovered, isDocked]);

  if (isDocked) {
    return (
      <>
        <style>{`
          .floating-content-dock {
            position: fixed;
            top: 50%;
            right: 20px;
            transform: translateY(-50%);
            z-index: 1000;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            filter: drop-shadow(0 10px 25px rgba(0, 0, 0, 0.1));
          }

          .dock-collapsed {
            width: 280px;
            height: 60px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 30px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 20px;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border: 2px solid rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(10px);
          }

          .dock-collapsed:hover {
            transform: scale(1.05);
            box-shadow: 0 15px 35px rgba(102, 126, 234, 0.3);
          }

          .dock-collapsed-content {
            display: flex;
            align-items: center;
            gap: 12px;
          }

          .dock-type-indicator {
            width: 10px;
            height: 10px;
            background: #00ff88;
            border-radius: 50%;
            animation: pulse 2s infinite;
          }

          @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
          }

          .dock-current-type {
            color: white;
            font-size: 14px;
            font-weight: 600;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
          }

          .dock-category-label {
            color: rgba(255, 255, 255, 0.8);
            font-size: 11px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
          }

          .dock-expand-icon {
            color: white;
            font-size: 16px;
            transition: transform 0.3s ease;
          }

          .dock-expanded .dock-expand-icon {
            transform: rotate(180deg);
          }

          .dock-expanded {
            width: 400px;
            height: auto;
            max-height: 600px;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15);
            overflow: hidden;
          }

          .dock-expanded-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 16px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            cursor: pointer;
          }

          .dock-expanded-title {
            font-size: 14px;
            font-weight: 600;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
          }

          .dock-expanded-content {
            max-height: 480px;
            overflow-y: auto;
            padding: 20px;
          }

          .dock-content-selector {
            display: flex;
            flex-direction: column;
            gap: 8px;
          }

          .dock-content-category {
            display: flex;
            flex-direction: column;
            border: 1px solid #F3F4F6;
            border-radius: 8px;
            overflow: hidden;
            transition: all 0.2s;
          }

          .dock-content-category.open {
            background-color: white;
            border-color: #E5E7EB;
          }

          .dock-category-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 16px;
            cursor: pointer;
            background: none;
            border: none;
            width: 100%;
            text-align: left;
          }

          .dock-category-title {
            font-size: 11px;
            font-weight: 600;
            color: #6B7280;
            text-transform: uppercase;
            letter-spacing: 0.5px;
          }

          .dock-category-arrow {
            transition: transform 0.3s;
            color: #6B7280;
          }

          .dock-content-category.open .dock-category-arrow {
            transform: rotate(90deg);
          }

          .dock-category-buttons-wrapper {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.4s ease-in-out, padding 0.4s ease-in-out;
          }

          .dock-content-category.open .dock-category-buttons-wrapper {
            max-height: 500px;
            padding: 0 16px 16px 16px;
          }

          .dock-category-buttons {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
          }

          .dock-type-button {
            background-color: #F9FAFB;
            color: #374151;
            border: 1px solid #E5E7EB;
            border-radius: 6px;
            padding: 10px 12px;
            font-family: 'Inter', sans-serif;
            font-size: 14px;
            font-weight: 500;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s ease;
          }

          .dock-type-button:hover {
            background-color: #F3F4F6;
            border-color: #D1D5DB;
          }

          .dock-type-button.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-color: #667eea;
            color: white !important;
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
          }

          .dock-expanded-content::-webkit-scrollbar {
            width: 6px;
          }

          .dock-expanded-content::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 3px;
          }

          .dock-expanded-content::-webkit-scrollbar-thumb {
            background: #c1c1c1;
            border-radius: 3px;
          }

          .dock-expanded-content::-webkit-scrollbar-thumb:hover {
            background: #a8a8a8;
          }
        `}</style>

        <div 
          className={`floating-content-dock ${isExpanded ? 'dock-expanded' : ''}`}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
        >
          {!isExpanded ? (
            <div className="dock-collapsed" onClick={() => setIsExpanded(true)}>
              <div className="dock-collapsed-content">
                <div className="dock-type-indicator"></div>
                <div>
                  <div className="dock-current-type">{currentTypeInfo.type}</div>
                  <div className="dock-category-label">{currentTypeInfo.category}</div>
                </div>
              </div>
              <div className="dock-expand-icon">⌄</div>
            </div>
          ) : (
            <>
              <div className="dock-expanded-header" onClick={() => setIsExpanded(false)}>
                <div className="dock-expanded-title">CHOOSE CONTENT TYPE</div>
                <div className="dock-expand-icon">⌄</div>
              </div>
              <div className="dock-expanded-content">
                <div className="dock-content-selector">
                  {contentCategories.map((category) => {
                    const isOpen = openCategory === category.name;
                    return (
                      <div key={category.name} className={`dock-content-category ${isOpen ? 'open' : ''}`}>
                        <button className="dock-category-header" onClick={() => handleToggleCategory(category.name)}>
                          <span className="dock-category-title">{category.name}</span>
                          <span className="dock-category-arrow">❯</span>
                        </button>
                        <div className="dock-category-buttons-wrapper">
                          <div className="dock-category-buttons">
                            {category.types.map((type, index) => (
                              <button 
                                key={`${category.name}-${type.id}-${index}`}
                                className={`dock-type-button ${selectedType === type.id ? 'active' : ''}`}
                                onClick={() => handleTypeSelect(type.id)}
                              >
                                {type.label}
                              </button>
                            ))}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          )}
        </div>
      </>
    );
  }

  // Original non-docked version
  return (
    <>
      <style>{`
        .content-type-selector {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .content-category {
          display: flex;
          flex-direction: column;
          border: 1px solid #F3F4F6;
          border-radius: 8px;
          overflow: hidden;
          transition: background-color 0.2s;
        }
        .content-category.open {
           background-color: white;
           border-color: #E5E7EB;
        }

        .category-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 16px;
          cursor: pointer;
          background: none;
          border: none;
          width: 100%;
          text-align: left;
        }
        .category-title {
          font-size: 11px;
          font-weight: 600;
          color: #6B7280;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }
        .category-arrow {
          transition: transform 0.3s;
        }
        .content-category.open .category-arrow {
          transform: rotate(90deg);
        }

        .category-buttons-wrapper {
          max-height: 0;
          overflow: hidden;
          transition: max-height 0.4s ease-in-out, padding 0.4s ease-in-out;
        }
        .content-category.open .category-buttons-wrapper {
          max-height: 500px;
          padding: 0 16px 16px 16px;
        }
        .category-buttons {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 8px;
        }
        .type-button {
          background-color: #F9FAFB;
          color: #374151;
          border: 1px solid #E5E7EB;
          border-radius: 6px;
          padding: 10px 12px;
          font-family: 'Inter', sans-serif;
          font-size: 14px;
          font-weight: 500;
          text-align: center;
          cursor: pointer;
          transition: all 0.2s ease;
        }
        .type-button:hover {
          background-color: #F3F4F6;
          border-color: #D1D5DB;
        }
        .type-button.active {
          background-color: var(--primary-color);
          border-color: var(--primary-color);
          color: white !important;
          box-shadow: 0 2px 8px rgba(124, 58, 237, 0.2);
        }
      `}</style>
      <div className="content-type-selector">
        {contentCategories.map((category) => {
          const isOpen = openCategory === category.name;
          return (
            <div key={category.name} className={`content-category ${isOpen ? 'open' : ''}`}>
              <button className="category-header" onClick={() => handleToggleCategory(category.name)}>
                <span className="category-title">{category.name}</span>
                <span className="category-arrow">❯</span>
              </button>
              <div className="category-buttons-wrapper">
                <div className="category-buttons">
                  {category.types.map((type, index) => (
                    <button 
                      key={`${category.name}-${type.id}-${index}`}
                      className={`type-button ${selectedType === type.id ? 'active' : ''}`}
                      onClick={() => onTypeSelect(type.id)}
                    >
                      {type.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </>
  );
};

export default ContentTypeSelector;
