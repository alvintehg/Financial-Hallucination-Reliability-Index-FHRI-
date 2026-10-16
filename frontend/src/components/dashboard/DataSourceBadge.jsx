import React from 'react';
import { Database, Globe, TrendingUp } from 'lucide-react';

/**
 * Data Source Attribution Badge
 * Shows the source of market/financial data (Finnhub, FMP, etc.)
 * Provides transparency and credibility to data displayed
 */
export const DataSourceBadge = ({ source, size = 'sm', className = '' }) => {
  // Source configurations
  const sourceConfig = {
    'Finnhub': {
      icon: TrendingUp,
      color: 'text-blue-400',
      bgColor: 'bg-blue-500',
      borderColor: 'border-blue-500',
      displayName: 'Finnhub'
    },
    'FMP': {
      icon: Database,
      color: 'text-purple-400',
      bgColor: 'bg-purple-500',
      borderColor: 'border-purple-500',
      displayName: 'Financial Modeling Prep'
    },
    'Financial Modeling Prep': {
      icon: Database,
      color: 'text-purple-400',
      bgColor: 'bg-purple-500',
      borderColor: 'border-purple-500',
      displayName: 'FMP'
    },
    'Alpha Vantage': {
      icon: Globe,
      color: 'text-green-400',
      bgColor: 'bg-green-500',
      borderColor: 'border-green-500',
      displayName: 'Alpha Vantage'
    },
    'Yahoo Finance': {
      icon: Globe,
      color: 'text-orange-400',
      bgColor: 'bg-orange-500',
      borderColor: 'border-orange-500',
      displayName: 'Yahoo Finance'
    },
    'CNN Fear & Greed': {
      icon: TrendingUp,
      color: 'text-red-400',
      bgColor: 'bg-red-500',
      borderColor: 'border-red-500',
      displayName: 'CNN F&G'
    },
    'CBOE VIX': {
      icon: TrendingUp,
      color: 'text-yellow-400',
      bgColor: 'bg-yellow-500',
      borderColor: 'border-yellow-500',
      displayName: 'CBOE'
    },
    'Finnhub News': {
      icon: Globe,
      color: 'text-cyan-400',
      bgColor: 'bg-cyan-500',
      borderColor: 'border-cyan-500',
      displayName: 'Finnhub News'
    },
    'Default': {
      icon: Database,
      color: 'text-gray-400',
      bgColor: 'bg-gray-500',
      borderColor: 'border-gray-500',
      displayName: source || 'Unknown'
    }
  };

  const config = sourceConfig[source] || sourceConfig['Default'];
  const Icon = config.icon;

  // Size variants
  const sizeClasses = {
    xs: 'text-[10px] px-1.5 py-0.5 gap-1',
    sm: 'text-xs px-2 py-0.5 gap-1',
    md: 'text-sm px-3 py-1 gap-2',
    lg: 'text-base px-4 py-1.5 gap-2'
  };

  const iconSizes = {
    xs: 'w-2.5 h-2.5',
    sm: 'w-3 h-3',
    md: 'w-4 h-4',
    lg: 'w-5 h-5'
  };

  return (
    <div className={`inline-flex items-center rounded ${sizeClasses[size]} ${config.bgColor} bg-opacity-20 ${config.color} border ${config.borderColor} border-opacity-30 font-semibold ${className}`}>
      <Icon className={iconSizes[size]} />
      <span>{config.displayName}</span>
    </div>
  );
};

/**
 * Multiple Data Sources Badge
 * Shows multiple data sources in a compact layout
 */
export const MultiSourceBadge = ({ sources = [], size = 'sm', className = '' }) => {
  if (!sources || sources.length === 0) return null;

  if (sources.length === 1) {
    return <DataSourceBadge source={sources[0]} size={size} className={className} />;
  }

  return (
    <div className={`inline-flex items-center gap-2 flex-wrap ${className}`}>
      {sources.map((source, idx) => (
        <DataSourceBadge key={idx} source={source} size={size} />
      ))}
    </div>
  );
};

/**
 * Inline text attribution (for footer text)
 */
export const DataSourceText = ({ sources = [], prefix = 'Data provided by', className = '' }) => {
  if (!sources || sources.length === 0) return null;

  const sourcesText = sources.join(', ');

  return (
    <p className={`text-white text-opacity-40 text-xs ${className}`}>
      {prefix} <span className="text-white text-opacity-60 font-semibold">{sourcesText}</span>
    </p>
  );
};

/**
 * Footer attribution component
 * Standardized footer for all widgets
 */
export const DataSourceFooter = ({ sources = [], className = '' }) => {
  if (!sources || sources.length === 0) return null;

  return (
    <div className={`mt-4 pt-4 border-t border-white border-opacity-10 ${className}`}>
      <div className="flex items-center justify-center gap-2 text-xs text-white text-opacity-40 flex-wrap">
        <span>Data sources:</span>
        <MultiSourceBadge sources={sources} size="xs" />
      </div>
    </div>
  );
};

export default DataSourceBadge;
