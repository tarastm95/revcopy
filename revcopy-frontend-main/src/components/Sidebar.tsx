import React, { useState } from 'react';
import { Sparkles, ChevronLeft, FolderOpen, User } from 'lucide-react';

const Sidebar = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed);
  };

  return (
    <aside className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        <div className="logo-icon">
          <Sparkles style={{ color: '#ffffff', fill: '#ffffff' }} className="w-5 h-5" />
        </div>
        <span className="logo-text">RevCopy</span>
      </div>
      
      <nav className="main-nav">
        <div className="nav-section">
          <h3 className="nav-heading">MAIN MENU</h3>
          <ul className="nav-list">
            <li className="nav-item">
              <a href="/content-generate" className="active">
                <Sparkles className="w-5 h-5" />
                <span>Content Generate</span>
              </a>
            </li>
            <li className="nav-item">
              <a href="/campaigns">
                <FolderOpen className="w-5 h-5" />
                <span>Campaigns</span>
              </a>
            </li>
          </ul>
        </div>
      </nav>
      
      <div className="sidebar-footer">
        <div className="user-profile">
          <div className="user-avatar">
            <User className="w-6 h-6" />
          </div>
          <div className="user-info">
            <div className="name">User</div>
            <div className="title">Customer</div>
          </div>
        </div>
        
        <button 
          className="sidebar-toggle" 
          onClick={toggleSidebar}
          title={isCollapsed ? "Expand" : "Collapse"}
        >
          <ChevronLeft className={`icon-collapse w-5 h-5 ${isCollapsed ? 'rotate-180' : ''}`} />
          <span className="collapse-text">Collapse</span>
        </button>
      </div>

      <style>{`
        :root {
          --sidebar-bg: #F9FAFB;
          --sidebar-border-color: #F3F4F6;
          --logo-text-color: #111827;
          --nav-heading-color: #6B7280;
          --nav-link-color: #374151;
          --nav-link-hover-bg: #F3F4F6;
          --nav-link-active-bg: var(--primary-light);
          --nav-link-active-color: var(--primary-color);
          --user-name-color: #374151;
          --user-title-color: #6B7280;
          --collapse-text-color: #6B7280;
        }

        .sidebar {
          position: fixed;
          top: 0;
          left: 0;
          width: 256px;
          height: 100vh;
          background-color: var(--sidebar-bg);
          padding: 24px 16px;
          display: flex;
          flex-direction: column;
          transition: width 0.3s ease;
          border-right: 1px solid var(--sidebar-border-color);
          z-index: 1000;
          overflow-y: auto;
        }
        
        .sidebar.collapsed { 
          width: 80px; 
        }
        
        .sidebar-header { 
          display: flex; 
          align-items: center; 
          gap: 12px; 
          padding: 0 8px; 
          margin-bottom: 32px;
          flex-shrink: 0;
        }
        
        .logo-icon { 
          width: 32px; 
          height: 32px; 
          background-color: var(--primary-color); 
          border-radius: 8px; 
          display: flex; 
          align-items: center; 
          justify-content: center; 
          flex-shrink: 0; 
        }

        .logo-icon svg {
          color: #ffffff !important;
          fill: #ffffff !important;
        }
        
        .logo-text { 
          font-size: 20px; 
          font-weight: 700;
          color: var(--logo-text-color);
          white-space: nowrap;
          opacity: 1;
          transition: opacity 0.2s;
        }
        
        .sidebar.collapsed .logo-text {
          opacity: 0;
          width: 0;
          overflow: hidden;
        }
        
        .main-nav { 
          flex-grow: 1; 
        }
        
        .nav-heading { 
          font-size: 11px; 
          color: var(--nav-heading-color);
          font-weight: 600; 
          padding: 0 12px; 
          margin-bottom: 8px; 
          white-space: nowrap;
          letter-spacing: 0.5px;
          opacity: 1;
          transition: opacity 0.2s;
        }
        
        .sidebar.collapsed .nav-heading {
          opacity: 0;
        }

        .nav-list { 
          list-style: none; 
          padding: 0;
          margin: 0;
        }
        
        .nav-item a { 
          display: flex; 
          align-items: center; 
          gap: 12px; 
          padding: 10px 12px; 
          border-radius: 6px; 
          text-decoration: none; 
          color: var(--nav-link-color); 
          font-weight: 500; 
          font-size: 14px;
          transition: background-color 0.2s, color 0.2s; 
          white-space: nowrap;
          overflow: hidden;
        }
        
        .sidebar.collapsed .nav-item a {
          justify-content: center;
        }

        .nav-item a:hover { 
          background-color: var(--nav-link-hover-bg); 
        }

        .nav-item a.active {
          background-color: var(--nav-link-active-bg);
          color: var(--nav-link-active-color);
        }
        
        .nav-item a span {
          opacity: 1;
          transition: opacity 0.2s;
        }
        
        .sidebar.collapsed .nav-item a span {
          opacity: 0;
          width: 0;
        }

        .sidebar-footer {
          margin-top: auto;
          padding-top: 16px;
        }

        .user-profile { 
          display: flex; 
          align-items: center; 
          gap: 12px; 
          padding: 12px; 
          border-radius: 6px;
          transition: background-color 0.2s;
        }

        .sidebar.collapsed .user-profile {
          justify-content: center;
          padding: 12px 0;
        }

        .user-avatar {
          width: 32px;
          height: 32px;
          background-color: #E5E7EB;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          color: #6B7280;
        }

        .user-info {
          opacity: 1;
          transition: opacity 0.2s;
        }
        
        .sidebar.collapsed .user-info {
          opacity: 0;
          width: 0;
          overflow: hidden;
        }

        .user-info .name { 
          font-weight: 600; 
          font-size: 14px;
          color: var(--user-name-color);
          white-space: nowrap;
        }
        
        .user-info .title { 
          font-size: 12px; 
          color: var(--user-title-color);
          white-space: nowrap;
        }
        
        .sidebar-toggle { 
          display: flex; 
          align-items: center; 
          gap: 12px; 
          width: 100%;
          background: none; 
          border: none; 
          cursor: pointer; 
          padding: 10px 12px; 
          border-radius: 6px; 
          color: var(--collapse-text-color); 
          font-size: 14px;
          font-weight: 500;
        }

        .sidebar.collapsed .sidebar-toggle {
          justify-content: center;
        }

        .collapse-text {
          opacity: 1;
          transition: opacity 0.2s;
        }

        .sidebar.collapsed .collapse-text {
          opacity: 0;
          width: 0;
        }
        
        .icon-collapse { 
          transition: transform 0.3s ease; 
        }

        /* Scrollbar styling for sidebar */
        .sidebar::-webkit-scrollbar {
          width: 6px;
        }

        .sidebar::-webkit-scrollbar-track {
          background: transparent;
        }

        .sidebar::-webkit-scrollbar-thumb {
          background: #D1D5DB;
          border-radius: 3px;
        }

        .sidebar::-webkit-scrollbar-thumb:hover {
          background: #9CA3AF;
        }
      `}</style>
    </aside>
  );
};

export default Sidebar;
