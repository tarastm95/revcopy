import React from 'react';
import { type ProductAnalysisResponse } from '../../lib/api';

interface AnalysisData {
  benefits?: string[];
  pain_points?: string[];
  key_insights?: string[];
  overall_sentiment?: string;
  total_reviews_processed?: number;
}

interface ProductInsightsProps {
  productData?: ProductAnalysisResponse;
  analysisData?: AnalysisData;
}

const ProductInsights: React.FC<ProductInsightsProps> = ({ productData, analysisData }) => {
  if (!productData) {
    return (
      <div className="product-insights-container">
        {/* Loading state */}
        <div style={{ textAlign: 'center', padding: '40px', color: '#6B7280' }}>
          <p>Loading product insights...</p>
        </div>
      </div>
    );
  }

  // Extract real benefits and pain points from analysis data
  const realBenefits = analysisData?.benefits?.slice(0, 4) || [];
  const realPainPoints = analysisData?.pain_points?.slice(0, 3) || [];

  // Only show insights if we have meaningful data
  const showBenefits = realBenefits.length > 0;
  const showPainPoints = realPainPoints.length >= 2; // Only show if we have substantial negative feedback

  return (
    <>
      <style>{`
        .product-insights-container {
          background-color: white;
          border-radius: 12px;
          border: 1px solid #F3F4F6;
          padding: 24px;
        }
        .product-main-info {
          margin-bottom: 24px;
        }
        .product-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 16px;
          padding-bottom: 16px;
          border-bottom: 1px solid #F3F4F6;
        }
        .product-title-section h3 {
          font-size: 18px;
          font-weight: 600;
          color: #111827;
          margin: 0 0 4px 0;
        }
        .product-title-section p {
          font-size: 14px;
          color: #6B7280;
          margin: 0;
        }
        .product-meta-compact {
          display: flex;
          align-items: center;
          gap: 8px;
          text-align: right;
        }
        .meta-compact {
          font-size: 12px;
          font-weight: 500;
          color: #374151;
          background: #F3F4F6;
          padding: 4px 8px;
          border-radius: 12px;
          white-space: nowrap;
          border: 1px solid #E5E7EB;
        }
        .product-description-summary {
          margin-bottom: 24px;
        }
        .product-description-summary h4 {
          font-size: 14px;
          font-weight: 600;
          color: #111827;
          margin: 0 0 8px 0;
        }
        .product-description-summary p {
          font-size: 14px;
          color: #6B7280;
          line-height: 1.6;
          margin: 0;
        }
        .insights-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 16px;
        }
        .insight-card {
          padding: 16px;
          border-radius: 8px;
        }
        .insight-card h4 {
          font-size: 14px;
          font-weight: 600;
          margin: 0 0 12px 0;
        }
        .insight-card ul {
          margin: 0;
          padding: 0;
          list-style: none;
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .insight-card li {
          font-size: 14px;
          color: #374151;
        }
        .positive {
          background-color: #F0FDF4;
          border: 1px solid #A7F3D0;
        }
        .positive h4 {
          color: #059669;
        }
        .improvement {
          background-color: #FEF2F2;
          border: 1px solid #FECACA;
        }
        .improvement h4 {
          color: #DC2626;
        }
      `}</style>
      <div className="product-insights-container">
        <div className="product-main-info">
          <div className="product-header">
            <div className="product-title-section">
              <h3>{productData.title}</h3>
              <p>by {productData.brand || 'Unknown Brand'}</p>
            </div>
            <div className="product-meta-compact">
              <span className="meta-compact">₪{productData.price}</span>
              <span className="meta-compact">{productData.rating?.toFixed(1) || 'N/A'} ★</span>
              <span className="meta-compact">{productData.platform}</span>
              <span className="meta-compact">{analysisData?.total_reviews_processed || productData.review_count || 0} reviews</span>
            </div>
          </div>
        </div>

        {productData.description && (
          <div className="product-description-summary">
            <h4>Product Description</h4>
            <p>{productData.description.substring(0, 200)}...</p>
          </div>
        )}

        {/* Only show insights if we have real analysis data */}
        {(showBenefits || showPainPoints) && (
          <div className="insights-grid">
            {showBenefits && (
              <div className="insight-card positive">
                <h4>Customer Benefits</h4>
                <ul>
                  {realBenefits.map((benefit, index) => (
                    <li key={index}>{benefit}</li>
                  ))}
                </ul>
              </div>
            )}
            
            {showPainPoints && (
              <div className="insight-card improvement">
                <h4>Areas for Improvement</h4>
                <ul>
                  {realPainPoints.map((painPoint, index) => (
                    <li key={index}>{painPoint}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}


      </div>
    </>
  );
};

export default ProductInsights;
