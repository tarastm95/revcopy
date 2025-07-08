
import React from 'react';
import { Copy } from 'lucide-react';

interface ContentEditorProps {
  onTextSelection: () => void;
  onCopyContent: (e: React.MouseEvent<HTMLButtonElement>, contentId: string) => void;
}

const ContentEditor: React.FC<ContentEditorProps> = ({
  onTextSelection,
  onCopyContent
}) => {
  return (
    <div className="content-body-wrapper">
      <div className="content-block" onMouseUp={onTextSelection}>
        <div className="content-header">
          <h4>Headline</h4>
          <button 
            className="copy-btn-small" 
            onClick={(e) => onCopyContent(e, 'generated-headline')}
          >
            <Copy size={14} />
          </button>
        </div>
        <input 
          type="text" 
          id="generated-headline" 
          defaultValue="Safer Walks Start Here. Get the Ultimate Control Leash!"
          className="content-input"
        />
        
        <div className="content-header">
          <h4>Body Text</h4>
          <button 
            className="copy-btn-small" 
            onClick={(e) => onCopyContent(e, 'generated-body')}
          >
            <Copy size={14} />
          </button>
        </div>
        <textarea 
          id="generated-body"
          defaultValue="🐾 Tired of sudden pulls? Our premium dual-handle leash combines unmatched durability and comfort, giving you total control. Its short handle is perfect for busy streets, while the long handle offers freedom in the park. Plus, reflective stitching keeps you both safe at night. Upgrade your walks today! 👇"
          className="content-textarea"
        />
      </div>
      
      <div className="content-actions">
        <button className="action-btn primary">Save to Campaign</button>
        <button className="action-btn secondary">Regenerate</button>
      </div>
    </div>
  );
};

export default ContentEditor;
