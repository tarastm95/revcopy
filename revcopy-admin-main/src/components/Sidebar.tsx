/**
 * Sidebar Component for RevCopy Admin Panel
 * 
 * Provides navigation with:
 * - Menu items with active state management
 * - User information display
 * - Secure logout functionality
 * - Responsive design
 */

import React, { useState } from 'react';
import { Users, CreditCard, Edit3, Settings, UserCheck, Bot, Globe, LogOut, User, LayoutDashboard, MessageSquare, ShieldCheck, Activity, Database, TrendingUp, AlertTriangle, Server, BarChart3, Zap, Clock, Eye } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '@/context/AuthContext';
import { NavLink } from 'react-router-dom';

interface SidebarProps {
  activeSection: string;
  onSectionChange: (section: string) => void;
}

/**
 * Main Sidebar Component
 */
const Sidebar: React.FC<SidebarProps> = ({ activeSection, onSectionChange }) => {
  const { user, logout } = useAuth();
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  /**
   * Navigation menu items configuration
   */
  const navItems = [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/users', icon: Users, label: 'Users Management' },
    { to: '/payments', icon: CreditCard, label: 'Payments' },
    { to: '/prompts', icon: MessageSquare, label: 'Prompt Management' },
    { to: '/admins', icon: ShieldCheck, label: 'Administrators' },
    
    // Performance & Monitoring Section
    { 
      label: 'Performance', 
      isSection: true,
      items: [
        { to: '/performance/overview', icon: Activity, label: 'System Overview' },
        { to: '/performance/realtime', icon: TrendingUp, label: 'Real-time Metrics' },
        { to: '/performance/database', icon: Database, label: 'Database Performance' },
        { to: '/performance/cache', icon: Zap, label: 'Cache Analytics' },
        { to: '/performance/tasks', icon: Clock, label: 'Background Tasks' },
      ]
    },
    
    // Monitoring Section  
    {
      label: 'Monitoring',
      isSection: true,
      items: [
        { to: '/monitoring/health', icon: Eye, label: 'Health Checks' },
        { to: '/monitoring/alerts', icon: AlertTriangle, label: 'Alerts & Notifications' },
        { to: '/monitoring/security', icon: ShieldCheck, label: 'Security Monitor' },
        { to: '/monitoring/logs', icon: BarChart3, label: 'System Logs' },
      ]
    },
    
    // System Section
    {
      label: 'System',
      isSection: true,
      items: [
        { to: '/system/maintenance', icon: Server, label: 'Maintenance' },
        { to: '/system/crawler', icon: Settings, label: 'Crawler Settings' },
        { to: '/system/amazon', icon: Settings, label: 'Amazon Settings' },
      ]
    }
  ];

  /**
   * Handle user logout with loading state
   */
  const handleLogout = async (): Promise<void> => {
    try {
      setIsLoggingOut(true);
      await logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setIsLoggingOut(false);
    }
  };

  /**
   * Get user initials for avatar display
   */
  const getUserInitials = (user: any): string => {
    if (!user) return 'A';
    
    if (user.username) {
      return user.username.charAt(0).toUpperCase();
    }
    
    if (user.email) {
      return user.email.charAt(0).toUpperCase();
    }
    
    return 'A';
  };

  /**
   * Get display name for user
   */
  const getDisplayName = (user: any): string => {
    if (!user) return 'Admin User';
    return user.username || user.email || 'Admin User';
  };

  const renderNavItem = (item: any, index: number) => {
    if (item.isSection) {
      return (
        <div key={index} className="mt-6">
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2 px-3">
            {item.label}
          </h3>
          {item.items?.map((subItem: any, subIndex: number) => (
            <NavLink
              key={subIndex}
              to={subItem.to}
              className={({ isActive }) =>
                `flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                  isActive
                    ? 'bg-blue-100 text-blue-700 border-r-2 border-blue-700'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`
              }
            >
              <subItem.icon className="w-5 h-5 mr-3" />
              {subItem.label}
            </NavLink>
          ))}
        </div>
      );
    }

    return (
      <NavLink
        key={index}
        to={item.to}
        className={({ isActive }) =>
          `flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
            isActive
              ? 'bg-blue-100 text-blue-700 border-r-2 border-blue-700'
              : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
          }`
        }
      >
        <item.icon className="w-5 h-5 mr-3" />
        {item.label}
      </NavLink>
    );
  };

  return (
    <div className="flex flex-col w-64 bg-white border-r border-gray-200">
      <div className="flex items-center justify-center h-16 border-b border-gray-200">
        <h1 className="text-xl font-bold text-gray-800">RevCopy Admin</h1>
      </div>
      
      <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
        {navItems.map(renderNavItem)}
      </nav>
      
      <div className="p-4 border-t border-gray-200">
        <div className="text-xs text-gray-500">
          <div className="font-medium">Enterprise Edition</div>
          <div>v2.0.0</div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
