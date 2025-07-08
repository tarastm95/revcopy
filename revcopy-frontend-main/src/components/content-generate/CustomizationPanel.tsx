
import React from 'react';

interface CustomizationState {
  style: string;
  length: string;
  language: string;
  output: string;
}

interface CustomizationPanelProps {
  customization: CustomizationState;
  onCustomizationChange: (field: keyof CustomizationState, value: string) => void;
}

const CustomizationPanel: React.FC<CustomizationPanelProps> = ({
  customization,
  onCustomizationChange
}) => {
  return (
    <div className="customization-grid">
      <div>
        <label htmlFor="style-select">Style</label>
        <select 
          id="style-select" 
          value={customization.style}
          onChange={(e) => onCustomizationChange('style', e.target.value)}
        >
          <option value="" disabled>Choose Style</option>
          <option value="storytelling">Storytelling</option>
          <option value="attention-grabbing">Attention Grabbing</option>
          <option value="feature-focused">Feature Focused</option>
          <option value="friendly">Friendly</option>
          <option value="scarcity">Scarcity</option>
          <option value="special-promotion">Special Promotion</option>
          <option value="funny">Funny</option>
          <option value="controversial">Controversial</option>
          <option value="before-after">Before and After</option>
          <option value="problem-solution">Problem Solution</option>
          <option value="mix-5-styles">Mix of 5 Styles</option>
        </select>
      </div>
      <div>
        <label htmlFor="length-select">Length</label>
        <select 
          id="length-select"
          value={customization.length}
          onChange={(e) => onCustomizationChange('length', e.target.value)}
        >
          <option value="" disabled>Choose Length</option>
          <option value="short">Short</option>
          <option value="medium">Medium</option>
          <option value="long">Long</option>
        </select>
      </div>
      <div>
        <label htmlFor="language-select">Language</label>
        <select 
          id="language-select"
          value={customization.language}
          onChange={(e) => onCustomizationChange('language', e.target.value)}
        >
          <option value="" disabled>Choose Language</option>
          <option value="english">English</option>
          <option value="spanish">Spanish</option>
          <option value="french">French</option>
          <option value="chinese">Chinese</option>
          <option value="hindi">Hindi</option>
          <option value="japanese">Japanese</option>
          <option value="german">German</option>
          <option value="swahili">Swahili</option>
          <option value="pidgin">Pidgin</option>
        </select>
      </div>
      <div>
        <label htmlFor="output-select">Output</label>
        <select 
          id="output-select"
          value={customization.output}
          onChange={(e) => onCustomizationChange('output', e.target.value)}
        >
          <option value="" disabled>Choose Output</option>
          <option value="1">1</option>
          <option value="2">2</option>
          <option value="3">3</option>
        </select>
      </div>
    </div>
  );
};

export default CustomizationPanel;
