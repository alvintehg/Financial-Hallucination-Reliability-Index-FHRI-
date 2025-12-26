import React from 'react';
import { Home, PieChart, TrendingUp, BarChart3, Target, MessageSquare, Bell, Settings, Edit3 } from 'lucide-react';

export const DashboardSidebar = ({ activeTab, onTabChange }) => {
  const navItems = [
    { id: 'dashboard', icon: Home, label: 'Dashboard' },
    { id: 'portfolio', icon: PieChart, label: 'Portfolio' },
    { id: 'holdings', icon: Edit3, label: 'Manage Holdings' },
    { id: 'investments', icon: TrendingUp, label: 'Investments' },
    { id: 'analytics', icon: BarChart3, label: 'Analytics' },
    { id: 'advisor', icon: MessageSquare, label: 'AI Advisor' },
  ];

  return (
    <div className="hidden lg:block fixed top-0 left-0 w-80 h-screen overflow-y-auto z-10"
      style={{
        background: 'linear-gradient(180deg, #1A1A1A 0%, #0A0A0A 100%)',
        borderRight: '1px solid rgba(64, 180, 229, 0.2)',
      }}
    >
      {/* Logo Header */}
      <div className="p-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-12 h-12 rounded-xl gradient-blue-button flex items-center justify-center">
            <TrendingUp className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-wider">WEALTH.AI</h1>
            <p className="text-xs text-white text-opacity-60">Robo Advisor</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="px-6 py-4">
        <div className="space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 ${
                  isActive
                    ? 'bg-white bg-opacity-10 border border-blue-500 shadow-[0_4px_15px_rgba(64,180,229,0.3)] text-blue-400'
                    : 'text-white text-opacity-70 hover:bg-white hover:bg-opacity-5 hover:text-white'
                }`}
              >
                <Icon className={`w-5 h-5 ${isActive ? 'text-blue-400' : ''}`} />
                <span className="font-semibold text-sm tracking-wide">{item.label}</span>
              </button>
            );
          })}
        </div>
      </nav>

      {/* Footer */}
      <div className="absolute bottom-0 left-0 right-0 p-6 border-t border-white border-opacity-10">
        {/* Action Buttons */}
        <div className="flex gap-2 mb-4">
          <button className="flex-1 p-3 rounded-xl bg-white bg-opacity-5 hover:bg-opacity-10 transition-all duration-300">
            <Bell className="w-5 h-5 text-white text-opacity-70 mx-auto" />
          </button>
          <button className="flex-1 p-3 rounded-xl bg-white bg-opacity-5 hover:bg-opacity-10 transition-all duration-300">
            <Settings className="w-5 h-5 text-white text-opacity-70 mx-auto" />
          </button>
        </div>

        {/* User Profile */}
        <div className="flex items-center gap-3 p-3 rounded-xl bg-white bg-opacity-5">
          <div className="w-10 h-10 rounded-full gradient-blue-button flex items-center justify-center text-white font-bold">
            TYC
          </div>
          <div className="flex-1 min-w-0">
            <div className="font-semibold text-white text-sm">Teh Yi Cheng</div>
            <div className="text-xs text-white text-opacity-60">Premium Account</div>
          </div>
        </div>
      </div>
    </div>
  );
};
