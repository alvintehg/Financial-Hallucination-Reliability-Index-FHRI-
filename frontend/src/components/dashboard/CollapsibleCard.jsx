import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

/**
 * Reusable collapsible card component for dashboard features
 * Maintains the existing design system (glass card styling, colors, spacing)
 */
export const CollapsibleCard = ({
  title,
  icon: Icon,
  children,
  defaultOpen = false,
  badge = null,
  className = ""
}) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className={`rounded-[20px] glass-card-strong overflow-hidden ${className}`}>
      {/* Header - Always Visible */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full p-6 flex items-center justify-between transition-all duration-300 hover:bg-white hover:bg-opacity-5"
      >
        <div className="flex items-center gap-3">
          {Icon && (
            <div className="w-10 h-10 rounded-xl gradient-blue-button flex items-center justify-center">
              <Icon className="w-5 h-5 text-white" />
            </div>
          )}
          <div className="text-left">
            <h3 className="text-lg font-bold text-white tracking-wide uppercase">
              {title}
            </h3>
          </div>
          {badge && (
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-blue-500 bg-opacity-20 text-blue-400 border border-blue-500 border-opacity-30">
              {badge}
            </span>
          )}
        </div>
        <div className="text-white text-opacity-70">
          {isOpen ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
        </div>
      </button>

      {/* Collapsible Content */}
      {isOpen && (
        <div className="px-6 pb-6 border-t border-white border-opacity-10">
          <div className="pt-4">
            {children}
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * Simple card wrapper for non-collapsible content
 * Matches the same design system
 */
export const SimpleCard = ({ title, icon: Icon, children, badge = null, className = "" }) => {
  return (
    <div className={`rounded-[20px] glass-card-strong p-6 ${className}`}>
      <div className="flex items-center gap-3 mb-4">
        {Icon && (
          <div className="w-10 h-10 rounded-xl gradient-blue-button flex items-center justify-center">
            <Icon className="w-5 h-5 text-white" />
          </div>
        )}
        <div>
          <h3 className="text-lg font-bold text-white tracking-wide uppercase">
            {title}
          </h3>
        </div>
        {badge && (
          <span className="px-3 py-1 rounded-full text-xs font-semibold bg-blue-500 bg-opacity-20 text-blue-400 border border-blue-500 border-opacity-30">
            {badge}
          </span>
        )}
      </div>
      <div>{children}</div>
    </div>
  );
};
